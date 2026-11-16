"""Merge two subtitle tracks (e.g. Arabic + English) into bilingual cues.

Algorithm overview:
1. For every cue pair (primary, secondary) compute the overlap ratio:
       overlap = shared duration / duration of the shorter cue
   A pair is a *candidate* if overlap >= threshold.
2. Greedy 1:1 matching: accept candidate pairs from best overlap first;
   each cue can be matched at most once, so no cue is duplicated.
3. Containment pass: an unmatched secondary cue that lies fully inside the
   time range of a *matched* pair is appended to that pair's merged cue
   (handles e.g. one Arabic line spanning two English lines).
4. Unmatched cues pass through with their own text only.
5. Output is sorted by start time and renumbered by the writer.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from .models import Cue

DEFAULT_THRESHOLD = 0.3


@dataclass
class MergeResult:
    cues: list[Cue]
    matched: int          # pairs matched directly
    contained: int        # secondary cues absorbed via containment
    primary_only: int     # primary cues with no secondary text
    secondary_only: int   # secondary cues with no primary text


def merge_cues(
    primary: list[Cue],
    secondary: list[Cue],
    threshold: float = DEFAULT_THRESHOLD,
) -> MergeResult:
    """Merge two cue lists into bilingual cues.

    Timing of a merged cue comes from the primary cue (base track).
    """
    if not 0.0 <= threshold <= 1.0:
        raise ValueError("threshold must be between 0.0 and 1.0")

    used_primary: set[int] = set()
    used_secondary: set[int] = set()

    # -- 1. Build candidate pairs sorted by overlap ratio (descending) -------
    candidates: list[tuple[float, int, int]] = []
    for i, p in enumerate(primary):
        for j, s in enumerate(secondary):
            if not p.overlaps(s):
                continue
            shorter = min(p.duration_ms, s.duration_ms)
            if shorter <= 0:
                shorter = 1
            ratio = p.overlap_ms(s) / shorter
            if ratio >= threshold:
                candidates.append((ratio, i, j))
    candidates.sort(key=lambda t: (-t[0], t[1], t[2]))

    # -- 2. Greedy 1:1 matching ---------------------------------------------
    pairs: list[tuple[int, int]] = []
    for _, i, j in candidates:
        if i in used_primary or j in used_secondary:
            continue
        used_primary.add(i)
        used_secondary.add(j)
        pairs.append((i, j))

    # -- 3. Containment pass -------------------------------------------------
    matched_pairs_with_contained: list[tuple[int, int, list[int]]] = []
    contained_count = 0
    for i, j in pairs:
        contained: list[int] = []
        p = primary[i]
        for k, s in enumerate(secondary):
            if k in used_secondary:
                continue
            if p.contains(s):
                contained.append(k)
                used_secondary.add(k)
                contained_count += 1
        matched_pairs_with_contained.append((i, j, contained))

    # -- 4. Build output cues -------------------------------------------------
    out: list[Cue] = []

    # Matched pairs: primary timing + primary lines + secondary lines.
    for i, j, contained in matched_pairs_with_contained:
        p, s = primary[i], secondary[j]
        lines = list(p.lines)
        lines.extend(s.lines)
        for k in contained:
            lines.extend(secondary[k].lines)
        out.append(Cue(start_ms=p.start_ms, end_ms=p.end_ms, lines=lines))

    # Primary cues with no match pass through unchanged.
    for i, p in enumerate(primary):
        if i not in used_primary:
            out.append(replace(p))

    # Secondary cues with no match pass through unchanged.
    for j, s in enumerate(secondary):
        if j not in used_secondary:
            out.append(replace(s))

    out.sort(key=lambda c: (c.start_ms, c.end_ms))

    return MergeResult(
        cues=out,
        matched=len(pairs),
        contained=contained_count,
        primary_only=len(primary) - len(pairs),
        secondary_only=len(secondary) - len(pairs) - contained_count,
    )
