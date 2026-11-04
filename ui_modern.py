from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import pymupdf
from PIL import Image, ImageTk


def apply_widget_theme(widget, theme_name: str | None = None):
    """Theme native widgets, including dialogs created after a theme switch.

    ttk controls inherit the application's styles. Native Tk controls and
    combobox popups need their colors set explicitly.
    """
    root = widget
    while root.master is not None:
        root = root.master
    if theme_name is None:
        theme_name = getattr(root, "theme_name", "light")
    dark = theme_name == "dark"
    background = "#202225" if dark else "#f0f0f0"
    field = "#313338" if dark else "#ffffff"
    foreground = "#f2f3f5" if dark else "#000000"
    selected = "#3d6382" if dark else "#0078d7"
    canvas = "#2b2d31" if dark else "#ffffff"

    def walk(current):
        if isinstance(current, (tk.Tk, tk.Toplevel)):
            current.configure(background=background)
        elif isinstance(current, tk.Text):
            current.configure(
                background=field, foreground=foreground,
                insertbackground=foreground, selectbackground=selected,
                selectforeground="#ffffff", highlightbackground=background,
            )
        elif isinstance(current, tk.Listbox):
            current.configure(
                background=field, foreground=foreground,
                selectbackground=selected, selectforeground="#ffffff",
                highlightbackground=background,
            )
        elif isinstance(current, tk.Canvas):
            current.configure(background=canvas)
        elif isinstance(current, ttk.Combobox):
            # The dropdown list is a Tcl-created Listbox outside winfo_children.
            try:
                popup = current.tk.call("ttk::combobox::PopdownWindow", current)
                current.tk.call(
                    str(popup) + ".f.l", "configure",
                    "-background", field, "-foreground", foreground,
                    "-selectbackground", selected, "-selectforeground", "#ffffff",
                )
            except tk.TclError:
                pass  # Some native platform themes do not expose a Tk listbox.
        for child in current.winfo_children():
            walk(child)

    walk(widget)


def resource_path(relative: str) -> Path:
    import sys
    base = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent))
    return base / relative


class IconStore:
    def __init__(self, master):
        self.master = master
        self._cache = {}

    def get(self, name: str, size: int = 20):
        key = (name, size)
        if key in self._cache:
            return self._cache[key]
        path = resource_path(f"assets/{name}.png")
        if not path.exists():
            return None
        im = Image.open(path).convert('RGBA').resize((size, size), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(im, master=self.master)
        self._cache[key] = photo
        return photo


class SplashScreen(tk.Toplevel):
    def __init__(self, parent, version: str):
        super().__init__(parent)
        self.overrideredirect(True)
        self.configure(bg='#f5f8fb')
        self.attributes('-topmost', True)
        self._img = None
        img_path = resource_path('assets/splash.png')
        if img_path.exists():
            im = Image.open(img_path).convert('RGB')
            self._img = ImageTk.PhotoImage(im, master=self)
            tk.Label(self, image=self._img, bd=0).pack()
        else:
            tk.Label(self, text='Forensic CV Manager', font=('Segoe UI', 24, 'bold'), bg='#f5f8fb').pack(padx=90, pady=(70,20))
        self.status_var = tk.StringVar(value='Starting application…')
        tk.Label(self, textvariable=self.status_var, bg='#f5f8fb', fg='#495057', font=('Segoe UI', 10)).pack(fill='x', padx=18, pady=(0, 8))
        self.progress = ttk.Progressbar(self, mode='determinate', maximum=100, value=8)
        self.progress.pack(fill='x', padx=18, pady=(0, 12))
        self.version_label = tk.Label(self, text=f'Version {version}', bg='#f5f8fb', fg='#6c757d', font=('Segoe UI', 9))
        self.version_label.pack(anchor='e', padx=18, pady=(0, 10))
        self.update_idletasks()
        w, h = self.winfo_reqwidth(), self.winfo_reqheight()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f'{w}x{h}+{(sw-w)//2}+{(sh-h)//2}')

    def step(self, text: str, value: int):
        self.status_var.set(text)
        self.progress['value'] = value
        self.update_idletasks()


