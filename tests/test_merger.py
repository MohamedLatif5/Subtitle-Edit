import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from subtitle_merger.merger import merge_cues
from subtitle_merger.models import Cue
from subtitle_merger.srt_parser import parse_srt_file
from subtitle_merger.srt_writer import format_srt

DATA = Path(__file__).resolve().parent / "data"


def cue(start: int, end: int, *lines: str) -> Cue:
    return Cue(start_ms=start, end_ms=end, lines=list(lines))


class TestMergeRealFiles(unittest.TestCase):
    def setUp(self):
        self.ar = parse_srt_file(DATA / "sample_ar.srt")
        self.en = parse_srt_file(DATA / "sample_en.srt")

    def test_merge_basic_pairs(self):
        result = merge_cues(self.ar, self.en)
        # 4 matched pairs (1,2,3+contained,5) + 1 primary-only (cue 4)
        self.assertEqual(result.matched, 4)
        self.assertEqual(result.contained, 1)
        self.assertEqual(result.primary_only, 1)
        self.assertEqual(len(result.cues), 5)

    def test_first_cue_is_bilingual(self):
        result = merge_cues(self.ar, self.en)
        first = sorted(result.cues, key=lambda c: c.start_ms)[0]
        self.assertEqual(first.lines, ["مرحبًا بكم في الفيديو", "Welcome to the video"])

    def test_containment_absorbs_two_english_lines(self):
        result = merge_cues(self.ar, self.en)
        merged = [c for c in result.cues if c.start_ms == 7000]
        self.assertEqual(len(merged), 1)
        self.assertEqual(
            merged[0].lines,
            [
                "هذا السطر العربي يغطي سطرين إنجليزيين",
                "This English line is short",
                "And this one follows it",
            ],
        )

    def test_unmatched_primary_keeps_own_text(self):
        result = merge_cues(self.ar, self.en)
        orphan = [c for c in result.cues if c.start_ms == 15_000]
        self.assertEqual(len(orphan), 1)
        self.assertEqual(orphan[0].lines, ["سطر عربي وحيد بدون مقابل"])

    def test_output_is_sorted_and_valid_srt(self):
        result = merge_cues(self.ar, self.en)
        text = format_srt(result.cues)
        starts = [c.start_ms for c in result.cues]
        self.assertEqual(starts, sorted(starts))
        self.assertIn("1\n00:00:01,000", text)
        self.assertIn("مرحبًا", text)
        self.assertIn("Welcome", text)


class TestMergeSynthetic(unittest.TestCase):
    def test_empty_input(self):
        self.assertEqual(merge_cues([], []).cues, [])

    def test_empty_secondary(self):
        result = merge_cues([cue(0, 1000, "hi")], [])
        self.assertEqual(len(result.cues), 1)
        self.assertEqual(result.cues[0].lines, ["hi"])

    def test_identical_tracks(self):
        a = [cue(0, 1000, "one"), cue(2000, 3000, "two")]
        result = merge_cues(a, [cue(0, 1000, "uno"), cue(2000, 3000, "dos")])
        self.assertEqual(result.matched, 2)
        self.assertEqual(result.cues[0].lines, ["one", "uno"])

    def test_no_overlap_means_pass_through(self):
        a = [cue(0, 1000, "a1")]
        b = [cue(5000, 6000, "b1")]
        result = merge_cues(a, b)
        self.assertEqual(result.matched, 0)
        self.assertEqual(len(result.cues), 2)

    def test_threshold_prevents_weak_match(self):
        a = [cue(0, 1000, "a1")]       # overlaps b1 by 100ms of 1000ms => 0.1
        b = [cue(900, 2000, "b1")]
        result = merge_cues(a, b, threshold=0.5)
        self.assertEqual(result.matched, 0)
        result2 = merge_cues(a, b, threshold=0.05)
        self.assertEqual(result2.matched, 1)

    def test_invalid_threshold(self):
        with self.assertRaises(ValueError):
            merge_cues([], [], threshold=1.5)

    def test_one_to_many_not_allowed(self):
        # a1 overlaps both b1 and b2; greedy 1:1 picks only the best pair.
        a = [cue(0, 3000, "a1")]
        b = [cue(0, 1500, "b1"), cue(1600, 3000, "b2")]
        result = merge_cues(a, b)
        self.assertEqual(result.matched, 1)
        # b2 is fully contained in a1's range -> absorbed by containment
        self.assertEqual(result.contained, 1)
        self.assertEqual(result.cues[0].lines, ["a1", "b1", "b2"])


if __name__ == "__main__":
    unittest.main()
