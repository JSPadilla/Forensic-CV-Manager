from __future__ import annotations

import hashlib
import tempfile
import unittest
import zipfile
from pathlib import Path

from attachments import (
    add_files,
    all_profile_attachments,
    ensure_attachment_schema,
    export_profile_documents,
    get_attachment,
    list_attachments,
)
from database import Database


class AttachmentStorageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.db = Database(self.root / "test.sqlite3")
        ensure_attachment_schema(self.db)
        self.record_id = self.db.insert_row(
            "training",
            {
                "attended_date": "2026-09-11",
                "course_name": "Attachment Test Course",
                "provider": "Test Provider",
                "hours": 8.0,
            },
        )

    def tearDown(self):
        self.db.close()
        self.temp.cleanup()

    def _make_document(self, name: str = "certificate.txt", content: bytes = b"certificate data") -> Path:
        path = self.root / name
        path.write_bytes(content)
        return path

    def test_add_list_and_read_attachment(self):
        source = self._make_document()
        ids = add_files(self.db, "training", self.record_id, [source])

        self.assertEqual(len(ids), 1)
        listed = list_attachments(self.db, "training", self.record_id)
        self.assertEqual(len(listed), 1)
        self.assertEqual(listed[0]["original_name"], "certificate.txt")
        self.assertEqual(listed[0]["sha256"], hashlib.sha256(b"certificate data").hexdigest())

        full = get_attachment(self.db, ids[0])
        self.assertIsNotNone(full)
        self.assertEqual(bytes(full["content"]), b"certificate data")

    def test_record_delete_cascades_to_attachments(self):
        source = self._make_document()
        add_files(self.db, "training", self.record_id, [source])
        self.assertEqual(len(list_attachments(self.db, "training", self.record_id)), 1)

        self.db.delete_row("training", self.record_id)
        remaining = self.db.conn.execute(
            "SELECT COUNT(*) FROM attachments WHERE record_table='training' AND record_id=?",
            (self.record_id,),
        ).fetchone()[0]
        self.assertEqual(remaining, 0)

    def test_export_zip_contains_document_and_manifest(self):
        source = self._make_document("Digital Forensics Certificate.txt", b"verified training")
        add_files(self.db, "training", self.record_id, [source])
        destination = self.root / "documents.zip"

        count = export_profile_documents(self.db, destination)
        self.assertEqual(count, 1)
        self.assertTrue(destination.exists())

        with zipfile.ZipFile(destination, "r") as archive:
            names = archive.namelist()
            self.assertIn("Documents/manifest.csv", names)
            document_names = [name for name in names if name.endswith("Digital Forensics Certificate.txt")]
            self.assertEqual(len(document_names), 1)
            self.assertEqual(archive.read(document_names[0]), b"verified training")
            manifest = archive.read("Documents/manifest.csv").decode("utf-8")
            self.assertIn("training", manifest)
            self.assertIn("Digital Forensics Certificate.txt", manifest)

    def test_attachments_are_scoped_to_active_profile(self):
        source = self._make_document()
        add_files(self.db, "training", self.record_id, [source])
        first_profile_id = self.db.current_profile_id

        second_profile_id = self.db.create_profile("Second Examiner")
        self.db.set_current_profile(second_profile_id)
        self.assertEqual(all_profile_attachments(self.db), [])

        self.db.set_current_profile(first_profile_id)
        self.assertEqual(len(all_profile_attachments(self.db)), 1)


if __name__ == "__main__":
    unittest.main()
