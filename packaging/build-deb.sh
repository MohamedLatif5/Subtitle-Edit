#!/usr/bin/env bash
# Build a .deb package for Subtitle Merger.
# Output: dist/subtitle-merger_<version>_all.deb
set -euo pipefail

cd "$(dirname "$0")/.."

VERSION=$(python3 -c "import sys; sys.path.insert(0, '.'); import subtitle_merger; print(subtitle_merger.__version__)")

STAGE="dist/debroot/subtitle-merger-${VERSION}"
SHARE="$STAGE/usr/local/share/subtitle-merger"

rm -rf dist
mkdir -p "$STAGE/DEBIAN" "$SHARE" "$STAGE/usr/local/bin" "$STAGE/usr/local/share/applications" "$STAGE/usr/local/share/doc/subtitle-merger"

# Application code (no GUI-independent duplication: main.py expects gui/ and
# subtitle_merger/ next to it).
cp -r subtitle_merger gui "$SHARE/"
cp main.py "$SHARE/"
find "$STAGE" -name '__pycache__' -type d -exec rm -rf {} +

# Command-line launcher on PATH.
cat > "$STAGE/usr/local/bin/subtitle-merger" <<'EOF'
#!/usr/bin/env bash
exec python3 /usr/local/share/subtitle-merger/main.py "$@"
EOF
chmod +x "$STAGE/usr/local/bin/subtitle-merger"

# Desktop entry for the application menu.
cp packaging/subtitle-merger.desktop "$STAGE/usr/local/share/applications/"

# Documentation and license.
cp README.md docs/*.md "$STAGE/usr/local/share/doc/subtitle-merger/"
cp LICENSE "$STAGE/usr/local/share/doc/subtitle-merger/"

# Package control file.
cat > "$STAGE/DEBIAN/control" <<EOF
Package: subtitle-merger
Version: ${VERSION}
Architecture: all
Maintainer: Mohamed Eid Latif <MohamedLatif@my.uopeople.edu>
Depends: python3 (>= 3.10), python3-tk
Section: utils
Priority: optional
Description: Merge two SRT subtitles of different languages into one file
 Subtitle Merger combines two SubRip (SRT) subtitle tracks, such as an
 Arabic and an English track, into a single bilingual SRT file with
 time-synchronized cues. Includes a tkinter GUI with live preview,
 configurable language order and match threshold.
EOF

dpkg-deb --build --root-owner-group "$STAGE" "dist/subtitle-merger_${VERSION}_all.deb"
echo "Built dist/subtitle-merger_${VERSION}_all.deb"
