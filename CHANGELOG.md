# Changelog

All notable changes to **Forensic CV Manager** are documented in this file.

The project uses Semantic Versioning (`MAJOR.MINOR.PATCH`) beginning with the 2.x release line. Earlier version history is retained below for reference.

---

## 2.5.0 — Unreleased

### Document attachments

- Added supporting-document attachments to the following record categories:
  - Employment
  - Education
  - Training
  - Certifications
  - Teaching
  - Organizations
  - Skills & Tools
  - Achievements
- Added document selection directly to Add and Edit record dialogs.
- Added support for attaching multiple documents to a single record.
- Stored attachments inside the SQLite database so documents remain portable with the application's data and are preserved by normal database backups.
- Added attachment metadata including original filename, MIME/file information, size, and SHA-256 hash.
- Added automatic cleanup of attachments when their associated record or profile is deleted.
- Added attachment-focused unit tests covering storage, retrieval, hashing, profile isolation, deletion cleanup, and ZIP export.

### Document previews and viewing

- Added a **Document** column to supported record tabs.
- Added thumbnail previews for PDF and image attachments.
- Added generic file-type previews for other supported document formats.
- Added an enlarged attachment viewer for reviewing documents from the record list.
- Added the ability to open the original attachment in the operating system's associated application.
- Reduced list-view document thumbnails from 54×54 pixels to 27×27 pixels for a cleaner, less distracting record display.
- Reduced attachment-enabled row height and narrowed the Document column to match the smaller preview size.
- Kept the enlarged document viewer unchanged when the list thumbnail size was reduced.

### Document export

- Added **Export Documents ZIP...** to the Generate CV tab.
- Added profile-wide export of all attached supporting documents to a ZIP archive.
- Added `manifest.csv` to exported document archives.
- The document manifest records:
  - record type
  - record ID
  - original filename
  - file size
  - SHA-256 hash
- Added duplicate-safe ZIP naming so documents with the same filename can be exported without overwriting one another.

### Record-list display improvements

- Added automatic sizing of visible record-list columns based on both heading text and displayed data.
- Added double-click autosizing of an individual column by double-clicking its separator line.
- Added bold Treeview column headings in both Light and Dark modes.
- Applied bold heading styling to the Document heading as well as normal data columns.
- Preserved click-to-sort behavior while adding autosizing support.
- Preserved document-thumbnail click behavior while adding separator double-click handling.

### Update checking

- Fixed **Tools > Check for Updates** by replacing the placeholder GitHub repository setting with `JSPadilla/Forensic-CV-Manager`.
- Retained GitHub Release-based version checking.
- Added regression tests for update-version comparison and repository configuration.
- Improved update-check error handling for unavailable repositories, repositories without published Releases, network failures, and GitHub anonymous API rate limiting.

### Stability, testing, and repository maintenance

- Fixed the attachment Add/Edit dialog lifecycle so attachment changes are committed after the dialog closes without attempting to access destroyed Tk widgets.
- Added a permanent GitHub Actions test workflow for v2.5.0 development.
- Added automated Python syntax validation and unit-test execution on branch pushes.
- Removed accidentally committed Python `__pycache__` files.
- Added `.gitignore` rules for Python cache and generated build artifacts.
- Removed temporary one-use patch workflows after their changes were applied.

---

## 2.4.0 — Sortable Record Columns

- Added click-to-sort column headings to record tabs.
- Clicking the same heading toggles ascending and descending order.
- Added chronological sorting for date and year columns.
- Added numeric sorting for Training Hours.
- Added Yes/No-aware sorting for Core Training.
- Added case-insensitive natural ordering for text columns.
- Kept blank values at the bottom of sorted results.
- Kept sorting as a display-only function so it does not alter database records or generated-CV ordering.

---

## 2.3.4 — Interface and PDF Workflow Cleanup

- Updated the status bar so it reflects the currently selected tab instead of retaining the last refreshed record category.
- Removed the PDF style selector from the Generate CV screen.
- Standardized native PDF output on the **Professional** style.
- Removed outdated date-format guidance from the Generate CV screen.
- Updated built-in help and documentation to match the simplified PDF workflow.

---

## 2.3.3 — v2.2 Layout Restoration and Theme Stabilization

- Restored the v2.2.0 application layout, spacing, tabs, profile bar, and traditional menu-driven visual scheme.
- Retained persistent Light and Dark appearance modes under **Tools > Appearance**.
- Retained the branded application icon and splash screen with version/loading status.
- Retained integrated PDF preview with page navigation, zoom, fit-width, and save-after-review.
- Retained professional Inno Setup installer branding, license presentation, and welcome artwork.
- Removed the `ttkbootstrap` dependency so Light mode uses the original Windows ttk appearance.
- Preserved database, profile, portable-storage, Word/PDF rendering, sorting, and update-checking behavior.

---

## 2.3.1 — Startup Style Collision Fix

- Corrected a startup styling conflict introduced during the 2.3 branding/theme work.
- Stabilized application startup while preserving the new visual features introduced in 2.3.0.

---

## 2.3.0 — Branding, Themes, Splash Screen, and PDF Preview

