from __future__ import annotations

import csv
import hashlib
import io
import mimetypes
import os
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
import tkinter as tk
from typing import Any, Iterable

from PIL import Image, ImageDraw, ImageFont, ImageTk

try:
    import pymupdf
except ImportError:  # PyMuPDF also exposes the legacy fitz module in older installs.
    import fitz as pymupdf

ATTACHMENT_TABLES = {
    "employment",
    "education",
    "training",
    "certifications",
    "teaching",
    "organizations",
    "skills",
    "achievements",
}

FILE_TYPES = [
    ("Documents and Images", "*.pdf *.doc *.docx *.xls *.xlsx *.ppt *.pptx *.txt *.rtf *.jpg *.jpeg *.png *.tif *.tiff *.bmp"),
    ("PDF", "*.pdf"),
    ("Word Documents", "*.doc *.docx"),
    ("Images", "*.jpg *.jpeg *.png *.tif *.tiff *.bmp"),
    ("All Files", "*.*"),
]


def ensure_attachment_schema(db) -> None:
    """Create attachment storage and delete triggers without altering record tables."""
    db.conn.execute(
        """CREATE TABLE IF NOT EXISTS attachments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_id INTEGER NOT NULL,
            record_table TEXT NOT NULL,
            record_id INTEGER NOT NULL,
            original_name TEXT NOT NULL,
            mime_type TEXT,
            size_bytes INTEGER NOT NULL DEFAULT 0,
            sha256 TEXT NOT NULL,
            content BLOB NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(profile_id) REFERENCES profiles(id) ON DELETE CASCADE
        )"""
    )
    db.conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_attachments_record ON attachments(profile_id, record_table, record_id)"
    )
    for table in sorted(ATTACHMENT_TABLES):
        db.conn.execute(
            f"""CREATE TRIGGER IF NOT EXISTS trg_{table}_attachments_delete
            AFTER DELETE ON {table}
            BEGIN
                DELETE FROM attachments
                WHERE profile_id=OLD.profile_id AND record_table='{table}' AND record_id=OLD.id;
            END"""
        )
    db.conn.commit()


def _validate_table(table: str) -> None:
    if table not in ATTACHMENT_TABLES:
        raise ValueError(f"Attachments are not enabled for {table}.")


def list_attachments(db, table: str, record_id: int) -> list[dict[str, Any]]:
    _validate_table(table)
    ensure_attachment_schema(db)
    rows = db.conn.execute(
        """SELECT id, profile_id, record_table, record_id, original_name, mime_type,
                  size_bytes, sha256, created_at
           FROM attachments
           WHERE profile_id=? AND record_table=? AND record_id=?
           ORDER BY original_name COLLATE NOCASE, id""",
        (db.current_profile_id, table, int(record_id)),
    ).fetchall()
    return [dict(row) for row in rows]


def attachment_count(db, table: str, record_id: int) -> int:
    _validate_table(table)
    ensure_attachment_schema(db)
    row = db.conn.execute(
        "SELECT COUNT(*) FROM attachments WHERE profile_id=? AND record_table=? AND record_id=?",
        (db.current_profile_id, table, int(record_id)),
    ).fetchone()
    return int(row[0]) if row else 0


def get_attachment(db, attachment_id: int) -> dict[str, Any] | None:
    ensure_attachment_schema(db)
    row = db.conn.execute(
        "SELECT * FROM attachments WHERE id=? AND profile_id=?",
        (int(attachment_id), db.current_profile_id),
    ).fetchone()
    return dict(row) if row else None


def add_files(db, table: str, record_id: int, paths: Iterable[str | Path]) -> list[int]:
    _validate_table(table)
    ensure_attachment_schema(db)
    added: list[int] = []
    for source in paths:
        path = Path(source)
        if not path.is_file():
            continue
        content = path.read_bytes()
        digest = hashlib.sha256(content).hexdigest()
        mime_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        cur = db.conn.execute(
            """INSERT INTO attachments
               (profile_id, record_table, record_id, original_name, mime_type, size_bytes, sha256, content)
               VALUES (?,?,?,?,?,?,?,?)""",
            (
                db.current_profile_id,
                table,
                int(record_id),
                path.name,
                mime_type,
                len(content),
                digest,
                sqlite_binary(content),
            ),
        )
        added.append(int(cur.lastrowid))
    db.conn.commit()
    return added


def sqlite_binary(content: bytes):
    # Imported lazily to keep this module's public surface focused on attachments.
    import sqlite3

    return sqlite3.Binary(content)


def delete_attachment(db, attachment_id: int) -> None:
    ensure_attachment_schema(db)
    db.conn.execute(
        "DELETE FROM attachments WHERE id=? AND profile_id=?",
        (int(attachment_id), db.current_profile_id),
    )
    db.conn.commit()


