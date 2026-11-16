"""Core data structures for subtitle cues and time helpers."""

from __future__ import annotations

from dataclasses import dataclass, field


def ms_to_srt_time(ms: int) -> str:
    """Convert milliseconds to SRT timestamp: HH:MM:SS,mmm."""
    if ms < 0:
        ms = 0
    hours, rem = divmod(ms, 3_600_000)
    minutes, rem = divmod(rem, 60_000)
    seconds, millis = divmod(rem, 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"


def srt_time_to_ms(timestamp: str) -> int | None:
    """Parse an SRT timestamp (HH:MM:SS,mmm) to milliseconds. None if invalid."""
    timestamp = timestamp.strip()
    # Accept both "00:01:02,500" and "00:01:02.500"
    normalized = timestamp.replace(".", ",")
    parts = normalized.split(":")
    if len(parts) != 3:
        return None
    hours, minutes, seconds = parts
    if not (hours.isdigit() and minutes.isdigit()):
        return None
    sec_parts = seconds.split(",")
    if len(sec_parts) != 2 or not (sec_parts[0].isdigit() and sec_parts[1].isdigit()):
        return None
    if len(sec_parts[1]) != 3:
        return None
    h, m, s, ms = int(hours), int(minutes), int(sec_parts[0]), int(sec_parts[1])
    if m > 59 or s > 59:
        return None
    return ((h * 60 + m) * 60 + s) * 1000 + ms


@dataclass
class Cue:
    """A single subtitle cue: a time range plus one or more text lines."""

    start_ms: int
    end_ms: int
    lines: list[str] = field(default_factory=list)
    index: int = 0  # sequential number, recomputed on write

    @property
    def duration_ms(self) -> int:
        return max(0, self.end_ms - self.start_ms)

    def text(self) -> str:
        return "\n".join(self.lines)

    def add_line(self, line: str) -> None:
        self.lines.append(line)

    def overlaps(self, other: "Cue") -> bool:
        return self.start_ms < other.end_ms and other.start_ms < self.end_ms

    def overlap_ms(self, other: "Cue") -> int:
        return max(0, min(self.end_ms, other.end_ms) - max(self.start_ms, other.start_ms))

    def contains(self, other: "Cue") -> bool:
        """True if `other` lies fully inside this cue's time range."""
        return self.start_ms <= other.start_ms and other.end_ms <= self.end_ms
