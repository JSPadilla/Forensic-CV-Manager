from __future__ import annotations

import os
import shutil
import sqlite3
import sys
import webbrowser
import json
from datetime import date, datetime
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Any

from database import Database
from seed_data import seed
from sample_data import load_sample_profile
from profile_io import export_profile, import_profile
from pdf_export import generate_pdf
from update_checker import check_github_release
from app_config import APP_NAME, APP_VERSION, GITHUB_REPOSITORY
from cv_generator import generate_cv
from date_utils import normalize_date, date_sort_key
from ui_modern import SplashScreen, PdfPreviewWindow, make_preview_temp_path, resource_path
from attachments import (
    ATTACHMENT_TABLES, AttachmentPicker, AttachmentViewer,
    all_profile_attachments, ensure_attachment_schema, export_profile_documents,
    get_attachment, list_attachments, thumbnail_photo,
)

DATE_FIELDS = {"start_date", "end_date", "graduation_date", "attended_date", "expiration_date", "earned_date", "testimony_date", "achievement_date"}
YEAR_FIELDS = {"start_year", "end_year"}

TABLE_CONFIG = {
    "employment": {
        "label": "Employment",
        "display": ["employer", "title", "start_date", "end_date"],
        "fields": [("employer", "Employer", "entry"), ("title", "Title", "entry"), ("start_date", "Start Date", "entry"), ("end_date", "End Date", "entry"), ("location", "Location", "entry"), ("description", "Description / Duties", "text")],
    },
    "education": {
        "label": "Education",
        "display": ["degree", "institution", "graduation_date", "honors"],
        "fields": [("degree", "Degree / Program", "entry"), ("institution", "Institution", "entry"), ("graduation_date", "Graduation Date", "entry"), ("honors", "Honors", "entry"), ("notes", "Notes", "text")],
    },
    "training": {
        "label": "Training",
        "display": ["attended_date", "course_name", "provider", "hours", "core_training"],
        "fields": [("attended_date", "Date Attended", "entry"), ("course_name", "Course Name", "entry"), ("provider", "Provider", "entry"), ("hours", "Hours", "entry"), ("category", "Category", "entry"), ("certificate_number", "Certificate Number", "entry"), ("expiration_date", "Expiration Date", "entry"), ("core_training", "Include in Core Training", "check"), ("notes", "Notes", "text")],
    },
    "certifications": {
        "label": "Certifications",
        "display": ["certification", "issuing_organization", "earned_date", "expiration_date", "status"],
        "fields": [("certification", "Certification", "entry"), ("issuing_organization", "Issuing Organization", "entry"), ("earned_date", "Earned Date", "entry"), ("expiration_date", "Expiration Date", "entry"), ("credential_number", "Credential Number", "entry"), ("status", "Status", "entry"), ("notes", "Notes", "text")],
    },
    "testimony": {
        "label": "Courtroom Testimony",
        "display": ["testimony_date", "case_number", "court", "witness_type"],
        "fields": [("testimony_date", "Testimony Date", "entry"), ("case_number", "Case Number", "entry"), ("court", "Court", "entry"), ("jurisdiction", "Jurisdiction", "entry"), ("witness_type", "Witness Type", "combo", ["Fact Witness", "Expert Witness"]), ("party", "Party", "entry"), ("subject", "Subject / Discipline", "entry"), ("outcome", "Outcome", "entry"), ("notes", "Notes", "text")],
    },
    "teaching": {
        "label": "Teaching",
        "display": ["organization", "role", "course_name", "start_date", "end_date"],
        "fields": [("organization", "Organization", "entry"), ("role", "Role", "entry"), ("course_name", "Course", "entry"), ("start_date", "Start Date", "entry"), ("end_date", "End Date", "entry"), ("hours", "Hours", "entry"), ("description", "Description", "text")],
    },
    "organizations": {
        "label": "Organizations",
        "display": ["organization", "role", "start_year", "end_year"],
        "fields": [("organization", "Organization", "entry"), ("role", "Role", "entry"), ("start_year", "Start Year", "entry"), ("end_year", "End Year", "entry"), ("notes", "Notes", "text")],
    },
    "skills": {
        "label": "Skills & Tools",
        "display": ["skill", "category", "proficiency"],
        "fields": [("skill", "Skill / Tool", "entry"), ("category", "Category", "entry"), ("proficiency", "Proficiency", "entry"), ("notes", "Notes", "text")],
    },
    "achievements": {
        "label": "Achievements",
        "display": ["achievement_date", "achievement", "organization", "category"],
        "fields": [("achievement", "Achievement", "entry"), ("achievement_date", "Date", "entry"), ("organization", "Organization", "entry"), ("category", "Category", "entry"), ("description", "Description", "text")],
    },
}


