"""Real Tk regressions for dialogs opened after selecting an appearance mode."""
import tempfile
import sys
import tkinter as tk
import unittest
from pathlib import Path
from tkinter import ttk
from unittest.mock import patch

from app import App, RecordDialog, ProfileNameDialog, TABLE_CONFIG
from attachments import AttachmentViewer, add_files
from database import Database
from ui_modern import apply_widget_theme


class DialogThemeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.temp.name) / "synthetic.sqlite3")
        self.app = App.__new__(App)
        tk.Tk.__init__(self.app)
        self.app.withdraw()
        self.app.db = self.db
        self.app.theme_name = "dark"
        self.app.set_status = lambda _: None
        self.app._style()
        self.parent = ttk.Frame(self.app)
        self.parent.db = self.db

    def tearDown(self):
        self.app.destroy()
        self.db.close()
        self.temp.cleanup()

    def assert_field(self, widget, dark=True):
        self.assertEqual(widget.cget("background"), "#313338" if dark else "#ffffff")
        self.assertEqual(widget.cget("foreground"), "#f2f3f5" if dark else "#000000")
        self.assertEqual(widget.cget("selectforeground"), "#ffffff")
        self.assertEqual(widget.cget("selectbackground"), "#3d6382" if dark else "#0078d7")

    def test_add_and_edit_dialogs_in_every_record_tab(self):
        for table, config in TABLE_CONFIG.items():
            for initial in (None, {"id": 1, "notes": "Synthetic notes", "hours": 8}):
                with self.subTest(table=table, edit=initial is not None):
                    dialog = RecordDialog(self.parent, table, config, initial)
                    try:
                        self.assertEqual(dialog.cget("background"), "#202225")
                        for widget in dialog.widgets.values():
                            if isinstance(widget, tk.Text):
                                self.assert_field(widget)
                                self.assertEqual(widget.cget("insertbackground"), "#f2f3f5")
                            elif isinstance(widget, ttk.Combobox):
                                self.assertEqual(self.app.style.lookup("TCombobox", "fieldbackground", ("readonly",)), "#313338")
                                popup = widget.tk.call("ttk::combobox::PopdownWindow", widget)
                                self.assertEqual(widget.tk.call(str(popup) + ".f.l", "cget", "-background"), "#313338")
                        if dialog.attachment_picker is not None:
                            self.assert_field(dialog.attachment_picker.listbox)
                    finally:
                        dialog.destroy()

    def test_nested_dialog_inherits_application_theme(self):
        outer = tk.Toplevel(self.app)
        parent = ttk.Frame(outer)
        parent.db = self.db
        dialog = RecordDialog(parent, "training", TABLE_CONFIG["training"])
        self.assert_field(dialog.widgets["notes"])
        self.assert_field(dialog.attachment_picker.listbox)
        profile = ProfileNameDialog(outer, "Synthetic profile")
        self.assertEqual(profile.cget("background"), "#202225")

    def test_switch_modes_updates_open_dialog_and_later_dialogs(self):
        dialog = RecordDialog(self.parent, "training", TABLE_CONFIG["training"])
        dialog.widgets["notes"].insert("1.0", "Keep these notes")
        for mode in ("light", "dark", "light"):
            with patch("app.save_theme_preference"):
                self.app.set_theme(mode)
            dark = mode == "dark"
            self.assert_field(dialog.widgets["notes"], dark)
            self.assert_field(dialog.attachment_picker.listbox, dark)
            self.assertEqual(dialog.cget("background"), "#202225" if dark else "#f0f0f0")
            self.assertEqual(dialog.widgets["notes"].get("1.0", "end").strip(), "Keep these notes")
            later = RecordDialog(self.parent, "training", TABLE_CONFIG["training"])
            self.assert_field(later.widgets["notes"], dark)
            self.assert_field(later.attachment_picker.listbox, dark)
            later.destroy()

    def test_attachment_viewer_list_and_canvas_follow_theme(self):
        record = self.db.insert_row("training", {"course_name": "Synthetic"})
        source = Path(self.temp.name) / "synthetic.txt"
        source.write_text("Synthetic document")
        add_files(self.db, "training", record, [source])
        viewer = AttachmentViewer(self.parent, self.db, "training", record)
        self.assert_field(viewer.listbox)
        self.assertEqual(viewer.canvas.cget("background"), "#2b2d31")
        self.assertEqual(viewer.listbox.curselection(), (0,))
        self.app.theme_name = "light"
        apply_widget_theme(viewer)
        self.assert_field(viewer.listbox, dark=False)
        self.assertEqual(viewer.listbox.curselection(), (0,))

    def test_combobox_popup_changes_with_open_dialog(self):
        dialog = RecordDialog(self.parent, "testimony", TABLE_CONFIG["testimony"])
        combo = next(w for w in dialog.widgets.values() if isinstance(w, ttk.Combobox))
        popup = str(combo.tk.call("ttk::combobox::PopdownWindow", combo)) + ".f.l"
        for mode, expected in (("light", "#ffffff"), ("dark", "#313338")):
            self.app.theme_name = mode
            apply_widget_theme(self.app)
            self.assertEqual(combo.tk.call(popup, "cget", "-background"), expected)

    def test_save_preserves_edited_values_and_attachment_selection(self):
        record = self.db.insert_row("training", {"course_name": "Synthetic course", "notes": "Original", "hours": 8})
        source = Path(self.temp.name) / "synthetic.txt"
        source.write_text("Synthetic document")
        attachment = add_files(self.db, "training", record, [source])[0]
        dialog = RecordDialog(self.parent, "training", TABLE_CONFIG["training"], self.db.get_row("training", record))
        dialog.attachment_picker.listbox.selection_set(0)
        apply_widget_theme(dialog)
        self.assertEqual(dialog.attachment_picker.listbox.curselection(), (0,))
        dialog.widgets["notes"].delete("1.0", "end")
        dialog.widgets["notes"].insert("1.0", "Edited")
        dialog.save()
        self.assertEqual(dialog.result["course_name"], "Synthetic course")
        self.assertEqual(dialog.result["hours"], 8.0)
        self.assertEqual(dialog.result["notes"], "Edited")
        self.assertIsNotNone(self.db.conn.execute("SELECT id FROM attachments WHERE id=?", (attachment,)).fetchone())

    def test_dark_interaction_states_have_readable_text(self):
        def luminance(color):
            components = [value / 65535 for value in self.app.winfo_rgb(color)]
            linear = [value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4 for value in components]
            return sum(value * weight for value, weight in zip(linear, (0.2126, 0.7152, 0.0722)))

        for name in ("Treeview.Heading", "Document.Treeview.Heading", "TButton",
                     "TCheckbutton", "TRadiobutton", "TCombobox", "TNotebook.Tab"):
            for state in ((), ("active",), ("pressed",), ("active", "pressed")):
                with self.subTest(style=name, state=state):
                    bg = luminance(self.app.style.lookup(name, "background", state))
                    fg = luminance(self.app.style.lookup(name, "foreground", state))
                    contrast = (max(bg, fg) + 0.05) / (min(bg, fg) + 0.05)
                    self.assertGreaterEqual(contrast, 4.5)
                    self.assertLess(bg, 0.15, "Dark-mode interaction backgrounds must stay dark")

    def test_light_theme_state_colors_are_restored_after_dark_mode(self):
        style = self.app.style
        light = "vista" if sys.platform.startswith("win") and "vista" in style.theme_names() else "clam"
        styles = ("Treeview.Heading", "Document.Treeview.Heading", "TCheckbutton", "TCombobox")
        states = ((), ("active",), ("pressed",))
        style.theme_use(light)
        expected = {(name, state, option): style.lookup(name, option, state)
                    for name in styles for state in states for option in ("background", "foreground")}
        for _ in range(2):
            with patch("app.save_theme_preference"):
                self.app.set_theme("dark")
                self.app.set_theme("light")
            self.assertEqual(style.theme_use(), light)
            for (name, state, option), value in expected.items():
                with self.subTest(style=name, state=state, option=option):
                    self.assertEqual(style.lookup(name, option, state), value)
            self.assertEqual(int(style.lookup("Document.Treeview", "rowheight")), 34)

    def test_disabled_controls_and_compact_rows_survive_theme_changes(self):
        for mode in ("light", "dark", "light", "dark"):
            with patch("app.save_theme_preference"):
                self.app.set_theme(mode)
            self.assertEqual(int(self.app.style.lookup("Document.Treeview", "rowheight")), 34)
            if mode == "dark":
                for name in ("TButton", "TEntry", "TCombobox", "Treeview.Heading"):
                    self.assertEqual(self.app.style.lookup(name, "foreground", ("disabled",)), "#b5bac1")

    def test_release_metadata_matches_application_version(self):
        from app_config import APP_VERSION
        from version import __version__

        root = Path(__file__).resolve().parents[1]
        self.assertEqual(APP_VERSION, __version__)
        self.assertIn(f'MyAppVersion "{__version__}"', (root / "installer_version.iss").read_text())
        metadata = (root / "version_info.txt").read_text()
        quad = ", ".join(__version__.split(".") + ["0"])
        self.assertIn(f"filevers=({quad})", metadata)
        self.assertIn(f"prodvers=({quad})", metadata)


if __name__ == "__main__":
    unittest.main()
