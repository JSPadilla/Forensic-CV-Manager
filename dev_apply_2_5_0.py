from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise SystemExit(f"Patch target not found: {label}")
    if text.count(old) != 1:
        raise SystemExit(f"Patch target is not unique: {label} ({text.count(old)} matches)")
    return text.replace(old, new, 1)


path = Path("app.py")
text = path.read_text(encoding="utf-8")

text = replace_once(
    text,
    "from ui_modern import SplashScreen, PdfPreviewWindow, make_preview_temp_path, resource_path\n",
    "from ui_modern import SplashScreen, PdfPreviewWindow, make_preview_temp_path, resource_path\n"
    "from attachments import (\n"
    "    ATTACHMENT_TABLES, AttachmentPicker, AttachmentViewer,\n"
    "    all_profile_attachments, ensure_attachment_schema, export_profile_documents,\n"
    "    get_attachment, list_attachments, thumbnail_photo,\n"
    ")\n",
    "attachment imports",
)

text = replace_once(
    text,
    "        self.vars: dict[str, Any] = {}\n        self.widgets: dict[str, Any] = {}\n        self.columnconfigure(1, weight=1)\n",
    "        self.vars: dict[str, Any] = {}\n        self.widgets: dict[str, Any] = {}\n"
    "        self.attachment_picker = None\n        self.columnconfigure(1, weight=1)\n",
    "record dialog attachment state",
)

text = replace_once(
    text,
    "            self.widgets[name] = widget\n            row += 1\n        buttons = ttk.Frame(self)\n",
    "            self.widgets[name] = widget\n            row += 1\n"
    "        if table in ATTACHMENT_TABLES:\n"
    "            record_id = int(initial['id']) if initial and initial.get('id') else None\n"
    "            self.attachment_picker = AttachmentPicker(self, parent.db, table, record_id)\n"
    "            self.attachment_picker.grid(row=row, column=0, columnspan=2, sticky='nsew', padx=8, pady=8)\n"
    "            self.rowconfigure(row, weight=1)\n"
    "            row += 1\n"
    "        buttons = ttk.Frame(self)\n",
    "record dialog attachment picker",
)

old_tree = '''        cols = self.config_data["display"]
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
        self.tree.bind("<Double-1>", lambda e: self.edit())
        self.refresh()
'''
new_tree = '''        cols = self.config_data["display"]
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
'''
text = replace_once(text, old_tree, new_tree, "record tree attachment column")

text = replace_once(
    text,
    "    def _heading_text(self, column: str) -> str:\n",
    '''    def _document_click(self, event):
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
''',
    "document click handlers",
)

old_refresh = '''        for row in rows:
            values = []
            for col in self.config_data["display"]:
                value = row.get(col, "")
                if col == "core_training":
                    value = "Yes" if value else "No"
                values.append("" if value is None else value)
            iid = str(row["id"])
            self.tree.insert("", "end", iid=iid, values=values)
            if iid in selected:
                self.tree.selection_add(iid)
        self.status_callback(f"{self.config_data['label']}: {len(self.tree.get_children())} record(s)")
'''
new_refresh = '''        self._thumbnail_refs.clear()
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
'''
text = replace_once(text, old_refresh, new_refresh, "record refresh thumbnails")

text = replace_once(
    text,
    '''        if dlg.result is not None:
            self.db.insert_row(self.table, dlg.result)
            self.refresh()
''',
    '''        if dlg.result is not None:
            row_id = self.db.insert_row(self.table, dlg.result)
            if dlg.attachment_picker is not None:
                dlg.attachment_picker.commit(row_id)
            self.refresh()
''',
    "add record attachments",
)

text = replace_once(
    text,
    '''        if dlg.result is not None:
            self.db.update_row(self.table, row_id, dlg.result)
            self.refresh()
''',
    '''        if dlg.result is not None:
            self.db.update_row(self.table, row_id, dlg.result)
            if dlg.attachment_picker is not None:
                dlg.attachment_picker.commit(row_id)
            self.refresh()
''',
    "edit record attachments",
)

text = replace_once(
    text,
    "        self.db = Database(self.db_path)\n        seed(self.db)\n",
    "        self.db = Database(self.db_path)\n        ensure_attachment_schema(self.db)\n        seed(self.db)\n",
    "attachment schema initialization",
)

text = replace_once(
    text,
    '''        ttk.Button(actions, text="Generate Word + PDF", command=lambda: self.generate("both")).pack(side="left", padx=(0, 8))
        ttk.Button(actions, text="Open Resume Folder", command=self.open_resume_folder).pack(side="left")
''',
    '''        ttk.Button(actions, text="Generate Word + PDF", command=lambda: self.generate("both")).pack(side="left", padx=(0, 8))
        ttk.Button(actions, text="Export Documents ZIP...", command=self.export_documents_zip).pack(side="left", padx=(0, 8))
        ttk.Button(actions, text="Open Resume Folder", command=self.open_resume_folder).pack(side="left")
''',
    "generate tab document export button",
)

text = replace_once(
    text,
    "    def backup_db(self):\n",
    '''    def export_documents_zip(self):
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
''',
    "document zip export method",
)

path.write_text(text, encoding="utf-8")
Path("version.py").write_text('__version__ = "2.5.0"\n', encoding="utf-8")
print("Applied v2.5.0 attachment integration patch.")