def application_dir() -> Path:
    """Return the folder containing the executable or source files."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def portable_data_dir() -> Path:
    """Store writable application data beside the app for flash-drive use."""
    path = application_dir() / "data"
    path.mkdir(parents=True, exist_ok=True)
    return path


def ui_settings_path() -> Path:
    return portable_data_dir() / "ui_settings.json"


def load_theme_preference() -> str:
    try:
        value = json.loads(ui_settings_path().read_text(encoding="utf-8")).get("theme", "light")
        return value if value in {"light", "dark"} else "light"
    except Exception:
        return "light"


def save_theme_preference(theme: str) -> None:
    try:
        ui_settings_path().write_text(json.dumps({"theme": theme}, indent=2), encoding="utf-8")
    except OSError:
        pass


def portable_resume_dir() -> Path:
    """Store generated CVs beside the application for flash-drive portability."""
    path = application_dir() / "Resume"
    path.mkdir(parents=True, exist_ok=True)
    return path


def legacy_database_path() -> Path:
    """Location used by v1 before portable storage was enabled."""
    if sys.platform.startswith("win"):
        base = Path(os.environ.get("LOCALAPPDATA", Path.home()))
    else:
        base = Path.home() / ".local" / "share"
    return base / "ForensicCVManager" / "forensic_cv.sqlite3"


def prepare_portable_database() -> Path:
    """Create a writable portable database from the release template on first run."""
    db_path = portable_data_dir() / "forensic_cv.sqlite3"
    template_path = portable_data_dir() / "template.sqlite3"
    legacy_path = legacy_database_path()
    if not db_path.exists():
        source = template_path if template_path.exists() else (legacy_path if legacy_path.exists() else None)
        if source:
            try:
                shutil.copy2(source, db_path)
            except OSError:
                pass
    return db_path


class ProfileNameDialog(tk.Toplevel):
    def __init__(self, parent, title: str, initial: str = ""):
        super().__init__(parent)
        self.title(title)
        self.transient(parent)
        self.grab_set()
        self.resizable(False, False)
        self.result = None
        self.var = tk.StringVar(value=initial)
        frame = ttk.Frame(self, padding=16)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="Profile Name:").grid(row=0, column=0, sticky="w", pady=5)
        entry = ttk.Entry(frame, textvariable=self.var, width=42)
        entry.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        buttons = ttk.Frame(frame)
        buttons.grid(row=2, column=0, sticky="e")
        ttk.Button(buttons, text="Cancel", command=self.destroy).pack(side="right", padx=4)
        ttk.Button(buttons, text="Save", command=self.save).pack(side="right", padx=4)
        entry.focus_set()
        self.bind("<Return>", lambda e: self.save())
        self.bind("<Escape>", lambda e: self.destroy())

    def save(self):
        value = self.var.get().strip()
        if not value:
            messagebox.showerror("Profile Name", "Enter a profile name.", parent=self)
            return
        self.result = value
        self.destroy()


class RecordDialog(tk.Toplevel):
    def __init__(self, parent, table: str, config: dict[str, Any], initial: dict[str, Any] | None = None):
        super().__init__(parent)
        self.title(("Edit " if initial else "Add ") + config["label"])
        self.transient(parent)
        self.grab_set()
        self.resizable(True, True)
        self.result = None
        self.vars: dict[str, Any] = {}
        self.widgets: dict[str, Any] = {}
        self.attachment_picker = None
        self.columnconfigure(1, weight=1)
        row = 0
        for field in config["fields"]:
            name, label, kind, *extra = field
            ttk.Label(self, text=label + ":").grid(row=row, column=0, sticky="nw", padx=8, pady=5)
            value = "" if initial is None or initial.get(name) is None else initial.get(name)
            if kind == "text":
                widget = tk.Text(self, width=65, height=5, wrap="word")
                try:
                    root = parent.winfo_toplevel()
                    if getattr(root, "theme_name", "light") == "dark":
                        widget.configure(bg="#313338", fg="#f2f3f5", insertbackground="#f2f3f5")
                except Exception:
                    pass
                widget.insert("1.0", str(value))
                widget.grid(row=row, column=1, sticky="nsew", padx=8, pady=5)
                self.rowconfigure(row, weight=1)
            elif kind == "check":
                var = tk.IntVar(value=int(value or 0))
                widget = ttk.Checkbutton(self, variable=var)
                widget.grid(row=row, column=1, sticky="w", padx=8, pady=5)
                self.vars[name] = var
            elif kind == "combo":
                var = tk.StringVar(value=str(value))
                widget = ttk.Combobox(self, textvariable=var, values=extra[0], state="readonly")
                if not value and extra[0]:
                    var.set(extra[0][0])
                widget.grid(row=row, column=1, sticky="ew", padx=8, pady=5)
                self.vars[name] = var
            else:
                var = tk.StringVar(value=str(value))
                widget = ttk.Entry(self, textvariable=var, width=65)
                widget.grid(row=row, column=1, sticky="ew", padx=8, pady=5)
                self.vars[name] = var
            self.widgets[name] = widget
            row += 1
        if table in ATTACHMENT_TABLES:
            record_id = int(initial['id']) if initial and initial.get('id') else None
            self.attachment_picker = AttachmentPicker(self, parent.db, table, record_id)
            self.attachment_picker.grid(row=row, column=0, columnspan=2, sticky='nsew', padx=8, pady=8)
            self.rowconfigure(row, weight=1)
            row += 1
        buttons = ttk.Frame(self)
        buttons.grid(row=row, column=0, columnspan=2, sticky="e", padx=8, pady=10)
        ttk.Button(buttons, text="Cancel", command=self.destroy).pack(side="right", padx=4)
        ttk.Button(buttons, text="Save", command=self.save).pack(side="right", padx=4)
        self.bind("<Escape>", lambda e: self.destroy())
        self.geometry("760x620")

    def save(self):
        result = {}
        for field in self.widgets:
            widget = self.widgets[field]
            if isinstance(widget, tk.Text):
                value = widget.get("1.0", "end").strip()
            else:
                value = self.vars[field].get()
            if field == "hours":
                try:
                    value = float(value) if str(value).strip() else None
                except ValueError:
                    messagebox.showerror("Invalid Hours", "Hours must be a number.", parent=self)
                    return
            elif field in DATE_FIELDS:
                try:
                    value = normalize_date(value, allow_present=field == "end_date")
                except ValueError as exc:
                    messagebox.showerror("Invalid Date", str(exc), parent=self)
                    self.widgets[field].focus_set()
                    return
            elif field in YEAR_FIELDS:
                try:
                    value = normalize_date(value, allow_present=field == "end_year", allow_year_only=True)
                    if value not in ("", "Present") and len(value) != 4:
                        raise ValueError(f'"{value}" must be a four-digit year or Present.')
                except ValueError as exc:
                    messagebox.showerror("Invalid Year", str(exc), parent=self)
                    self.widgets[field].focus_set()
                    return
            result[field] = value
        self.result = result
        self.destroy()


class RecordsTab(ttk.Frame):
    def __init__(self, parent, db: Database, table: str, status_callback):
        super().__init__(parent)
        self.db = db
        self.table = table
        self.config_data = TABLE_CONFIG[table]
        self.status_callback = status_callback
        self.search_var = tk.StringVar()
        self.sort_column: str | None = None
        self.sort_descending = False
        top = ttk.Frame(self)
        top.pack(fill="x", padx=8, pady=8)
        ttk.Label(top, text="Search:").pack(side="left")
        entry = ttk.Entry(top, textvariable=self.search_var, width=35)
        entry.pack(side="left", padx=5)
        self.search_var.trace_add("write", lambda *_: self.refresh())
        ttk.Button(top, text="Add", command=self.add).pack(side="right", padx=3)
        ttk.Button(top, text="Edit", command=self.edit).pack(side="right", padx=3)
        ttk.Button(top, text="Delete", command=self.delete).pack(side="right", padx=3)

        cols = self.config_data["display"]
        self.attachments_enabled = self.table in ATTACHMENT_TABLES
        self._thumbnail_refs = {}
        if self.attachments_enabled:
            ttk.Style(self).configure("Document.Treeview", rowheight=60)
            self.tree = ttk.Treeview(self, columns=cols, show=("tree", "headings"), selectmode="browse", style="Document.Treeview")
            self.tree.heading("#0", text="Document")
            self.tree.column("#0", width=86, minwidth=72, stretch=False, anchor="center")
        else:
            self.tree = ttk.Treeview(self, columns=cols, show="headings", selectmode="browse")
        for col in cols:
            self.tree.heading(
                col,
                text=self._heading_text(col),
                command=lambda column=col: self.sort_by(column),
            )
            width = 110
            if col in {"course_name", "certification", "employer", "degree", "skill", "achievement"}:
                width = 260
            self.tree.column(col, width=width, minwidth=70, stretch=True)
        y = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        x = ttk.Scrollbar(self, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=y.set, xscrollcommand=x.set)
        self.tree.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=(0, 8))
        y.pack(side="right", fill="y", padx=(0, 8), pady=(0, 8))
        x.pack(side="bottom", fill="x", padx=8)
        if self.attachments_enabled:
            self.tree.bind("<ButtonRelease-1>", self._document_click)
        self.tree.bind("<Double-1>", self._double_click)
        self.refresh()

    def _document_click(self, event):
        if not self.attachments_enabled or self.tree.identify_column(event.x) != "#0":
            return
        iid = self.tree.identify_row(event.y)
        if iid and list_attachments(self.db, self.table, int(iid)):
            self.after(1, lambda: AttachmentViewer(self, self.db, self.table, int(iid)))

    def _double_click(self, event):
        if self.attachments_enabled and self.tree.identify_column(event.x) == "#0":
            return
        self.edit()

    def _heading_text(self, column: str) -> str:
        label = column.replace("_", " ").title()
        if self.sort_column == column:
            return f"{label} {'▼' if self.sort_descending else '▲'}"
        return label

    def _update_headings(self) -> None:
        for column in self.config_data["display"]:
            self.tree.heading(column, text=self._heading_text(column))

    @staticmethod
    def _natural_text_key(value: object):
        text = "" if value is None else str(value).strip().casefold()
        parts = []
        current = ""
        numeric = None
        for char in text:
            is_digit = char.isdigit()
            if numeric is None or is_digit == numeric:
                current += char
                numeric = is_digit
            else:
                parts.append(int(current) if numeric else current)
                current = char
                numeric = is_digit
        if current:
            parts.append(int(current) if numeric else current)
        return tuple((0, part) if isinstance(part, int) else (1, part) for part in parts)

    def _sort_key(self, row: dict[str, Any], column: str):
        value = row.get(column)
        if column in DATE_FIELDS or column in YEAR_FIELDS:
            return date_sort_key(value, present_is_latest=column in {"end_date", "end_year"})
        if column == "hours":
            try:
                return float(value)
            except (TypeError, ValueError):
                return float("-inf")
        if column == "core_training":
            return 1 if value else 0
        return self._natural_text_key(value)

    def sort_by(self, column: str) -> None:
        if column == self.sort_column:
            self.sort_descending = not self.sort_descending
        else:
            self.sort_column = column
            self.sort_descending = False
        self._update_headings()
        self.refresh()

    def refresh(self):
        term = self.search_var.get().lower().strip()
        selected = set(self.tree.selection())
        self.tree.delete(*self.tree.get_children())
        rows = []
        for row in self.db.list_rows(self.table):
            hay = " ".join(str(v or "") for v in row.values()).lower()
            if term and term not in hay:
                continue
            rows.append(row)

        if self.sort_column:
            # Keep blank values at the bottom in either direction while sorting
            # populated values using the appropriate data type.
            populated = [r for r in rows if str(r.get(self.sort_column) or "").strip()]
            blanks = [r for r in rows if not str(r.get(self.sort_column) or "").strip()]
            populated.sort(
                key=lambda r: self._sort_key(r, self.sort_column),
                reverse=self.sort_descending,
            )
            rows = populated + blanks

        self._thumbnail_refs.clear()
        for row in rows:
            values = []
            for col in self.config_data["display"]:
                value = row.get(col, "")
                if col == "core_training":
                    value = "Yes" if value else "No"
                values.append("" if value is None else value)
            iid = str(row["id"])
            if self.attachments_enabled:
                attachments = list_attachments(self.db, self.table, row["id"])
                image = None
                label = ""
                if attachments:
                    full = get_attachment(self.db, attachments[0]["id"])
                    if full:
                        image = thumbnail_photo(self, full)
                        if image is not None:
                            self._thumbnail_refs[iid] = image
                    label = str(len(attachments)) if len(attachments) > 1 else ""
                self.tree.insert("", "end", iid=iid, text=label, image=image or "", values=values)
            else:
                self.tree.insert("", "end", iid=iid, values=values)
            if iid in selected:
                self.tree.selection_add(iid)
        self.status_callback(f"{self.config_data['label']}: {len(self.tree.get_children())} record(s)")

    def selected_id(self):
        sel = self.tree.selection()
        return int(sel[0]) if sel else None

    def add(self):
        dlg = RecordDialog(self, self.table, self.config_data)
        self.wait_window(dlg)
        if dlg.result is not None:
            row_id = self.db.insert_row(self.table, dlg.result)
            if dlg.attachment_picker is not None:
                dlg.attachment_picker.commit(row_id)
            self.refresh()

    def edit(self):
        row_id = self.selected_id()
        if not row_id:
            messagebox.showinfo("Select Record", "Select a record to edit.", parent=self)
            return
        dlg = RecordDialog(self, self.table, self.config_data, self.db.get_row(self.table, row_id))
        self.wait_window(dlg)
        if dlg.result is not None:
            self.db.update_row(self.table, row_id, dlg.result)
            if dlg.attachment_picker is not None:
                dlg.attachment_picker.commit(row_id)
            self.refresh()

    def delete(self):
        row_id = self.selected_id()
        if not row_id:
            messagebox.showinfo("Select Record", "Select a record to delete.", parent=self)
            return
        if messagebox.askyesno("Delete Record", "Delete the selected record?", parent=self):
            self.db.delete_row(self.table, row_id)
            self.refresh()


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.withdraw()
        self.title(f"{APP_NAME} {APP_VERSION}")
        self.geometry("1250x760")
        self.minsize(950, 600)
        self.theme_name = load_theme_preference()
        try:
            self.iconbitmap(str(resource_path("assets/app.ico")))
        except Exception:
            pass
        self.splash = SplashScreen(self, APP_VERSION)
        self.splash.step("Preparing portable workspace…", 20)
        self.db_path = prepare_portable_database()
        self.splash.step("Opening credential database…", 42)
        self.db = Database(self.db_path)
        ensure_attachment_schema(self.db)
        seed(self.db)
        self.splash.step("Loading profiles and records…", 60)
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self._style()
        self._menu()
        self.splash.step("Building application workspace…", 76)
        self.status = tk.StringVar(value="Ready")
        self.profile_bar = ttk.Frame(self, padding=(8, 6))
        self.profile_bar.pack(fill="x")
        ttk.Label(self.profile_bar, text="Active Profile:").pack(side="left")
        self.profile_choice = tk.StringVar()
        self.profile_combo = ttk.Combobox(self.profile_bar, textvariable=self.profile_choice, state="readonly", width=34)
        self.profile_combo.pack(side="left", padx=6)
        self.profile_combo.bind("<<ComboboxSelected>>", self.switch_profile)
        ttk.Button(self.profile_bar, text="Manage Profiles", command=self.manage_profiles).pack(side="left", padx=3)
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)
        self._dashboard_tab()
        self._profile_tab()
        self.record_tabs = {}
        for table in TABLE_CONFIG:
            tab = RecordsTab(self.notebook, self.db, table, self.set_status)
            self.record_tabs[table] = tab
            self.notebook.add(tab, text=TABLE_CONFIG[table]["label"])
        self._generate_tab()
        ttk.Label(self, textvariable=self.status, relief="sunken", anchor="w").pack(fill="x", side="bottom")
        self.refresh_profile_selector()
        self._on_tab_changed()
        self._apply_native_widget_theme()
        self.splash.step("Ready", 100)
        self.update_idletasks()
        self.splash.destroy()
        self.deiconify()
        self.after(1800, self.auto_check_for_updates)

    def _style(self):
        style = ttk.Style(self)
        self.style = style
        if self.theme_name == "dark":
            self._apply_dark_ttk_style()
        else:
            self._apply_light_ttk_style()

    def _apply_light_ttk_style(self):
        style = self.style
        try:
            style.theme_use("vista" if sys.platform.startswith("win") else "clam")
        except tk.TclError:
            pass
        style.configure("Treeview", rowheight=26)
        style.configure("Title.TLabel", font=("Segoe UI", 18, "bold"))
        style.configure("Metric.TLabel", font=("Segoe UI", 20, "bold"), foreground="#1f4e79")

    def _apply_dark_ttk_style(self):
        style = self.style
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        bg = "#202225"
        panel = "#2b2d31"
        field = "#313338"
        fg = "#f2f3f5"
        muted = "#b5bac1"
        accent = "#6ea8d7"
        self.configure(bg=bg)
        style.configure(".", background=bg, foreground=fg, fieldbackground=field)
        style.configure("TFrame", background=bg)
        style.configure("TLabel", background=bg, foreground=fg)
        style.configure("TLabelframe", background=bg, foreground=fg)
        style.configure("TLabelframe.Label", background=bg, foreground=fg)
        style.configure("TButton", background=panel, foreground=fg, padding=(8, 4))
        style.map("TButton", background=[("active", "#3a3d42")])
        style.configure("TEntry", fieldbackground=field, foreground=fg)
        style.configure("TCombobox", fieldbackground=field, foreground=fg, background=field)
        style.map("TCombobox", fieldbackground=[("readonly", field)], foreground=[("readonly", fg)])
        style.configure("TNotebook", background=bg, borderwidth=0)
        style.configure("TNotebook.Tab", background=panel, foreground=muted, padding=(10, 5))
        style.map("TNotebook.Tab", background=[("selected", field)], foreground=[("selected", fg)])
        style.configure("Treeview", rowheight=26, background=field, fieldbackground=field, foreground=fg)
        style.configure("Treeview.Heading", background=panel, foreground=fg)
        style.map("Treeview", background=[("selected", "#3d6382")], foreground=[("selected", "#ffffff")])
        style.configure("Title.TLabel", font=("Segoe UI", 18, "bold"), background=bg, foreground=fg)
        style.configure("Metric.TLabel", font=("Segoe UI", 20, "bold"), background=bg, foreground=accent)

    def set_theme(self, theme_name: str):
        if theme_name not in {"light", "dark"}:
            return
        self.theme_name = theme_name
        if theme_name == "dark":
            self._apply_dark_ttk_style()
        else:
            self.configure(bg="#f0f0f0")
            self._apply_light_ttk_style()
        save_theme_preference(theme_name)
        self._apply_native_widget_theme()
        self.set_status("Dark mode enabled" if theme_name == "dark" else "Light mode enabled")

    def _apply_native_widget_theme(self):
        dark = self.theme_name == "dark"
        text_bg, text_fg = (("#313338", "#f2f3f5") if dark else ("#ffffff", "#000000"))
        canvas_bg = "#2b2d31" if dark else "#ffffff"
        self._theme_walk(self, text_bg, text_fg, canvas_bg)
        if hasattr(self, "dashboard_chart"):
            try:
                self.dashboard_chart.configure(background=canvas_bg)
                self.refresh_dashboard()
            except Exception:
                pass

    def _theme_walk(self, widget, text_bg, text_fg, canvas_bg):
        for child in widget.winfo_children():
            if isinstance(child, tk.Text):
                try:
                    child.configure(bg=text_bg, fg=text_fg, insertbackground=text_fg)
                except tk.TclError:
                    pass
            elif isinstance(child, tk.Canvas):
                try:
                    child.configure(background=canvas_bg)
                except tk.TclError:
                    pass
            self._theme_walk(child, text_bg, text_fg, canvas_bg)

    def _menu(self):
        menu = tk.Menu(self)
        file_menu = tk.Menu(menu, tearoff=False)
        file_menu.add_command(label="New Blank Profile...", command=self.new_blank_profile)
        file_menu.add_command(label="Load Sample Data...", command=self.load_sample_data)
        file_menu.add_separator()
        file_menu.add_command(label="Import Profile...", command=self.import_profile_file)
        file_menu.add_command(label="Export Current Profile...", command=self.export_profile_file)
        file_menu.add_separator()
        file_menu.add_command(label="Backup Database...", command=self.backup_db)
        file_menu.add_command(label="Restore Database...", command=self.restore_db)
        file_menu.add_separator()
        file_menu.add_command(label="Clear Current Profile Data...", command=self.clear_profile_data)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_close)
        menu.add_cascade(label="File", menu=file_menu)
        tools_menu = tk.Menu(menu, tearoff=False)
        appearance_menu = tk.Menu(tools_menu, tearoff=False)
        appearance_menu.add_command(label="Light Mode", command=lambda: self.set_theme("light"))
        appearance_menu.add_command(label="Dark Mode", command=lambda: self.set_theme("dark"))
        tools_menu.add_cascade(label="Appearance", menu=appearance_menu)
        tools_menu.add_separator()
        tools_menu.add_command(label="Check for Updates...", command=self.check_for_updates)
        tools_menu.add_command(label="Open Resume Folder", command=self.open_resume_folder)
        tools_menu.add_command(label="Open Data Folder", command=self.open_data_folder)
        menu.add_cascade(label="Tools", menu=tools_menu)
        help_menu = tk.Menu(menu, tearoff=False)
        help_menu.add_command(label="User Manual", command=self.show_user_manual)
        help_menu.add_command(label="How to Add Records", command=lambda: self.show_user_manual("Adding Records"))
        help_menu.add_separator()
        help_menu.add_command(label="About", command=self.show_about)
        menu.add_cascade(label="Help", menu=help_menu)
        self.config(menu=menu)

    def show_about(self):
        messagebox.showinfo(
            "About",
            f"{APP_NAME} {APP_VERSION}\n\n"
            "Portable professional credential and CV tracking.\n"
            "Versioning follows Semantic Versioning (MAJOR.MINOR.PATCH).",
            parent=self,
        )

    def show_user_manual(self, initial_section: str = "Getting Started"):
        manual = tk.Toplevel(self)
        manual.title(f"{APP_NAME} User Manual")
        manual.geometry("900x680")
        manual.minsize(700, 500)
        manual.transient(self)

        outer = ttk.Frame(manual, padding=10)
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text="User Manual", style="Title.TLabel").pack(anchor="w", pady=(0, 8))
        ttk.Label(outer, text=f"Forensic CV Manager {APP_VERSION}").pack(anchor="w", pady=(0, 10))

        book = ttk.Notebook(outer)
        book.pack(fill="both", expand=True)

        sections = {
            "Getting Started": """GETTING STARTED