def all_profile_attachments(db) -> list[dict[str, Any]]:
    ensure_attachment_schema(db)
    rows = db.conn.execute(
        """SELECT id, profile_id, record_table, record_id, original_name, mime_type,
                  size_bytes, sha256, created_at
           FROM attachments WHERE profile_id=?
           ORDER BY record_table, record_id, original_name COLLATE NOCASE""",
        (db.current_profile_id,),
    ).fetchall()
    return [dict(row) for row in rows]


def _safe_name(value: str) -> str:
    cleaned = "".join(c if c.isalnum() or c in " ._-" else "_" for c in value).strip()
    return cleaned or "document"


def export_profile_documents(db, destination: str | Path) -> int:
    """Export every attachment for the active profile into a ZIP with a manifest."""
    ensure_attachment_schema(db)
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    rows = all_profile_attachments(db)
    manifest = io.StringIO()
    writer = csv.writer(manifest)
    writer.writerow(["Record Type", "Record ID", "Original Filename", "Size (bytes)", "SHA-256"])

    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        used: set[str] = set()
        for meta in rows:
            full = get_attachment(db, meta["id"])
            if not full:
                continue
            table = _safe_name(str(meta["record_table"]).replace("_", " ").title())
            original = _safe_name(str(meta["original_name"]))
            base = f"Documents/{table}/{meta['record_id']}_{original}"
            arcname = base
            counter = 2
            while arcname.casefold() in used:
                p = Path(base)
                arcname = str(p.with_name(f"{p.stem}_{counter}{p.suffix}"))
                counter += 1
            used.add(arcname.casefold())
            archive.writestr(arcname, bytes(full["content"]))
            writer.writerow([
                meta["record_table"],
                meta["record_id"],
                meta["original_name"],
                meta["size_bytes"],
                meta["sha256"],
            ])
        archive.writestr("Documents/manifest.csv", manifest.getvalue().encode("utf-8"))
    return len(rows)


def open_attachment_bytes(name: str, content: bytes) -> None:
    suffix = Path(name).suffix
    temp_dir = Path(tempfile.mkdtemp(prefix="fcv_attachment_"))
    path = temp_dir / _safe_name(name)
    if suffix and not path.suffix:
        path = path.with_suffix(suffix)
    path.write_bytes(content)
    if sys.platform.startswith("win"):
        os.startfile(str(path))
    elif sys.platform == "darwin":
        subprocess.Popen(["open", str(path)])
    else:
        subprocess.Popen(["xdg-open", str(path)])


