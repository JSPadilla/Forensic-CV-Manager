# Forensic CV Manager 2.5.2

Forensic CV Manager is a portable SQLite-backed desktop application for tracking professional qualifications and generating court-ready curricula vitae.

## What's new in 2.5.2

- Consistent Dark Mode for Add/Edit dialogs, notes, attachment lists, and dropdowns, including dialogs opened after changing appearance.
- Readable dark hover and pressed colors for table headings and other interactive controls.
- Light Mode restores its original theme colors when switching back. Compact thumbnails, sorting, and separator autosizing remain available.

## Performance improvements introduced in 2.5.1

- Faster record refreshes and column sorting through reuse of existing rows and cached document thumbnails.
- Automatic dashboard updates after adding, editing, or deleting records, with refreshed totals when changing profiles.
- Column widths remain stable during sorting and unchanged refreshes. Added or edited values can widen a column; double-click a separator to fit the column to the displayed content.
- Updated PDF preview imports to remove the legacy PyMuPDF `fitz` deprecation warning.

Existing databases and stored attachments remain compatible; no manual data conversion is needed. List thumbnails remain 27×27 pixels, and the enlarged document viewer is unchanged. The first load of a profile still renders its document thumbnails; later refreshes reuse them while their content is unchanged.

## Release privacy

The release template contains only fictitious demonstration data for **Alex Morgan** at the fictional **Metro Regional Public Safety Laboratory**. No developer, agency, personal email, phone number, case number, or employment history is included.

On first launch, `data/template.sqlite3` is copied to `data/forensic_cv.sqlite3`. The template remains unchanged and the working database stores all user edits.

## Features

- Built-in user manual under Help
- Persistent light and dark appearance modes while retaining the v2.2.0 base layout
- Integrated PDF preview with page navigation, zoom, fit-width, and save-after-review
- Portable SQLite database beside the executable
- Multiple independent examiner profiles
- Create, edit, and delete individual records
- Attach supporting documents to professional records
- Document thumbnails/previews on supported record tabs
- Integrated enlarged document viewer for PDF and image attachments
- Open attached Office and other document types in their default application
- Export all documents for the active profile to a ZIP archive with a SHA-256 manifest
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
- Portable ZIP build and optional Inno Setup installer
- Optional Authenticode signing hook

## Record attachments

Version 2.5.0 adds supporting-document storage to the following record categories:

- Employment
- Education
- Training
- Certifications
- Teaching
- Organizations
- Skills & Tools
- Achievements

Use **Add Document...** in the Add or Edit dialog for a supported record. Multiple documents may be attached to the same record.

Attachments are stored as BLOB data inside the portable SQLite database rather than as loose files. This keeps the supporting documents with the database during normal backup and portable use.

Supported image and PDF attachments display a thumbnail in the **Document** column. Select the thumbnail to open the integrated enlarged viewer. Other document types display a file-type preview and can be opened with the operating system's associated application.

On the **Generate CV** tab, select **Export Documents ZIP...** to export every supporting document for the active profile. The ZIP contains the documents organized by record type and a `manifest.csv` containing record information, file size, and SHA-256 hash values.

## Run from Python

```bat
python -m pip install -r requirements.txt
python app.py
```

## Build the portable Windows release

```bat
build_windows.bat
```

Copy the entire `dist` folder to the flash drive. Do not copy only the executable.

## Build an installer

Install Inno Setup 6, run `build_windows.bat`, and then run:

```bat
build_installer.bat
```

The installer is created in the `installer` folder. The portable build remains the preferred option for flash-drive use.

## Code signing

A trusted signing certificate is not included. To sign during the build, install the Windows SDK so `signtool.exe` is available and set these environment variables before running `build_windows.bat`:

```bat
set SIGN_PFX=C:\Certificates\YourCodeSigningCertificate.pfx
set SIGN_PASSWORD=your-password
build_windows.bat
```

Without a trusted certificate, Windows may display **Unknown Publisher**. The build cannot legitimately remove that warning by itself.

## Update checker

The update checker is configured in `app_config.py` for this repository:

```python
GITHUB_REPOSITORY = "JSPadilla/Forensic-CV-Manager"
```

The checker reads the latest public GitHub release and compares its tag with `APP_VERSION`. It does not download or install updates automatically.

## PDF generation

Use **Preview & Save PDF** on the Generate CV tab to review a temporary native PDF inside the application before saving it. PDF files are generated directly with ReportLab. Microsoft Word and LibreOffice are not required. Word documents are generated independently with python-docx for users who need an editable copy. Both renderers use the same normalized CV data model.

## Profile exchange

Use **File > Export Current Profile** to create a JSON profile package. Use **File > Import Profile** to add it as a separate profile. Imports never overwrite an existing profile.

## Backups

The working database is:

```text
data\forensic_cv.sqlite3
```

Because v2.5.0 stores attachments inside SQLite, normal database backups also preserve the attached documents. Back up the database regularly to a location separate from the flash drive.

## Version management

The release version is defined once in `version.py` using Semantic Versioning (`MAJOR.MINOR.PATCH`). The build scripts generate Windows executable metadata and Inno Setup version information from that value.

## User manual

Open **Help > User Manual** for instructions covering profiles, adding records, flexible dates, editing, deletion, CV generation, backups, and portable use. **Help > How to Add Records** opens directly to the record-entry instructions.

## Sorting Records

Record lists can be sorted by clicking a column heading. Click once for ascending order and click the same heading again for descending order. The active heading displays an arrow showing the current direction. Dates are sorted chronologically, hours numerically, and text alphabetically using natural ordering. Sorting changes only the on-screen list; it does not alter the database or the chronological ordering used by generated CV reports.

Sorting preserves the selected record and column widths. Columns fit their headings and data when a profile is loaded, then grow only as needed for added or edited values. To refit a column, double-click the separator at the right edge of its heading. This also works for the Document column.

## Dashboard refresh

Training hours, record counts, and certification alerts refresh automatically after record changes. Switching profiles, importing a profile, or clearing the active profile's records also refreshes the dashboard. **Refresh Dashboard** remains available for a manual refresh. Returning to the Dashboard tab also checks for profile and date changes so expiration alerts stay current.

## Testing and profiling

Run the test suite from the repository folder:

```text
python -m unittest discover -s tests -v
```

The GUI regression tests require Tk and a display. On Linux without a desktop, use `xvfb-run -a python -m unittest discover -s tests -v` with Xvfb installed. GitHub Actions runs these checks for main, feature branches, and pull requests to main.

To measure refreshes and sorting with synthetic records and documents:

```text
python tools/benchmark_refresh.py --records 1000 --samples 5
```

The optional `--database PATH` argument profiles a disposable copy of an existing SQLite database. The source database is opened read-only, and output contains aggregate timings and call counts. Timings include profiling overhead; repeated refresh and sorting measurements use the thumbnail cache after initial loading. Keep personal databases, documents, and test archives outside the repository.