class PdfPreviewWindow(tk.Toplevel):
    def __init__(self, parent, pdf_path: Path, default_save_path: Path, on_saved=None):
        super().__init__(parent)
        self.title('PDF Preview')
        self.geometry('1000x760')
        self.minsize(760, 560)
        self.transient(parent)
        self.pdf_path = Path(pdf_path)
        self.default_save_path = Path(default_save_path)
        self.on_saved = on_saved
        self.doc = pymupdf.open(str(self.pdf_path))
        self.page_index = 0
        self.zoom = 1.15
        self._photo = None

        toolbar = ttk.Frame(self, padding=(10,8))
        toolbar.pack(fill='x')
        ttk.Button(toolbar, text='◀ Previous', command=self.prev_page).pack(side='left', padx=(0,4))
        ttk.Button(toolbar, text='Next ▶', command=self.next_page).pack(side='left', padx=4)
        self.page_var = tk.StringVar()
        ttk.Label(toolbar, textvariable=self.page_var).pack(side='left', padx=12)
        ttk.Separator(toolbar, orient='vertical').pack(side='left', fill='y', padx=8)
        ttk.Button(toolbar, text='Zoom −', command=self.zoom_out).pack(side='left', padx=3)
        ttk.Button(toolbar, text='Zoom +', command=self.zoom_in).pack(side='left', padx=3)
        ttk.Button(toolbar, text='Fit Width', command=self.fit_width).pack(side='left', padx=3)
        ttk.Button(toolbar, text='Save PDF…', command=self.save_pdf).pack(side='right', padx=3)

        body = ttk.Frame(self)
        body.pack(fill='both', expand=True)
        self.canvas = tk.Canvas(body, highlightthickness=0, background='#7a7d80')
        v = ttk.Scrollbar(body, orient='vertical', command=self.canvas.yview)
        h = ttk.Scrollbar(body, orient='horizontal', command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=v.set, xscrollcommand=h.set)
        self.canvas.grid(row=0,column=0,sticky='nsew')
        v.grid(row=0,column=1,sticky='ns')
        h.grid(row=1,column=0,sticky='ew')
        body.rowconfigure(0,weight=1); body.columnconfigure(0,weight=1)
        self.canvas.bind('<Configure>', lambda e: self._render())
        self.protocol('WM_DELETE_WINDOW', self.close)
        apply_widget_theme(self)
        self.after(40, self._render)

    def _render(self):
        if not self.doc.page_count:
            return
        page = self.doc.load_page(self.page_index)
        matrix = pymupdf.Matrix(self.zoom, self.zoom)
        pix = page.get_pixmap(matrix=matrix, alpha=False)
        mode = 'RGB'
        im = Image.frombytes(mode, (pix.width, pix.height), pix.samples)
        self._photo = ImageTk.PhotoImage(im, master=self)
        self.canvas.delete('all')
        self.canvas.create_image(18,18,anchor='nw',image=self._photo)
        self.canvas.configure(scrollregion=(0,0,pix.width+36,pix.height+36))
        self.page_var.set(f'Page {self.page_index+1} of {self.doc.page_count}   •   {int(self.zoom*100)}%')

    def prev_page(self):
        if self.page_index > 0:
            self.page_index -= 1; self.canvas.xview_moveto(0); self.canvas.yview_moveto(0); self._render()

    def next_page(self):
        if self.page_index + 1 < self.doc.page_count:
            self.page_index += 1; self.canvas.xview_moveto(0); self.canvas.yview_moveto(0); self._render()

    def zoom_in(self):
        self.zoom = min(3.0, self.zoom + .15); self._render()

    def zoom_out(self):
        self.zoom = max(.45, self.zoom - .15); self._render()

    def fit_width(self):
        page = self.doc.load_page(self.page_index)
        available = max(300, self.canvas.winfo_width() - 50)
        self.zoom = max(.45, min(2.5, available / page.rect.width))
        self._render()

    def save_pdf(self):
        target = filedialog.asksaveasfilename(
            parent=self, title='Save PDF', defaultextension='.pdf',
            initialdir=str(self.default_save_path.parent), initialfile=self.default_save_path.name,
            filetypes=[('PDF Document','*.pdf')]
        )
        if not target:
            return
        try:
            shutil.copy2(self.pdf_path, target)
            if self.on_saved:
                self.on_saved(Path(target))
            messagebox.showinfo('PDF Saved', f'PDF saved successfully:\n\n{target}', parent=self)
        except Exception as exc:
            messagebox.showerror('Save PDF', str(exc), parent=self)

    def close(self):
        try: self.doc.close()
        except Exception: pass
        try:
            shutil.rmtree(self.pdf_path.parent, ignore_errors=True)
        except Exception:
            pass
        self.destroy()


def make_preview_temp_path() -> Path:
    root = Path(tempfile.mkdtemp(prefix='fcv_preview_'))
    return root / 'preview.pdf'
