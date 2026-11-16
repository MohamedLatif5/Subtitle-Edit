# Subtitle Merger

A desktop tool for **Ubuntu Linux** that merges two SRT subtitle files of
different languages (e.g. Arabic + English) into a **single bilingual SRT
file** — every cue shows both languages together, time-synchronized.

Built with **Python 3 + tkinter** and **zero external dependencies**.

## Features

- Merge any two SRT files into one bilingual file
- Time-based matching with a tunable overlap threshold
- Containment handling: one line covering two lines in the other language is
  absorbed into a single merged cue
- Unmatched cues pass through with their own text — nothing is lost
- Live preview of the first 10 merged cues before saving
- Choice of language order in the output (primary on top or bottom)
- Tolerant parser: UTF-8 / UTF-8-BOM, legacy Arabic encodings (cp1256),
  CRLF line endings, missing sequence numbers
- Output written as UTF-8 (with BOM) for maximum player compatibility

## Install

**Option A — Debian package (recommended):**

```bash
packaging/build-deb.sh
sudo dpkg -i dist/subtitle-merger_*.deb
```

Then launch "Subtitle Merger" from the application menu, or run
`subtitle-merger` from a terminal.

**Option B — run from source:**

```bash
sudo apt install python3-tk
./run.sh        # or: python3 main.py
```

See [docs/INSTALL.md](docs/INSTALL.md) for details.

## Example

Input — `ar.srt` and `en.srt`:

```
1                                    1
00:00:01,000 --> 00:00:03,500        00:00:01,000 --> 00:00:03,400
مرحبًا بكم في الفيديو                Welcome to the video
```

Output — `merged.srt`:

```
1
00:00:01,000 --> 00:00:03,500
مرحبًا بكم في الفيديو
Welcome to the video
```

## Project layout

| Path                    | Purpose                                  |
| ----------------------- | ---------------------------------------- |
| `subtitle_merger/`      | Core library (no GUI code)               |
| `gui/app.py`            | Tkinter GUI                              |
| `main.py` / `run.sh`    | Entry points                             |
| `tests/`                | Unit tests + sample SRT files            |
| `docs/`                 | Installation, usage, architecture, AGENTS |
| `packaging/`            | .deb build script + desktop entry        |

## Documentation

- [docs/INSTALL.md](docs/INSTALL.md) — installation on Ubuntu
- [docs/USAGE.md](docs/USAGE.md) — step-by-step usage guide + troubleshooting
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — how the code and merge algorithm work
- [docs/AGENTS.md](docs/AGENTS.md) — guide for AI coding agents working on this repo

## Tests

```bash
python3 -m unittest discover -s tests -v
```

## License

MIT