def _generic_image(name: str, size: tuple[int, int]) -> Image.Image:
    image = Image.new("RGB", size, "white")
    draw = ImageDraw.Draw(image)
    ext = Path(name).suffix.upper().lstrip(".") or "FILE"
    label = ext[:8]
    font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), label, font=font)
    x = max(4, (size[0] - (bbox[2] - bbox[0])) // 2)
    y = max(4, (size[1] - (bbox[3] - bbox[1])) // 2)
    draw.rectangle((2, 2, size[0] - 3, size[1] - 3), outline="gray", width=2)
    draw.text((x, y), label, fill="black", font=font)
    return image


def preview_image(name: str, content: bytes, max_size: tuple[int, int]) -> Image.Image:
    suffix = Path(name).suffix.lower()
    try:
        if suffix == ".pdf":
            document = pymupdf.open(stream=content, filetype="pdf")
            try:
                if document.page_count:
                    page = document.load_page(0)
                    pix = page.get_pixmap(matrix=pymupdf.Matrix(1.5, 1.5), alpha=False)
                    image = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
                else:
                    image = _generic_image(name, (320, 420))
            finally:
                document.close()
        elif suffix in {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".gif", ".webp"}:
            image = Image.open(io.BytesIO(content)).convert("RGB")
        else:
            image = _generic_image(name, (320, 420))
    except Exception:
        image = _generic_image(name, (320, 420))
    image.thumbnail(max_size, Image.Resampling.LANCZOS)
    return image


def thumbnail_photo(master, attachment: dict[str, Any] | None, size: tuple[int, int] = (54, 54)):
    if not attachment:
        return None
    image = preview_image(str(attachment["original_name"]), bytes(attachment["content"]), size)
    canvas = Image.new("RGB", size, "white")
    x = (size[0] - image.width) // 2
    y = (size[1] - image.height) // 2
    canvas.paste(image, (x, y))
    return ImageTk.PhotoImage(canvas, master=master)


class AttachmentPicker(ttk.LabelFrame):
    """Staged attachment editor used inside Add/Edit record dialogs."""

    def __init__(self, parent, db, table: str, record_id: int | None = None):
        super().__init__(parent, text="Documents", padding=8)
        _validate_table(table)
        ensure_attachment_schema(db)
        self.db = db
        self.table = table
        self.record_id = record_id
        self.pending: list[Path] = []
        self.removed_ids: set[int] = set()

        self.listbox = tk.Listbox(self, height=4, exportselection=False)
        self.listbox.pack(side="left", fill="both", expand=True)
        buttons = ttk.Frame(self)
        buttons.pack(side="right", fill="y", padx=(8, 0))
        ttk.Button(buttons, text="Add Document...", command=self.add).pack(fill="x", pady=2)
        ttk.Button(buttons, text="Remove", command=self.remove).pack(fill="x", pady=2)
        ttk.Button(buttons, text="Open", command=self.open_selected).pack(fill="x", pady=2)
        self.refresh()

    def _items(self):
        existing = [] if self.record_id is None else [a for a in list_attachments(self.db, self.table, self.record_id) if a["id"] not in self.removed_ids]
        return [("existing", a) for a in existing] + [("pending", p) for p in self.pending]

    def refresh(self):
        self.listbox.delete(0, "end")
        for kind, item in self._items():
            name = item["original_name"] if kind == "existing" else item.name
            self.listbox.insert("end", name)

    def add(self):
        paths = filedialog.askopenfilenames(title="Attach Documents", filetypes=FILE_TYPES, parent=self.winfo_toplevel())
        for raw in paths:
            p = Path(raw)
            if p.is_file() and p not in self.pending:
                self.pending.append(p)
        self.refresh()

    def remove(self):
        selection = self.listbox.curselection()
        if not selection:
            return
        index = int(selection[0])
        kind, item = self._items()[index]
        if kind == "existing":
            self.removed_ids.add(int(item["id"]))
        else:
            self.pending.remove(item)
        self.refresh()

    def open_selected(self):
        selection = self.listbox.curselection()
        if not selection:
            return
        kind, item = self._items()[int(selection[0])]
        try:
            if kind == "existing":
                full = get_attachment(self.db, int(item["id"]))
                if full:
                    open_attachment_bytes(full["original_name"], bytes(full["content"]))
            else:
                content = item.read_bytes()
                open_attachment_bytes(item.name, content)
        except Exception as exc:
            messagebox.showerror("Open Document", str(exc), parent=self.winfo_toplevel())

    def commit(self, record_id: int) -> None:
        for attachment_id in self.removed_ids:
            delete_attachment(self.db, attachment_id)
        if self.pending:
            add_files(self.db, self.table, record_id, self.pending)
        self.record_id = record_id
        self.pending.clear()
        self.removed_ids.clear()
        self.refresh()


class AttachmentViewer(tk.Toplevel):
    def __init__(self, parent, db, table: str, record_id: int):
        super().__init__(parent)
        self.db = db
        self.table = table
        self.record_id = int(record_id)
        self.title("Document Viewer")
        self.geometry("1000x720")
        self.minsize(760, 520)
        self.transient(parent.winfo_toplevel())
        self._image_ref = None

        outer = ttk.Frame(self, padding=10)
        outer.pack(fill="both", expand=True)
        left = ttk.Frame(outer)
        left.pack(side="left", fill="y", padx=(0, 10))
        ttk.Label(left, text="Attached Documents").pack(anchor="w")
        self.listbox = tk.Listbox(left, width=34, exportselection=False)
        self.listbox.pack(fill="y", expand=True, pady=(5, 8))
        ttk.Button(left, text="Open Original", command=self.open_original).pack(fill="x")

        right = ttk.Frame(outer)
        right.pack(side="left", fill="both", expand=True)
        self.name_var = tk.StringVar(value="")
        ttk.Label(right, textvariable=self.name_var).pack(anchor="w", pady=(0, 5))
        self.canvas = tk.Canvas(right, background="#555555", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", lambda _e: self.render())

        self.attachments = list_attachments(db, table, self.record_id)
        for item in self.attachments:
            self.listbox.insert("end", item["original_name"])
        self.listbox.bind("<<ListboxSelect>>", lambda _e: self.render())
        if self.attachments:
            self.listbox.selection_set(0)
            self.render()
        else:
            self.name_var.set("No documents are attached to this record.")

    def selected(self):
        sel = self.listbox.curselection()
        if not sel:
            return None
        return self.attachments[int(sel[0])]

    def render(self):
        meta = self.selected()
        if not meta:
            return
        full = get_attachment(self.db, int(meta["id"]))
        if not full:
            return
        self.name_var.set(f"{full['original_name']}  ({int(full['size_bytes']):,} bytes)")
        width = max(200, self.canvas.winfo_width() - 20)
        height = max(200, self.canvas.winfo_height() - 20)
        image = preview_image(full["original_name"], bytes(full["content"]), (width, height))
        self._image_ref = ImageTk.PhotoImage(image, master=self.canvas)
        self.canvas.delete("all")
        self.canvas.create_image(self.canvas.winfo_width() // 2, self.canvas.winfo_height() // 2, image=self._image_ref, anchor="center")

    def open_original(self):
        meta = self.selected()
        if not meta:
            return
        full = get_attachment(self.db, int(meta["id"]))
        if full:
            try:
                open_attachment_bytes(full["original_name"], bytes(full["content"]))
            except Exception as exc:
                messagebox.showerror("Open Document", str(exc), parent=self)
