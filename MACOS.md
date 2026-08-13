# macOS Support

This branch adds the first macOS build path for Forensic CV Manager while keeping the SQLite schema and CV-generation code shared with Windows.

## Build

Use a current Python 3 installation on macOS:

```bash
chmod +x build_macos.sh
./build_macos.sh
```

The build script installs the project requirements and PyInstaller, regenerates the sanitized template database, builds `Forensic CV Manager.app`, and creates a portable release folder under `dist/Forensic-CV-Manager-macOS-Portable`.

## Apple Silicon and Intel

PyInstaller builds for the architecture of the Python interpreter used for the build. Build on Apple Silicon with an arm64 Python for an Apple Silicon build. Intel builds should use an x86_64 Python/build environment. A universal build can be added later after both architectures are tested.

## Portable data

Forensic CV Manager continues to use its existing portable SQLite database model. The database format itself is cross-platform and can be used by Windows and macOS builds.

## Signing and notarization

The initial build script does not automatically sign or notarize the application. A publicly distributed macOS build should eventually be signed with an Apple Developer ID Application certificate and submitted for Apple notarization to reduce Gatekeeper warnings.

## Test checklist

- Launch the application and create/select profiles.
- Add, edit, delete, search, and sort records on each applicable tab.
- Switch between Light and Dark appearance.
- Generate a Word CV.
- Preview and save a PDF CV.
- Confirm the template/working SQLite database is writable.
- Confirm Resume and Backups remain portable.
- Confirm generated Word/PDF files open correctly.
- Test on Apple Silicon before release; test Intel separately if Intel support is desired.

## Known first-pass limitation

The Windows 2.4.0 source uses platform-specific folder-opening logic. `platform_utils.py` provides the macOS implementation (`open`), and the application should be migrated to that helper before declaring macOS support production-ready.