1. Select an existing profile from the Active Profile list, or choose File > New Blank Profile.
2. Open the Profile tab and enter the examiner's contact information and professional summary.
3. Use the record tabs to add employment, education, training, certifications, testimony, teaching, organizations, skills, and achievements.
4. Open Generate CV, select the sections, and create a Word or PDF document.

The working database is stored in the data folder beside the application. Generated documents are stored in the Resume folder by default.""",
            "Adding Records": """ADDING RECORDS

1. Select the correct profile from Active Profile.
2. Open the appropriate tab, such as Training, Certifications, or Courtroom Testimony.
3. Select Add in the upper-right corner of that tab.
4. Complete the fields in the Add Record window.
5. Select Save. The new record appears in the table and is immediately available to the dashboard and CV generator.

DATE ENTRY
Common date formats are accepted, including 3/5/2026, 03-05-2026, 2026-03-05, March 5, 2026, March 2026, 03/2026, and 2026. Employment end dates may use Present, Current, Ongoing, or Now. Dates are normalized internally for reliable sorting.

LONG TEXT
Description and Notes fields accept multiline text. The complete text is retained and printed in generated CVs.

TRAINING HOURS
Enter only the documented course hours as a number. Leave the field blank when hours are unknown. Training totals are calculated automatically.

CORE TRAINING
On a training record, select Include in Core Training when the course should appear in the concise Core Training section of the CV.""",
            "Editing and Deleting": """EDITING AND DELETING RECORDS

