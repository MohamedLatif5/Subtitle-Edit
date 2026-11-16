import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from subtitle_merger.models import Cue, ms_to_srt_time, srt_time_to_ms
from subtitle_merger.srt_parser import parse_srt_file, parse_srt_text

DATA = Path(__file__).resolve().parent / "data"


class TestTimeHelpers(unittest.TestCase):
    def test_roundtrip(self):
        for ms in (0, 1, 65_500, 3_661_234):
            self.assertEqual(srt_time_to_ms(ms_to_srt_time(ms)), ms)

    def test_format(self):
        self.assertEqual(ms_to_srt_time(3_661_234), "01:01:01,234")

    def test_invalid(self):
        self.assertIsNone(srt_time_to_ms("not a time"))
        self.assertIsNone(srt_time_to_ms("00:99:00,000"))
        self.assertIsNone(srt_time_to_ms("00:00:01"))


class TestParser(unittest.TestCase):
    def test_parse_arabic_sample(self):
        cues = parse_srt_file(DATA / "sample_ar.srt")
        self.assertEqual(len(cues), 5)
        self.assertEqual(cues[0].start_ms, 1000)
        self.assertEqual(cues[0].end_ms, 3500)
        self.assertEqual(cues[0].lines, ["مرحبًا بكم في الفيديو"])

    def test_parse_english_sample(self):
        cues = parse_srt_file(DATA / "sample_en.srt")
        self.assertEqual(len(cues), 5)

    def test_multiline_cue(self):
        text = "1\n00:00:01,000 --> 00:00:02,000\nline one\nline two\n"
        cues = parse_srt_text(text)
        self.assertEqual(len(cues), 1)
        self.assertEqual(cues[0].lines, ["line one", "line two"])

    def test_broken_numbers_still_parse(self):
        cues = parse_srt_file(DATA / "broken_numbers.srt")
        self.assertEqual(len(cues), 2)

    def test_bom_file(self):
        cues = parse_srt_file(DATA / "bom_file.srt")
        self.assertEqual(cues[0].lines[0], "Hello with BOM")

    def test_crlf(self):
        text = "1\r\n00:00:01,000 --> 00:00:02,000\r\nhi\r\n\r\n2\r\n00:00:03,000 --> 00:00:04,000\r\nbye\r\n"
        cues = parse_srt_text(text)
        self.assertEqual(len(cues), 2)

    def test_garbage_raises(self):
        with self.assertRaises(ValueError):
            parse_srt_text("this is not a subtitle file at all")

    def test_missing_file(self):
        with self.assertRaises(FileNotFoundError):
            parse_srt_file(DATA / "does_not_exist.srt")


class TestCueHelpers(unittest.TestCase):
    def test_overlap(self):
        a = Cue(start_ms=0, end_ms=100, lines=[])
        b = Cue(start_ms=50, end_ms=150, lines=[])
        c = Cue(start_ms=200, end_ms=300, lines=[])
        self.assertTrue(a.overlaps(b))
        self.assertEqual(a.overlap_ms(b), 50)
        self.assertFalse(a.overlaps(c))

    def test_contains(self):
        outer = Cue(start_ms=0, end_ms=100, lines=[])
        inner = Cue(start_ms=10, end_ms=50, lines=[])
        self.assertTrue(outer.contains(inner))
        self.assertFalse(inner.contains(outer))


if __name__ == "__main__":
    unittest.main()
