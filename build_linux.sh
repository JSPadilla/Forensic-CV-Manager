#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

echo "============================================="
echo " Forensic CV Manager - Linux Portable Builder"
echo "============================================="

python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt pyinstaller
python3 create_release_template.py

rm -rf build dist
python3 -m PyInstaller \
  --noconfirm \
  --clean \
  --onefile \
  --windowed \
  --name "ForensicCVManager" \
  --add-data "assets:assets" \
  app.py

mkdir -p dist/data dist/Resume dist/Backups
cp data/template.sqlite3 dist/data/template.sqlite3
cp README.md dist/README.md
cp USER_MANUAL.md dist/USER_MANUAL.md
if [ -f LICENSE ]; then cp LICENSE dist/LICENSE; fi
if [ -f LICENSE.txt ]; then cp LICENSE.txt dist/LICENSE.txt; fi

echo
echo "Linux portable build complete: $(pwd)/dist"
