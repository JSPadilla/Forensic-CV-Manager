from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def open_path(path: str | Path) -> None:
    """Open a file or folder with the operating system's default handler."""
    target = str(Path(path).resolve())
    if sys.platform.startswith("win"):
        os.startfile(target)
    elif sys.platform == "darwin":
        subprocess.Popen(["open", target])
    else:
        subprocess.Popen(["xdg-open", target])


def platform_name() -> str:
    if sys.platform.startswith("win"):
        return "Windows"
    if sys.platform == "darwin":
        return "macOS"
    return "Linux"
