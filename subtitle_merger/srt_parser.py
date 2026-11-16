"""SRT parser: read an SRT file into a list of Cue objects.

Tolerant of real-world files:
- UTF-8 with or without BOM (BOM is stripped)
- CRLF or LF line endings
- Missing/damaged sequence numbers
- Blank lines between blocks (or missing ones)
- Timestamps separated by " --> " (also tolerates extra spaces)
"""

from __future__ import annotations

import codecs
from pathlib import Path

from .models import Cue, srt_time_to_ms

_ARROW = "-->"


def _decode(raw: bytes) -> str:
    """Decode bytes to text, handling BOM and common encodings."""
    # UTF-8 BOM
    if raw.startswith(codecs.BOM_UTF8):
        return raw.decode("utf-8-sig")
    # Try UTF-8 strictly first
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        pass
    # Fallback chain for legacy encodings (cp1256 covers Arabic)
    for enc in ("cp1256", "cp1252", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    # latin-1 never fails
    return raw.decode("latin-1")


def parse_srt_text(text: str) -> list[Cue]:
    """Parse SRT content into cues. Raises ValueError on a badly broken file."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    blocks = [b for b in text.split("\n\n") if b.strip()]
    cues: list[Cue] = []
    errors: list[str] = []

    for block_num, block in enumerate(blocks, start=1):
        lines = block.strip("\n").split("\n")
        if not lines:
            continue

        # Skip a leading sequence number line if present.
        idx = 0
        if lines[0].strip().isdigit():
            idx = 1

        if idx >= len(lines) or _ARROW not in lines[idx]:
            # No timing line found in this block
            errors.append(f"block {block_num}: missing timing line")
            continue

        timing = _parse_timing_line(lines[idx])
        if timing is None:
            errors.append(f"block {block_num}: bad timestamp '{lines[idx]}'")
            continue

        start_ms, end_ms = timing
        text_lines = [ln for ln in lines[idx + 1:]]

        if start_ms > end_ms:
            errors.append(f"block {block_num}: start after end")
            continue

        cues.append(Cue(start_ms=start_ms, end_ms=end_ms, lines=text_lines))

    # A file that has some content but produced no cues at all is invalid.
    if not cues and errors:
        raise ValueError(
            "No valid subtitles found in file. "
            "Is this really an SRT file? Details: " + "; ".join(errors[:3])
        )
    return cues


def _parse_timing_line(line: str) -> tuple[int, int] | None:
    """Parse '00:00:01,000 --> 00:00:03,500' returning (start_ms, end_ms)."""
    parts = line.split(_ARROW)
    if len(parts) != 2:
        return None
    start = srt_time_to_ms(parts[0])
    end = srt_time_to_ms(parts[1])
    if start is None or end is None:
        return None
    return start, end


def parse_srt_file(path: str | Path) -> list[Cue]:
    """Read and parse an SRT file from disk."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    if not path.is_file():
        raise ValueError(f"Not a file: {path}")
    raw = path.read_bytes()
    if not raw.strip():
        raise ValueError(f"File is empty: {path}")
    return parse_srt_text(_decode(raw))
