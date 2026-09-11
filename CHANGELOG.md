# Changelog

## 2.5.0

- Added portable supporting-document attachments for Employment, Education, Training, Certifications, Teaching, Organizations, Skills & Tools, and Achievements.
- Added document selection to Add and Edit record dialogs, including support for multiple documents per record.
- Stored attachments directly inside the SQLite database so normal database backups preserve supporting files.
- Added a Document preview column to supported record tabs.
- Added thumbnail previews for PDF and image attachments and file-type previews for other document formats.
- Added an enlarged document viewer with an option to open the original attachment in its associated application.
- Added automatic attachment cleanup when a linked record or profile is deleted.
- Added **Export Documents ZIP...** to Generate CV for exporting all documents belonging to the active profile.
- Added `manifest.csv` to document ZIP exports with record type, record ID, original filename, file size, and SHA-256 hash.

## 2.4.0

- Added click-to-sort column headers to record tabs.
- Clicking the same heading toggles ascending and descending order.
- Date and year columns sort chronologically.
- Training hours sort numerically and Core Training sorts as Yes/No.
- Text columns use case-insensitive natural ordering.
- Blank values remain at the bottom of sorted results.
- Sorting is a display-only feature and does not change stored data or CV report ordering.

## 2.3.4
- Status bar now updates to reflect the currently selected tab instead of retaining the last refreshed record category.
- Removed the PDF style selector; all native PDF reports now use the Professional style.
- Removed the outdated date-format guidance message from the Generate CV screen.
- Updated built-in help and documentation to match the simplified PDF workflow.

# Version 2.0.0

- Replaced all release seed data with fictitious sample information.
- Added immutable template database copied to a writable database on first launch.
- Added blank-profile creation and sample-data loading.
- Added profile import/export using JSON packages.
- Added dashboard record chart and certification expiration alerts.
- Added Word, PDF, and combined output commands.
- Added optional automatic GitHub release checking.
- Added Inno Setup installer project.
- Added optional Authenticode signing step to the Windows build.
- Retained the stable v1 interface, portable storage, flexible dates, full-text report output, multiple profiles, and chronological sorting.

# Version 2.1.0

- Adopted Semantic Versioning using a single `version.py` source.
- Added application version to the window title and About dialog.
- Added generated Windows executable version metadata.
- Synchronized the Inno Setup installer version from the same source.
- Added a built-in user manual under Help.
- Added a direct Help > How to Add Records command.
- Documented record creation, date entry, editing, deletion, profiles, CV generation, backup, and portability.

# Version 2.2.0

- Added native PDF generation with ReportLab.
- Removed the Microsoft Word and LibreOffice dependency for PDF output.
- Added a shared renderer-neutral CV data model used by Word and PDF generation.
- Added Professional, Court Testimony, Executive, Academic, and Law Enforcement PDF styles.
- Added automatic PDF page numbers and generated-date footers.
- Added clickable email and web links in PDF contact information.
- Added PDF title, author, subject, and keyword metadata.
- Added Professional Achievements to the selectable CV sections.
- Retained independent editable Word output through python-docx.

# Version 2.3.3

- Restored the v2.2.0 application layout, spacing, tabs, profile bar, and standard menu-driven visual scheme.
- Retained persistent Light and Dark appearance modes under Tools > Appearance.
- Retained branded application icon and splash screen with version/loading status.
- Retained the integrated PDF preview with page navigation, zoom, fit-width, and save-after-review.
- Retained professional Inno Setup installer branding, license, and welcome artwork.
- Removed the ttkbootstrap dependency so Light mode uses the original v2.2.0 Windows ttk appearance.
- Preserved all database, profile, portable-storage, Word/PDF rendering, sorting, and update-checking behavior.
