#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"

PYTHON_BIN="${PYTHON_BIN:-python3}"
command -v "$PYTHON_BIN" >/dev/null 2>&1 || { echo "Python 3 was not found."; exit 1; }

"$PYTHON_BIN" -m pip install -r requirements.txt pyinstaller
"$PYTHON_BIN" create_release_template.py

rm -rf build dist
ICON_ARG=()
if [ -f "assets/app.icns" ]; then
  ICON_ARG=(--icon "assets/app.icns")
fi

"$PYTHON_BIN" -m PyInstaller --noconfirm --clean --windowed --name "Forensic CV Manager" "${ICON_ARG[@]}" --add-data "assets:assets" app.py

PORTABLE="dist/Forensic-CV-Manager-macOS-Portable"
mkdir -p "$PORTABLE/data" "$PORTABLE/Resume" "$PORTABLE/Backups"
cp -R "dist/Forensic CV Manager.app" "$PORTABLE/"
cp "data/template.sqlite3" "$PORTABLE/data/template.sqlite3"
cp README.md "$PORTABLE/README.md"
cp USER_MANUAL.md "$PORTABLE/USER_MANUAL.md"
cp LICENSE.txt "$PORTABLE/LICENSE.txt"
cp Sample_Generated_CV.docx "$PORTABLE/Sample_Generated_CV.docx"
cp Sample_Generated_CV.pdf "$PORTABLE/Sample_Generated_CV.pdf"

echo "Build complete: $PORTABLE"
echo "This build is unsigned unless you sign/notarize it separately with Apple developer tools."