- Added application branding improvements.
- Added persistent Light and Dark appearance modes.
- Added a branded startup splash screen with version and loading-status feedback.
- Added an integrated PDF preview window.
- Added PDF preview page navigation.
- Added PDF preview zoom controls.
- Added fit-width support in PDF preview.
- Added save-after-review workflow for native PDF generation.
- Improved installer presentation and branding.

---

## 2.2.0 — Native PDF Generation

- Added native PDF generation using ReportLab.
- Removed the requirement for Microsoft Word or LibreOffice when creating PDFs.
- Added a shared renderer-neutral CV data model used by both Word and PDF generation.
- Added Professional, Court Testimony, Executive, Academic, and Law Enforcement PDF styles.
- Added automatic PDF page numbers.
- Added generated-date footers.
- Added clickable email and web links in PDF contact information.
- Added PDF document metadata including title, author, subject, and keywords.
- Added Professional Achievements as a selectable CV section.
- Retained independent editable Word generation through `python-docx`.

---

## 2.1.0 — Semantic Versioning and User Manual

- Adopted Semantic Versioning using a single `version.py` source.
- Added the application version to the window title.
- Added the application version to the About dialog.
- Added generated Windows executable version metadata.
- Synchronized the Inno Setup installer version with the central version source.
- Added a built-in user manual under **Help**.
- Added **Help > How to Add Records** for direct access to record-entry instructions.
- Documented:
  - record creation
  - flexible date entry
  - editing and deletion
  - profile management
  - CV generation
  - database backup
  - portable operation

---

## 2.0.1 — Profile and Update-Checker Fixes

- Corrected profile-related issues identified after the 2.0.0 architecture release.
- Corrected update-checker behavior.
- Improved reliability of the release-ready 2.x architecture without changing the overall workflow introduced in 2.0.0.

---

## 2.0.0 — Release-Ready Architecture

- Replaced release seed data with fictitious demonstration information.
- Added an immutable template database that is copied to a writable working database on first launch.
- Added blank-profile creation.
- Added fictitious sample-data loading.
- Added profile import/export using JSON profile packages.
- Added dashboard record-count visualization.
- Added certification expiration alerts.
- Added Word output generation.
- Added PDF output generation workflow.
- Added combined Word + PDF generation.
- Added optional automatic GitHub Release update checking.
- Added an Inno Setup installer project.
- Added an optional Authenticode signing step to the Windows build process.
- Retained the stable v1 user interface and existing professional-record workflow.
- Retained portable storage.
- Retained flexible date handling.
- Retained full-text report output.
- Retained multiple profiles.
- Retained chronological report sorting.

---

## 1.2.2 — Flexible Dates and Portable Resume Output

- Added flexible date-entry support.
- Improved normalization and chronological handling of dates used in records and generated documents.
- Added portable Resume output so generated CV files are stored with the portable application workspace.
- Continued the portable-data design introduced in earlier 1.x releases.

---

## 1.2.1 — Report Output Fixes

- Corrected report-generation/output issues found after multi-profile support was introduced.
- Improved generated CV consistency while retaining the existing data-entry workflow.

---

## 1.2.0 — Multi-Profile Support

- Added support for multiple examiner/professional profiles in a single application database.
- Added the ability to switch the active profile.
- Scoped professional records and generated CV content to the selected profile.
- Established the profile-management foundation used throughout later releases.

---

## 1.1.0 — Portable Database

- Moved the working SQLite database into the portable application structure.
- Enabled professional records to travel with the application when run from removable media or another portable folder.
- Reduced dependence on machine-specific application-data locations.

---

## 1.0.1 — Windows Build Fix

- Corrected issues in the initial Windows packaged build.
- Improved reliability of the portable Windows executable following the initial stable release.

---

## 1.0.0 — Initial Stable Release

- Initial stable release of Forensic CV Manager.
- Added SQLite-backed professional-record storage.
- Added desktop record management for core CV information.
- Added CV-generation capability.
- Established the original Windows/Tkinter application interface that later releases continued to evolve.

---

## Repository Maintenance

The following repository-level changes are not tied to a specific application feature release but are part of the project history:

- Added GNU General Public License v3 project licensing.
- Added GitHub Sponsors/Funding configuration for Buy Me a Coffee support.
- Updated Buy Me a Coffee funding information after initial configuration.
- Maintained the v2.4.0 `main` branch as the stable baseline while v2.5.0 document-attachment work is developed and tested separately.

---

## Version History Summary

| Version | Primary focus |
| --- | --- |
| 2.5.0 | Supporting-document attachments, previews, ZIP export, list autosizing, update-checker repair |
| 2.4.0 | Sortable record columns |
| 2.3.4 | Status-bar and PDF workflow cleanup |
| 2.3.3 | v2.2 layout restoration and theme stabilization |
| 2.3.1 | Startup style collision fix |
| 2.3.0 | Branding, themes, splash screen, PDF preview |
| 2.2.0 | Native PDF generation |
| 2.1.0 | Semantic Versioning and built-in user manual |
| 2.0.1 | Profile and update-checker fixes |
| 2.0.0 | Release-ready architecture |
| 1.2.2 | Flexible dates and portable Resume output |
| 1.2.1 | Report output fixes |
| 1.2.0 | Multi-profile support |
| 1.1.0 | Portable database |
| 1.0.1 | Windows build fix |
| 1.0.0 | Initial stable application |
