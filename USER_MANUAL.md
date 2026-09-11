# Forensic CV Manager User Manual

## Adding records

1. Select the intended examiner from **Active Profile**.
2. Open the appropriate record tab, such as Training, Certifications, Employment, or Courtroom Testimony.
3. Select **Add** in the upper-right corner.
4. Complete the available fields.
5. For supported record types, use **Add Document...** in the Documents section to select one or more supporting files.
6. Select **Save**. The record and its attachments are immediately available in the application.

Document attachments are available for Employment, Education, Training, Certifications, Teaching, Organizations, Skills & Tools, and Achievements.

Common date formats are accepted, including `3/5/2026`, `03-05-2026`, `2026-03-05`, `March 5, 2026`, `March 2026`, `03/2026`, and `2026`. Employment end dates may use `Present`, `Current`, `Ongoing`, or `Now`.

Description and Notes fields support multiline text and are printed in full. Enter only documented numeric course hours in the Hours field. Select **Include in Core Training** when a training record should appear in the concise Core Training section.

## Supporting documents

Supporting files are stored directly inside the SQLite database so they remain with the portable database and are included in normal database backups.

A record may contain multiple attachments. Use the Documents section in the Add or Edit dialog to add, remove, or open attachments before saving the record.

On supported record tabs, the first attachment is represented in the **Document** column. PDF and image files display a thumbnail. Select the preview to open the enlarged document viewer. If more than one document is attached, the preview also indicates the attachment count.

The enlarged viewer renders PDF first pages and image files directly. Office documents and other formats can be opened using **Open Original**, which launches the file in the operating system's associated application.

## Editing and deleting

Select a record and choose **Edit** to revise it. Existing attachments are listed in the Documents section and may be added, opened, or removed before saving.

Select **Delete** to permanently remove a record. Attached documents associated with that record are also removed from the database. Back up the database before bulk deletion.

## Profiles

Use **Active Profile** to switch examiners. Select **Manage Profiles** to add, rename, switch, or delete profiles. Profile import and export are available from the File menu.

## Generating a CV

Open **Generate CV**, select the desired sections, then choose Word, PDF, or both. PDF reports use the consistent Professional style. Generated files default to the portable `Resume` folder. Date-based sections are sorted newest to oldest.

### Exporting supporting documents

On **Generate CV**, select **Export Documents ZIP...** to export all supporting documents associated with the active profile.

The ZIP file is organized by record type and includes `Documents/manifest.csv`. The manifest records the source record type, record ID, original filename, file size, and SHA-256 value for each exported document.

## Backup and portability

Keep the executable and its `data`, `Resume`, and `Backups` folders together. Use **File > Backup Database** regularly and store a separate copy in an approved secure location.

Because document attachments are stored inside `data/forensic_cv.sqlite3`, backing up the SQLite database also backs up the supporting documents.

## Appearance

Use **Tools > Appearance > Light Mode** or **Dark Mode**. The choice is stored in the portable `data` folder and restored on the next launch. Light mode intentionally retains the v2.2.0 Windows-style interface.

## PDF Preview

On **Generate CV**, select **Preview & Save PDF**. A temporary native PDF opens in the integrated viewer. Use Previous/Next, Zoom, or Fit Width to review it. Select **Save PDF** to write the approved copy to the portable `Resume` folder or another chosen location. Closing the preview without saving does not create a resume file.

## Sorting Records

Record lists can be sorted by clicking a column heading. Click once for ascending order and click the same heading again for descending order. The active heading displays an arrow showing the current direction. Dates are sorted chronologically, hours numerically, and text alphabetically using natural ordering. Sorting changes only the on-screen list; it does not alter the database or the chronological ordering used by generated CV reports.
