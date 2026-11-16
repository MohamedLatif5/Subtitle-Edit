#!/usr/bin/env python3
"""Entry point for the Subtitle Merger GUI."""

import sys
from pathlib import Path

# Ensure the project root is importable when launched from anywhere.
sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    import tkinter  # noqa: F401
except ImportError:
    sys.stderr.write(
        "tkinter is not installed.\n"
        "Install it with:  sudo apt install python3-tk\n"
    )
    sys.exit(1)

from gui.app import main

if __name__ == "__main__":
    main()
