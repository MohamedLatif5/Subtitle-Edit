"""SRT writer: serialize a list of Cue objects back to SRT text/file."""

from __future__ import annotations

from pathlib import Path

from .models import Cue, ms_to_srt_time


def format_srt(cues: list[Cue]) -> str:
    """Format cues as SRT text (with renumbered indices), sorted by start time."""
    ordered = sorted(cues, key=lambda c: (c.start_ms, c.end_ms))
    blocks: list[str] = []
    for i, cue in enumerate(ordered, start=1):
        lines = [str(i), f"{ms_to_srt_time(cue.start_ms)} --> {ms_to_srt_time(cue.end_ms)}"]
        lines.extend(cue.lines)
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks) + "\n"


def write_srt_file(cues: list[Cue], path: str | Path, bom: bool = True) -> None:
    """Write cues to an SRT file as UTF-8. BOM on by default for player compatibility."""
    path = Path(path)
    text = format_srt(cues)
    encoding = "utf-8-sig" if bom else "utf-8"
    path.write_text(text, encoding=encoding)
