# Usage Guide

## The workflow in 3 steps

1. **Load both files** — press *Choose…* for the primary and secondary file.
   After each load the label shows the file name and how many cues were found.
2. **Adjust options** (optional).
3. **Merge & Save…** — review the preview, pick an output path, done.

## Which file is "Primary"?

The **primary** file is the *base track*:

- Merged cues take their **timing** from the primary file.
- The primary language appears **on top** in each cue by default
  (change with *Language order in output*).
- Any primary cue that has no counterpart is still written out, so no
  subtitle line is ever dropped.

Typical setup: Arabic as primary, English as secondary.

## Options

### Language order in output

| Value               | Result in each merged cue |
| ------------------- | ------------------------- |
| `Primary on top`    | Primary text first, then secondary |
| `Secondary on top`  | Secondary text first, then primary |

### Match threshold (%)

Controls how strictly two cues must overlap in time to be considered the
"same" subtitle line. The ratio is

```
overlap ratio = shared time / duration of the shorter cue
```

| Threshold | Behavior |
| --------- | -------- |
| 0 %       | Any touching cue pairs match — most aggressive merging |
| **30 %**  | **Default** — good balance for most releases |
| 70–100 %  | Only nearly identical timings match — for files from the same source |

If two files come from the same translator/site, keep the default. If they
come from different sources with different segmentation, a lower threshold
(10–20 %) often matches better.

## Reading the status line

After a successful merge the status bar shows:

```
Saved 5 cues → /path/merged.srt (matched: 4 | contained: 1 | primary-only: 1 | secondary-only: 0)
```

- **matched** — cue pairs found in both files and combined
- **contained** — extra lines fully inside another cue's time range,
  absorbed into that cue (e.g. one Arabic line over two English lines)
- **primary-only / secondary-only** — lines that had no counterpart and were
  written with their own text only

## Walkthrough with the sample files

Sample bilingual files ship with the project under `tests/data/`
(`sample_ar.srt`, `sample_en.srt`).

1. Run `./run.sh`
2. Primary → `tests/data/sample_ar.srt` (5 cues)
3. Secondary → `tests/data/sample_en.srt` (5 cues)
4. Merge & Save → save as `merged.srt`

Result (5 cues):

```
1
00:00:01,000 --> 00:00:03,500
مرحبًا بكم في الفيديو
Welcome to the video

2
00:00:04,000 --> 00:00:06,000
اليوم سنتعلم شيئًا جديدًا
Today we learn something new

3
00:00:07,000 --> 00:00:10,000
هذا السطر العربي يغطي سطرين إنجليزيين
This English line is short
And this one follows it

4
00:00:15,000 --> 00:00:17,000
سطر عربي وحيد بدون مقابل

5
00:00:20,000 --> 00:00:22,500
شكرًا لمشاهدتكم
Thanks for watching
```

Note cue 3: the Arabic line spans the whole 3 seconds while English split it
into two cues — both English lines are absorbed under one Arabic timing.
Cue 4 has no English counterpart and keeps its own text only.

## Troubleshooting

| Problem | Cause & fix |
| ------- | ----------- |
| "Cannot read file … No valid subtitles found" | The file is not SRT (or corrupt). Check it opens in a text editor. |
| Numbers are missing in output | Cosmetic only — cues are renumbered automatically on save. |
| Languages not aligned well | Lower the match threshold (try 10–20 %) or try swapping primary/secondary. |
| Arabic shows as boxes in the merged file | The *file* is fine (UTF-8); the **player** lacks an Arabic font. Install Noto Arabic fonts for the player. |
| A second language line appears far from its pair | Lower threshold keeps weak pairs apart; raise it to 50 %+ for stricter matching. |
| `tkinter` error at startup | `sudo apt install python3-tk` |
