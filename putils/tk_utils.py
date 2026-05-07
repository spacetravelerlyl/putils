from __future__ import annotations

import tkinter as tk
from tkinter import ttk


def copy_treeview_selection_to_clipboard(tree: ttk.Treeview, widget: tk.Widget) -> None:
    selection = tree.selection()
    if not selection:
        return
    columns = tree["columns"]
    header = "\t".join(tree.heading(col, option="text") for col in columns)
    lines = [header]
    for item_id in selection:
        values = tree.item(item_id, "values")
        lines.append("\t".join(str(v) for v in values))
    widget.clipboard_clear()
    widget.clipboard_append("\n".join(lines))


def open_in_file_manager(path: str) -> None:
    import os
    import platform
    import subprocess

    resolved = os.path.abspath(path)
    if not os.path.exists(resolved):
        return
    system = platform.system()
    if system == "Windows":
        subprocess.Popen(["explorer", "/select,", resolved], creationflags=subprocess.DETACHED_PROCESS)
    elif system == "Darwin":
        subprocess.Popen(["open", "-R", resolved])
    else:
        subprocess.Popen(["xdg-open", resolved])
