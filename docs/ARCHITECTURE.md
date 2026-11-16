# Architecture

## Overview

```
┌──────────────┐     ┌──────────────────────────────────────────────┐
│  gui/app.py  │ --> │            subtitle_merger/ (core)           │
│  (tkinter)   │     │                                              │
└──────────────┘     │  srt_parser.py ──> models.py (Cue)           │
                     │        │                  ▲                  │
                     │        v                  │                  │
                     │  merger.py ───────────────┘                  │
                     │        │                                     │
                     │        v                                     │
                     │  srt_writer.py                               │
                     └──────────────────────────────────────────────┘
```

The core package (`subtitle_merger/`) contains **no GUI code** — it can be
used from a script, test, or another UI. The GUI is a thin layer over it.

## Modules

### `models.py`

- `Cue` dataclass: `start_ms`, `end_ms`, `lines[]`, `index` — times are kept
  in **milliseconds** (integers) throughout; formatting happens only at the
  edges.
- Time helpers: `srt_time_to_ms()`, `ms_to_srt_time()` (accepts `,` or `.`
  as the millisecond separator).

### `srt_parser.py`

`parse_srt_file(path) -> list[Cue]`

- `_decode()` — strips UTF-8 BOM, tries strict UTF-8, then falls back to
  cp1256 (Arabic), cp1252, latin-1.
- Splits on blank lines into blocks, skips sequence-number lines (they may
  be missing or wrong), requires only a `-->` timing line.
- Normalizes CRLF → LF.
- Raises `ValueError` with details if a non-empty file yields zero cues.

### `merger.py`

`merge_cues(primary, secondary, threshold=0.3) -> MergeResult`

Four passes (see the algorithm comment in the file for full detail):

1. **Candidate scoring** — every overlapping pair gets
   `overlap / min(durations)`; below-threshold pairs are dropped.
2. **Greedy 1:1 matching** — best-scoring pairs are accepted first; each cue
   is used at most once, so a cue can never be duplicated across many pairs.
3. **Containment** — an unmatched secondary cue fully inside a matched
   primary cue's range is appended to that pair.
4. **Pass-through** — unmatched cues keep their own text only.

Merged cues take the **primary cue's timing**. Output is sorted by start
time; the writer renumbers cues, so input numbering is irrelevant.

`MergeResult` reports counters (`matched`, `contained`, `primary_only`,
`secondary_only`) used by the GUI status line.

### `srt_writer.py`

`write_srt_file(cues, path, bom=True)` — sorts, renumbers, writes UTF-8
(BOM on by default: some Windows players and TVs need it to auto-detect
UTF-8; it does not hurt Linux players).

### `gui/app.py`

- `MergeApp(tk.Tk)` — three labeled sections mirroring the workflow:
  file pickers, options, preview `Text` widget, status bar.
- Merge runs in a **background thread**; results hop back to the UI thread
  via `self.after(0, …)` (tkinter is not thread-safe).
- File dialogs filter `*.srt`; every parse error is surfaced with
  `messagebox.showerror`.

## Time representation

Everything internal is integer milliseconds. Conversions to/from the
`HH:MM:SS,mmm` string format happen only in `models.py` and are round-trip
tested (`test_roundtrip`).

## Extending the tool

**Add another format (e.g. WebVTT):**
1. Add `vtt_parser.py` / `vtt_writer.py` producing/consuming `list[Cue]` —
   VTT timestamps differ only in the separator (`.` vs `,`) and the
   `WEBVTT` header.
2. Add a format dropdown in `gui/app.py` and dispatch in the pick/save
   handlers. `merger.py` needs no changes — it only knows `Cue`.

**Add support for style tags / ASS:** the `Cue.lines` structure would need
to grow (per-line styling); the merge algorithm itself stays the same
because it operates purely on time ranges.

## Testing strategy

- `tests/test_parser.py` — timestamp helpers, real sample files (Arabic
  text included), BOM, CRLF, broken numbering, garbage rejection.
- `tests/test_merger.py` — the shipped samples end-to-end, plus synthetic
  edge cases: empty inputs, identical tracks, no overlap, threshold
  boundaries, and one-to-many protection.

Run: `python3 -m unittest discover -s tests -v`
