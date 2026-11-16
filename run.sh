#!/usr/bin/env bash
# Launch the Subtitle Merger GUI.
set -euo pipefail
cd "$(dirname "$0")"
exec python3 main.py "$@"