To edit a record, select it in the table and choose Edit. Make the changes and select Save.

To delete a record, select it and choose Delete. Confirm the deletion when prompted. Deleted records cannot be recovered unless a database backup is restored.

File > Clear Current Profile Data removes all professional records for the selected profile but keeps the profile itself. Manage Profiles can permanently delete an entire profile and its linked records. Create a backup before performing bulk deletions.""",
            "Profiles": """MANAGING PROFILES

Use the Active Profile list to switch between examiners. All records, dashboard totals, and generated CV sections are filtered to the selected profile.

Select Manage Profiles to add, rename, switch, or delete profiles. Duplicate profile names are displayed with a parenthetical number for clarity.

File > Export Current Profile creates a portable profile package. File > Import Profile loads a profile package into the current database.""",
            "Generating a CV": """GENERATING A CV

1. Select the correct Active Profile.
2. Open the Generate CV tab.
3. Select the sections to include.
4. Choose Generate Word CV, Preview & Save PDF, or Generate Word + PDF.
5. Confirm the suggested filename and Resume folder location.

Date-based sections are ordered newest to oldest. Long entries and multiline descriptions are included in full. PDF documents are generated directly by the application and do not require Microsoft Word or LibreOffice. Word output remains available for later editing.""",
            "Backup and Portability": """BACKUP AND PORTABILITY

