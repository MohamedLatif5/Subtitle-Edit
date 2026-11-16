# AGENTS.md — Guide for AI Coding Agents

Instructions for AI assistants and coding agents (Claude, ZCode, Copilot,
etc.) working on this repository.

## Project summary

Subtitle Merger merges two SRT subtitle files in different languages
(e.g. Arabic + English) into one bilingual SRT file. Target platform:
**Ubuntu Linux**. Stack: **Python 3 (3.10+) stdlib only** — tkinter for the
GUI, unittest for tests. **Do not add third-party dependencies** unless the
user explicitly asks.

## Layout map

```
subtitle_merger/        Core library — NO GUI code here
  models.py             Cue dataclass + ms<->SRT time helpers
  srt_parser.py         SRT file/text -> list[Cue]  (tolerant decoder)
  srt_writer.py         list[Cue] -> SRT file (UTF-8 + BOM)
  merger.py             Time-based merge algorithm
gui/app.py              Tkinter UI (thin layer over the core)
main.py / run.sh        Entry points
tests/                  unittest tests + sample SRT files (tests/data/)
docs/                   INSTALL.md, USAGE.md, ARCHITECTURE.md, AGENTS.md
packaging/              build-deb.sh (builds dist/*.deb) + desktop entry
```

## Conventions

- Times are **integer milliseconds** everywhere; convert to
  `HH:MM:SS,mmm` strings only via `models.ms_to_srt_time` /
  `models.srt_time_to_ms`. Never parse/format timestamps elsewhere.
- Keep the core package import-clean: nothing in `subtitle_merger/` may
  import tkinter or read GUI state.
- The GUI calls UI-thread-unsafe work from a background thread and hops
  back with `self.after(0, …)`. Any new long-running work in the GUI must
  follow the same pattern.
- User-facing strings in the GUI are in English (UI), and docs are written
  in English; keep that consistent.
- Match existing style: stdlib-only, dataclasses, type hints, module
  docstrings explaining *why*.

## Commands

```bash
# Run the app
./run.sh                       # or: python3 main.py

# Run all tests (must pass before any commit)
python3 -m unittest discover -s tests -v

# Quick end-to-end core check without the GUI
python3 - <<'EOF'
import sys; sys.path.insert(0, '.')
from subtitle_merger.srt_parser import parse_srt_file
from subtitle_merger.merger import merge_cues
from subtitle_merger.srt_writer import write_srt_file
ar = parse_srt_file('tests/data/sample_ar.srt')
en = parse_srt_file('tests/data/sample_en.srt')
r = merge_cues(ar, en)
write_srt_file(r.cues, '/tmp/merged.srt')
print(r)
EOF
```

## When changing code

- **Parser changes** → add/adjust tests in `tests/test_parser.py`. The
  parser must stay tolerant: BOM, CRLF, missing indices, legacy encodings
  (cp1256 for Arabic) must keep working.
- **Merger changes** → add/adjust tests in `tests/test_merger.py`. Key
  invariants that must never break:
  1. Greedy matching is strictly **1:1** — a cue never appears in two
     merged cues.
  2. No text is ever dropped: unmatched cues pass through.
  3. Merged cues use the **primary** cue's timing.
  4. Output is sorted by start time and renumbered by the writer.
- **GUI changes** → verify with a smoke test (instantiate `MergeApp`,
  `update()`, `destroy()`) since there is no UI test harness.
- Add sample data to `tests/data/` when fixing a real-world parsing bug.

## Known sharp edges

- `merger.py` containment pass only absorbs *secondary* cues inside
  *matched primary* cues; a primary cue contained inside a matched
  secondary cue is passed through unmatched. Don't "fix" this without a
  test showing the desired behavior.
- `srt_parser._decode()` fallback order matters for Arabic
  (cp1256 before cp1252); reordering it will corrupt Arabic text silently.
- `packaging/build-deb.sh` installs to `/usr/local/` (not `/usr/`) so it
  never collides with apt-managed files; keep it that way.
- The deb version string is read from `subtitle_merger/__init__.py` — bump
  it there when releasing, nowhere else.

## Definition of done

1. `python3 -m unittest discover -s tests -v` — all green.
2. GUI smoke test passes.
3. Docs (`README.md`, `docs/`) updated if behavior, options, or layout
   changed.
