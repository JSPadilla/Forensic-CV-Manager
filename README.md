# Forensic CV Manager 2.4.0

Forensic CV Manager is a portable SQLite-backed desktop application for tracking professional qualifications and generating court-ready curricula vitae.

> **Cross-platform development:** The `feature/macos-support` branch extends the v2.4.0 baseline toward a single portable source package for Windows, macOS, and Linux. The same SQLite database and portable folders can be shared between platform-specific builds.

## Release privacy

The release template contains only fictitious demonstration data for **Alex Morgan** at the fictional **Metro Regional Public Safety Laboratory**. No developer, agency, personal email, phone number, case number, or employment history is included.

On first launch, `data/template.sqlite3` is copied to `data/forensic_cv.sqlite3`. The template remains unchanged and the working database stores all user edits.

## Features

- Cross-platform Python source for Windows, macOS, and Linux
- Shared portable SQLite database across supported operating systems
- Platform-aware file and folder opening (`os.startfile` on Windows, `open` on macOS, and `xdg-open` on Linux)
- Optional `FCV_PORTABLE_ROOT` environment variable for a shared portable application root
- Built-in user manual under Help
- Persistent light and dark appearance modes while retaining the v2.2.0 base layout
- Integrated PDF preview with page navigation, zoom, fit-width, and save-after-review
- Portable SQLite database beside the application root
- Multiple independent examiner profiles
- Create, edit, and delete individual records
- Clear all records for the selected profile
- Fictitious sample database and reusable sample-data command
- Import/export a single profile as `.fcvprofile.json`
- Flexible date entry with chronological report sorting
- Dashboard metrics, record-count chart, and certification expiration alerts
- Word CV generation
- Native PDF generation through ReportLab with no Office dependency
- Consistent Professional-style native PDF output
- PDF page numbers, clickable links, and document metadata
- Portable `Resume`, `data`, and `Backups` folders
- Optional GitHub release update checker
- Platform-specific portable builds from the same source tree
- Optional Windows Inno Setup installer
- Optional Windows Authenticode signing hook

## Cross-platform portable design

Forensic CV Manager uses one application codebase and one SQLite database format. Windows, macOS, and Linux builds can therefore share the same working data when they are configured to use the same portable application root.

A portable package may be arranged like this:

```text
Forensic-CV-Manager-Portable/
├── Windows/
│   └── Forensic CV Manager.exe
├── macOS/
│   └── Forensic CV Manager.app
├── Linux/
│   └── Forensic CV Manager
├── data/
│   ├── template.sqlite3
│   └── forensic_cv.sqlite3
├── Resume/
├── Backups/
├── README.md
└── USER_MANUAL.md
```

The operating-system executables are platform-specific; a Windows `.exe` cannot run natively on macOS or Linux. The application source, database format, profiles, and generated-document folders are shared.

When `FCV_PORTABLE_ROOT` is set, the application uses that location for its writable `data` and `Resume` folders. This is useful when a platform-specific executable lives inside a subfolder of a shared flash-drive package.

## Run from Python

Install the requirements and launch the same source on Windows, macOS, or Linux:

```text
python -m pip install -r requirements.txt
python app.py
```

On systems where Python 3 is invoked as `python3`, use that command instead.

## Build the portable Windows release

```bat
build_windows.bat
```

Copy the entire generated portable folder to the flash drive. Do not copy only the executable.

## Build the portable macOS release

Run from Terminal on a Mac:

```bash
chmod +x build_macos.sh
./build_macos.sh
```

The script creates a macOS `.app` bundle and portable folder. macOS builds must be created on macOS. See `MACOS.md` for additional information about architecture, Gatekeeper, signing, and notarization.

## Build the portable Linux release

Run from a Linux terminal:

```bash
chmod +x build_linux.sh
./build_linux.sh
```

The Linux build is created in `dist/Forensic-CV-Manager-Linux-Portable`. Linux builds should be created on the Linux architecture/distribution family you intend to support and then tested on the target systems.

## Portable launchers

The repository includes launchers for macOS and Linux that set `FCV_PORTABLE_ROOT` to the shared portable folder before starting the platform-specific application:

```text
Run_ForensicCVManager_macOS.command
Run_ForensicCVManager_Linux.sh
```

This allows the platform-specific application to use the same `data`, `Resume`, and `Backups` locations when the complete package is moved between computers or stored on removable media.

## Build a Windows installer

Install Inno Setup 6, run `build_windows.bat`, and then run:

```bat
build_installer.bat
```

The installer is created in the `installer` folder. The portable build remains the preferred option for flash-drive use.

## Code signing

A trusted signing certificate is not included. To sign the Windows build, install the Windows SDK so `signtool.exe` is available and set these environment variables before running `build_windows.bat`:

```bat
set SIGN_PFX=C:\Certificates\YourCodeSigningCertificate.pfx
set SIGN_PASSWORD=your-password
build_windows.bat
```

Without a trusted certificate, Windows may display **Unknown Publisher**.

macOS applications distributed to other users may trigger Gatekeeper warnings unless they are signed with an appropriate Apple Developer certificate and notarized by Apple. Signing and notarization are separate from the PyInstaller build process.

## Update checker

Edit `app_config.py` before publishing:

```python
GITHUB_REPOSITORY = "owner/repository"
```

The checker reads the latest public GitHub release and compares its tag with `APP_VERSION`. It does not download or install updates automatically.

## PDF generation

Use **Preview & Save PDF** on the Generate CV tab to review a temporary native PDF inside the application before saving it. PDF files are generated directly with ReportLab. Microsoft Word and LibreOffice are not required. Word documents are generated independently with python-docx for users who need an editable copy. Both renderers use the same normalized CV data model.

## Profile exchange

Use **File > Export Current Profile** to create a JSON profile package. Use **File > Import Profile** to add it as a separate profile. Imports never overwrite an existing profile.

Because the profile package and SQLite data are platform-independent, profiles can also be transferred between Windows, macOS, and Linux installations.

## Backups

The working database is:

```text
data/forensic_cv.sqlite3
```

Back up that file regularly to a location separate from the flash drive. If using a shared portable package, all supported platform builds can access this same database.

## Version management

The release version is defined once in `version.py` using Semantic Versioning (`MAJOR.MINOR.PATCH`). The current `main` baseline remains v2.4.0 while cross-platform support is developed and tested on `feature/macos-support`.

## User manual

Open **Help > User Manual** for instructions covering profiles, adding records, flexible dates, editing, deletion, CV generation, backups, and portable use. **Help > How to Add Records** opens directly to the record-entry instructions.

## Sorting Records

Record lists can be sorted by clicking a column heading. Click once for ascending order and click the same heading again for descending order. The active heading displays an arrow showing the current direction. Dates are sorted chronologically, hours numerically, and text alphabetically using natural ordering. Sorting changes only the on-screen list; it does not alter the database or the chronological ordering used by generated CV reports.
