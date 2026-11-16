# Installation (Ubuntu Linux)

## Requirements

| Requirement | Version | Notes |
| ----------- | ------- | ----- |
| Python 3    | 3.10+   | Preinstalled on modern Ubuntu |
| tkinter     | any     | Provided by the `python3-tk` package |

The app has **no external Python packages** — everything is stdlib.

## Step 1 — Install tkinter

```bash
sudo apt update
sudo apt install python3-tk
```

Verify:

```bash
python3 -c "import tkinter; print('OK', tkinter.TkVersion)"
# → OK 8.6
```

## Option A — Install the .deb package (recommended)

Build and install:

```bash
packaging/build-deb.sh
sudo dpkg -i dist/subtitle-merger_*.deb
```

The package installs:

- `/usr/local/bin/subtitle-merger` — terminal launcher
- `/usr/local/share/subtitle-merger/` — application code
- `/usr/local/share/applications/subtitle-merger.desktop` — application-menu entry

"Subtitle Merger" then appears in the GNOME Activities search / app grid.
To remove: `sudo dpkg -r subtitle-merger`.

## Option B — Run from source

From the project folder:

```bash
./run.sh
```

or equivalently:

```bash
python3 main.py
```

## Optional — Run tests

```bash
python3 -m unittest discover -s tests -v
```

## Troubleshooting installation

**`ModuleNotFoundError: No module named 'tkinter'`**
→ `sudo apt install python3-tk`

**`cannot open display`**
→ The app is a GUI program; run it from a desktop session, not over SSH
   (unless you use X forwarding: `ssh -X`).

**Fonts / Arabic text looks disconnected**
→ Install an Arabic-capable font:
   `sudo apt install fonts-noto-core fonts-noto-arabic` (or `fonts-kacst`),
   then restart the app.