The application is designed to run from a portable folder or flash drive. Keep the executable, data folder, Resume folder, and Backups folder together.

Use File > Backup Database to copy the current SQLite database to another drive or secure location. Use File > Restore Database to replace the working database with a backup.

Do not rely on a flash drive as the only copy of professional records. Maintain a separate encrypted or agency-approved backup.""",
        }

        selected_index = 0
        for index, (title, content) in enumerate(sections.items()):
            page = ttk.Frame(book, padding=8)
            book.add(page, text=title)
            text_frame = ttk.Frame(page)
            text_frame.pack(fill="both", expand=True)
            text = tk.Text(text_frame, wrap="word", padx=12, pady=12, font=("Segoe UI", 10), state="normal")
            scroll = ttk.Scrollbar(text_frame, orient="vertical", command=text.yview)
            text.configure(yscrollcommand=scroll.set)
            text.pack(side="left", fill="both", expand=True)
            scroll.pack(side="right", fill="y")
            text.insert("1.0", content)
            text.configure(state="disabled")
            if title == initial_section:
                selected_index = index
        book.select(selected_index)
        ttk.Button(outer, text="Close", command=manual.destroy).pack(anchor="e", pady=(10, 0))
        if self.theme_name == "dark":
            self._theme_walk(manual, "#313338", "#f2f3f5", "#2b2d31")

    def refresh_profile_selector(self):
        self._profiles = self.db.list_profiles()
        labels = []
        counts = {}
        for profile in self._profiles:
            base = (profile.get("profile_name") or profile.get("full_name") or "Unnamed Profile").strip()
            counts[base] = counts.get(base, 0) + 1
            label = base if counts[base] == 1 else f"{base} ({counts[base]})"
            labels.append(label)
        self._profile_labels = labels
        self.profile_combo["values"] = labels
        for index, profile in enumerate(self._profiles):
            if profile["id"] == self.db.current_profile_id:
                self.profile_choice.set(labels[index])
                self.profile_combo.current(index)
                break

    def switch_profile(self, event=None):
        index = self.profile_combo.current()
        if index < 0 or index >= len(self._profiles):
            return
        pid = self._profiles[index]["id"]
        if pid == self.db.current_profile_id:
            return
        self.db.set_current_profile(pid)
        self.reload_current_profile()
        self._on_tab_changed()

    def reload_current_profile(self):
        profile = self.db.get_profile()
        for name, var in getattr(self, "profile_vars", {}).items():
            var.set(profile.get(name, ""))
        if hasattr(self, "profile_summary"):
            self.profile_summary.delete("1.0", "end")
            self.profile_summary.insert("1.0", profile.get("summary", ""))
        for tab in getattr(self, "record_tabs", {}).values():
            tab.refresh()
        self.refresh_dashboard()
        self.refresh_profile_selector()
        self._on_tab_changed()

    def manage_profiles(self):
        win = tk.Toplevel(self)
        win.title("Manage Profiles")
        win.transient(self)
        win.grab_set()
        win.geometry("560x360")
        frame = ttk.Frame(win, padding=12)
        frame.pack(fill="both", expand=True)
        tree = ttk.Treeview(frame, columns=("name", "full_name"), show="headings", selectmode="browse")
        tree.heading("name", text="Profile Name")
        tree.heading("full_name", text="Full Name")
        tree.column("name", width=200)
        tree.column("full_name", width=280)
        tree.pack(fill="both", expand=True)
        def refresh():
            tree.delete(*tree.get_children())
            for p in self.db.list_profiles():
                tree.insert("", "end", iid=str(p["id"]), values=(p["profile_name"], p["full_name"]))
        def selected():
            sel = tree.selection()
            return int(sel[0]) if sel else None
        def add():
            dlg = ProfileNameDialog(win, "Add Profile")
            win.wait_window(dlg)
            if dlg.result:
                pid = self.db.create_profile(dlg.result)
                self.db.set_current_profile(pid)
                refresh(); self.reload_current_profile()
        def rename():
            pid = selected()
            if not pid:
                messagebox.showinfo("Select Profile", "Select a profile to rename.", parent=win); return
            current = next(p for p in self.db.list_profiles() if p["id"] == pid)
            dlg = ProfileNameDialog(win, "Rename Profile", current["profile_name"])
            win.wait_window(dlg)
            if dlg.result:
                self.db.rename_profile(pid, dlg.result); refresh(); self.refresh_profile_selector()
        def activate():
            pid = selected()
            if pid:
                self.db.set_current_profile(pid); self.reload_current_profile(); win.destroy()
        def delete():
            pid = selected()
            if not pid:
                messagebox.showinfo("Select Profile", "Select a profile to delete.", parent=win); return
            current = next(p for p in self.db.list_profiles() if p["id"] == pid)
            prompt = f"Permanently delete profile '{current['profile_name']}' and every record linked to it?\n\nThis cannot be undone."
            if not messagebox.askyesno("Delete Profile", prompt, parent=win):
                return
            try:
                self.db.delete_profile(pid); refresh(); self.reload_current_profile()
            except ValueError as exc:
                messagebox.showerror("Delete Profile", str(exc), parent=win)
        buttons = ttk.Frame(frame)
        buttons.pack(fill="x", pady=(10,0))
        ttk.Button(buttons, text="Add", command=add).pack(side="left", padx=3)
        ttk.Button(buttons, text="Rename", command=rename).pack(side="left", padx=3)
        ttk.Button(buttons, text="Set Active", command=activate).pack(side="left", padx=3)
        ttk.Button(buttons, text="Delete", command=delete).pack(side="left", padx=3)
        ttk.Button(buttons, text="Close", command=win.destroy).pack(side="right", padx=3)
        tree.bind("<Double-1>", lambda e: activate())
        refresh()

    def new_blank_profile(self):
        dialog = ProfileNameDialog(self, "New Blank Profile", "New Examiner")
        self.wait_window(dialog)
        if not dialog.result: return
        pid = self.db.create_blank_profile(dialog.result)
        self.db.set_current_profile(pid)
        self.reload_current_profile()
        self.set_status(f"Created blank profile: {dialog.result}")

    def load_sample_data(self):
        name = self.db.get_profile().get("profile_name") or "current profile"
        if not messagebox.askyesno("Load Sample Data", f"Replace all records in '{name}' with fictitious demonstration data?"):
            return
        load_sample_profile(self.db, clear=True)
        self.reload_current_profile()
        self.set_status("Fictitious sample data loaded")

    def export_profile_file(self):
        profile = self.db.get_profile()
        default = (profile.get("profile_name") or "profile").replace(" ", "_") + ".fcvprofile.json"
        out = filedialog.asksaveasfilename(title="Export Profile", defaultextension=".json", initialdir=str(portable_data_dir()), initialfile=default, filetypes=[("Forensic CV Profile", "*.json")])
        if out:
            export_profile(self.db, out)
            self.set_status(f"Profile exported: {out}")

    def import_profile_file(self):
        src = filedialog.askopenfilename(title="Import Profile", filetypes=[("Forensic CV Profile", "*.json"), ("JSON", "*.json")])
        if not src: return
        try:
            pid = import_profile(self.db, src)
            self.db.set_current_profile(pid)
            self.reload_current_profile()
            self.set_status(f"Profile imported: {src}")
        except Exception as exc:
            messagebox.showerror("Import Error", str(exc))

    def auto_check_for_updates(self):
        if not GITHUB_REPOSITORY or GITHUB_REPOSITORY == "OWNER/REPOSITORY":
            return
        try:
            result = check_github_release(GITHUB_REPOSITORY, APP_VERSION, timeout=4)
            if result.update_available and messagebox.askyesno("Update Available", f"Version {result.latest_version} is available. Open the release page?"):
                webbrowser.open(result.release_url)
        except Exception:
            # Startup checks are intentionally quiet when offline.
            pass

    def check_for_updates(self):
        self.set_status("Checking for updates...")
        self.update_idletasks()
        try:
            result = check_github_release(GITHUB_REPOSITORY, APP_VERSION)
            if result.update_available:
                if messagebox.askyesno("Update Available", f"Version {result.latest_version} is available. Open the release page?"):
                    webbrowser.open(result.release_url)
            else:
                message = result.message or f"You are using the current version ({APP_VERSION})."
                messagebox.showinfo("Update Check", message)
        except Exception as exc:
            messagebox.showinfo("Update Check", str(exc))
        self.set_status("Ready")

    def clear_profile_data(self):
        profile = self.db.get_profile()
        name = profile.get("profile_name") or profile.get("full_name") or "current profile"
        prompt = f"Delete ALL employment, education, training, certification, testimony, teaching, organization, skill, and achievement records for '{name}'?\n\nThe profile itself will remain. This cannot be undone."
        if messagebox.askyesno("Clear Profile Data", prompt, parent=self):
            self.db.clear_current_profile_data()
            self.reload_current_profile()
            self.set_status(f"All records cleared for {name}")

    def _dashboard_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Dashboard")
        ttk.Label(tab, text="Professional Qualifications Dashboard", style="Title.TLabel").pack(anchor="w", padx=20, pady=(20, 10))
        self.metrics_frame = ttk.Frame(tab)
        self.metrics_frame.pack(fill="x", padx=20)
        ttk.Button(tab, text="Refresh Dashboard", command=self.refresh_dashboard).pack(anchor="w", padx=20, pady=15)
        body = ttk.Frame(tab)
        body.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        body.columnconfigure(0, weight=3); body.columnconfigure(1, weight=2); body.rowconfigure(0, weight=1)
        self.summary_text = tk.Text(body, height=18, wrap="word", state="disabled")
        self.summary_text.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        chart_box = ttk.LabelFrame(body, text="Professional Record Counts", padding=8)
        chart_box.grid(row=0, column=1, sticky="nsew")
        self.dashboard_chart = tk.Canvas(chart_box, height=300, highlightthickness=0, background="white")
        self.dashboard_chart.pack(fill="both", expand=True)
        self.refresh_dashboard()

    def refresh_dashboard(self):
        for w in self.metrics_frame.winfo_children():
            w.destroy()
        total_hours = self.db.scalar("SELECT COALESCE(SUM(hours),0) FROM training") or 0
        expert = self.db.scalar("SELECT COUNT(*) FROM testimony WHERE witness_type='Expert Witness'") or 0
        fact = self.db.scalar("SELECT COUNT(*) FROM testimony WHERE witness_type='Fact Witness'") or 0
        metrics = [("Training Hours", f"{total_hours:,.2f}"), ("Training Records", str(self.db.count('training'))), ("Certifications", str(self.db.count('certifications'))), ("Expert Testimony", str(expert)), ("Fact Testimony", str(fact))]
        for i, (label, value) in enumerate(metrics):
            box = ttk.LabelFrame(self.metrics_frame, text=label, padding=12)
            box.grid(row=0, column=i, padx=5, sticky="nsew")
            ttk.Label(box, text=value, style="Metric.TLabel").pack()
            self.metrics_frame.columnconfigure(i, weight=1)
        expiring = self.db.conn.execute("SELECT certification, expiration_date FROM certifications WHERE profile_id=? AND expiration_date <> '' ORDER BY expiration_date", (self.db.current_profile_id,)).fetchall()
        alerts = []
        for r in expiring:
            raw = str(r["expiration_date"] or "")
            try:
                normalized = normalize_date(raw, allow_present=False, year_only_ok=True)
                parts = normalized.split("-")
                y, m = int(parts[0]), int(parts[1]) if len(parts) > 1 else 12
                d = int(parts[2]) if len(parts) > 2 else 28
                days = (date(y, m, min(d, 28)) - date.today()).days
                if days < 0: label = "EXPIRED"
                elif days <= 90: label = f"expires in {days} days"
                elif days <= 365: label = f"expires in {days} days"
                else: label = "active"
            except Exception:
                label = "review date"
            alerts.append(f"• {r['certification']}: {raw} — {label}")
        text = "Certification expiration alerts\n\n" + ("\n".join(alerts) if alerts else "No expiration dates entered.")
        text += "\n\nPortable database\n\n" + str(self.db_path)
        text += "\n\nGenerated CV folder\n\n" + str(portable_resume_dir())
        self.summary_text.config(state="normal")
        self.summary_text.delete("1.0", "end")
        self.summary_text.insert("1.0", text)
        self.summary_text.config(state="disabled")

        counts = [("Training", self.db.count("training")), ("Certs", self.db.count("certifications")), ("Testimony", self.db.count("testimony")), ("Teaching", self.db.count("teaching")), ("Education", self.db.count("education"))]
        self.dashboard_chart.delete("all")
        self.dashboard_chart.update_idletasks()
        width = max(self.dashboard_chart.winfo_width(), 360); height = max(self.dashboard_chart.winfo_height(), 260)
        max_value = max([v for _, v in counts] + [1])
        left, top, bottom = 75, 20, height - 35
        usable = max(120, width - left - 20)
        bar_h = max(22, min(38, (bottom - top) // len(counts) - 8))
        chart_fg = "#f2f3f5" if self.theme_name == "dark" else "#212529"
        for i, (label, value) in enumerate(counts):
            y = top + i * ((bottom-top) / len(counts))
            x2 = left + usable * (value / max_value)
            self.dashboard_chart.create_text(left-8, y+bar_h/2, text=label, anchor="e", fill=chart_fg)
            self.dashboard_chart.create_rectangle(left, y, x2, y+bar_h, fill="#1f4e79", outline="")
            self.dashboard_chart.create_text(x2+6, y+bar_h/2, text=str(value), anchor="w", fill=chart_fg)

    def _profile_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Profile")
        profile = self.db.get_profile()
        self.profile_vars = {}
        fields = [("full_name", "Full Name"), ("preferred_name", "Preferred Name"), ("title", "Professional Title"), ("agency", "Agency / Employer"), ("email", "Email"), ("phone", "Phone")]
        frame = ttk.Frame(tab, padding=20)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(1, weight=1)
        for i, (name, label) in enumerate(fields):
            ttk.Label(frame, text=label + ":").grid(row=i, column=0, sticky="w", pady=5)
            var = tk.StringVar(value=profile.get(name, ""))
            ttk.Entry(frame, textvariable=var, width=70).grid(row=i, column=1, sticky="ew", padx=8, pady=5)
            self.profile_vars[name] = var
        ttk.Label(frame, text="Professional Summary:").grid(row=len(fields), column=0, sticky="nw", pady=5)
        self.profile_summary = tk.Text(frame, height=12, wrap="word")
        self.profile_summary.insert("1.0", profile.get("summary", ""))
        self.profile_summary.grid(row=len(fields), column=1, sticky="nsew", padx=8, pady=5)
        frame.rowconfigure(len(fields), weight=1)
        ttk.Button(frame, text="Save Profile", command=self.save_profile).grid(row=len(fields)+1, column=1, sticky="e", pady=10)

    def save_profile(self):
        data = {k: v.get().strip() for k, v in self.profile_vars.items()}
        data["summary"] = self.profile_summary.get("1.0", "end").strip()
        self.db.save_profile(data)
        self.set_status("Profile saved")
        self.refresh_dashboard()

    def _generate_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Generate CV")
        frame = ttk.Frame(tab, padding=20)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="Create CV", style="Title.TLabel").pack(anchor="w", pady=(0, 8))
        ttk.Label(frame, text="Select the sections to include. Word and PDF outputs are generated independently from the same current SQLite records.").pack(anchor="w", pady=(0, 12))
        self.cv_options = {}
        options = [("summary", "Professional Summary", 1), ("core_training", "Core Training", 1), ("employment", "Work Experience", 1), ("teaching", "Teaching Experience", 1), ("organizations", "Professional Organizations", 1), ("certifications", "Certifications", 1), ("skills", "Skills and Tools", 1), ("education", "Education", 1), ("testimony", "Courtroom Testimony", 1), ("achievements", "Professional Achievements", 1), ("full_training", "Detailed Training Appendix", 0)]
        checks = ttk.LabelFrame(frame, text="CV Sections", padding=12)
        checks.pack(fill="x", pady=8)
        for i, (key, label, default) in enumerate(options):
            var = tk.IntVar(value=default)
            ttk.Checkbutton(checks, text=label, variable=var).grid(row=i // 2, column=i % 2, sticky="w", padx=12, pady=5)
            self.cv_options[key] = var

        actions = ttk.Frame(frame)
        actions.pack(fill="x", pady=16)
        ttk.Button(actions, text="Generate Word CV...", command=lambda: self.generate("docx")).pack(side="left", padx=(0, 8))
        ttk.Button(actions, text="Preview & Save PDF...", command=self.preview_pdf).pack(side="left", padx=(0, 8))
        ttk.Button(actions, text="Generate Word + PDF", command=lambda: self.generate("both")).pack(side="left", padx=(0, 8))
        ttk.Button(actions, text="Export Documents ZIP...", command=self.export_documents_zip).pack(side="left", padx=(0, 8))
        ttk.Button(actions, text="Open Resume Folder", command=self.open_resume_folder).pack(side="left")

    def preview_pdf(self):
        profile = self.db.get_profile()
        base = (profile.get("preferred_name") or profile.get("full_name") or "Forensic").replace(" ", "_") + "_CV.pdf"
        temp_path = make_preview_temp_path()
        try:
            options = {k: bool(v.get()) for k, v in self.cv_options.items()}
            self.set_status("Rendering PDF preview...")
            self.update_idletasks()
            generate_pdf(self.db, temp_path, options, theme_name="Professional")
            default_save = portable_resume_dir() / base
            PdfPreviewWindow(self, temp_path, default_save, on_saved=lambda p: self.set_status(f"PDF saved: {p}"))
            self.set_status("PDF preview ready")
        except Exception as exc:
            messagebox.showerror("PDF Preview", str(exc), parent=self)
            self.set_status("Ready")

    def generate(self, output_type: str = "docx"):
        profile = self.db.get_profile()
        base = (profile.get("preferred_name") or profile.get("full_name") or "Forensic").replace(" ", "_") + "_CV"
        extension = ".pdf" if output_type == "pdf" else ".docx"
        out = filedialog.asksaveasfilename(title="Save CV", defaultextension=extension, initialdir=str(portable_resume_dir()), initialfile=base + extension, filetypes=[("PDF Document", "*.pdf")] if extension == ".pdf" else [("Word Document", "*.docx")])
        if not out:
            return
        try:
            options = {k: bool(v.get()) for k, v in self.cv_options.items()}
            if output_type == "pdf":
                pdf_path = Path(out)
                generate_pdf(self.db, pdf_path, options, theme_name="Professional")
                generated = pdf_path
            else:
                docx_path = Path(out)
                generate_cv(self.db, docx_path, options)
                generated = docx_path
                if output_type == "both":
                    generate_pdf(self.db, docx_path.with_suffix(".pdf"), options, theme_name="Professional")
            self.set_status(f"CV generated: {generated}")
            if messagebox.askyesno("CV Generated", "The CV was created successfully. Open the output folder now?"):
                self.open_resume_folder()
        except Exception as exc:
            messagebox.showerror("Generation Error", str(exc))

    def export_documents_zip(self):
        profile = self.db.get_profile()
        attachments = all_profile_attachments(self.db)
        if not attachments:
            messagebox.showinfo("Export Documents", "No documents are attached to the current profile.", parent=self)
            return
        base = (profile.get("preferred_name") or profile.get("full_name") or "Forensic").replace(" ", "_") + "_Documents.zip"
        out = filedialog.asksaveasfilename(
            title="Export Attached Documents",
            defaultextension=".zip",
            initialdir=str(portable_resume_dir()),
            initialfile=base,
            filetypes=[("ZIP Archive", "*.zip")],
        )
        if not out:
            return
        try:
            count = export_profile_documents(self.db, out)
            self.set_status(f"Exported {count} document(s): {out}")
            messagebox.showinfo("Export Documents", f"Exported {count} attached document(s) to:\n\n{out}", parent=self)
        except Exception as exc:
            messagebox.showerror("Export Documents", str(exc), parent=self)

    def backup_db(self):
        out = filedialog.asksaveasfilename(title="Backup Database", defaultextension=".sqlite3", initialfile="forensic_cv_backup.sqlite3", filetypes=[("SQLite Database", "*.sqlite3"), ("All Files", "*.*")])
        if out:
            self.db.conn.commit()
            shutil.copy2(self.db_path, out)
            self.set_status(f"Database backed up: {out}")

    def restore_db(self):
        src = filedialog.askopenfilename(title="Restore Database", filetypes=[("SQLite Database", "*.sqlite3"), ("All Files", "*.*")])
        if not src:
            return
        if not messagebox.askyesno("Restore Database", "This will replace the current database. Continue?"):
            return
        try:
            check = sqlite3.connect(src)
            check.execute("SELECT name FROM sqlite_master LIMIT 1").fetchone()
            check.close()
            self.db.close()
            shutil.copy2(src, self.db_path)
            self.db = Database(self.db_path)
            messagebox.showinfo("Restore Complete", "Database restored. The application will now restart.")
            self.destroy()
            os.execl(sys.executable, sys.executable, *sys.argv)
        except Exception as exc:
            messagebox.showerror("Restore Error", str(exc))

    def open_resume_folder(self):
        path = str(portable_resume_dir())
        if sys.platform.startswith("win"):
            os.startfile(path)
        else:
            os.system(f'xdg-open "{path}" >/dev/null 2>&1 &')

    def open_data_folder(self):
        path = str(portable_data_dir())
        if sys.platform.startswith("win"):
            os.startfile(path)
        else:
            os.system(f'xdg-open "{path}" >/dev/null 2>&1 &')

    def _on_tab_changed(self, _event=None):
        """Keep the status bar relevant to the currently selected tab."""
        if not hasattr(self, "notebook") or not self.notebook.tabs():
            return
        try:
            selected = self.notebook.select()
            tab_text = self.notebook.tab(selected, "text")
        except tk.TclError:
            return

        if tab_text == "Dashboard":
            profile = self.db.get_profile()
            name = profile.get("profile_name") or profile.get("preferred_name") or profile.get("full_name") or "Current profile"
            self.set_status(f"Dashboard: {name}")
            return
        if tab_text == "Profile":
            profile = self.db.get_profile()
            name = profile.get("profile_name") or profile.get("preferred_name") or profile.get("full_name") or "Current profile"
            self.set_status(f"Profile: {name}")
            return
        if tab_text == "Generate CV":
            self.set_status("Generate CV: select sections, then create Word or preview PDF")
            return

        for table, record_tab in getattr(self, "record_tabs", {}).items():
            if TABLE_CONFIG[table]["label"] == tab_text:
                record_tab.refresh()
                return
        self.set_status(tab_text)

    def set_status(self, text):
        self.status.set(text)

    def on_close(self):
        self.db.close()
        self.destroy()


if __name__ == "__main__":
    App().mainloop()
