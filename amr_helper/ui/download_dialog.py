from __future__ import annotations

import time
import tkinter as tk
from tkinter import ttk


class LzDownloadDialog(tk.Toplevel):
    """Modal progress UI while LZ satellite chips download."""

    def __init__(self, parent: tk.Misc, total: int):
        super().__init__(parent)
        self.title("Downloading LZ images")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", lambda: None)
        self.total = max(total, 1)
        self.started = time.monotonic()
        self._build()
        self.update_idletasks()
        self._center_on(parent)

    def _build(self) -> None:
        frame = ttk.Frame(self, padding=16)
        frame.pack(fill=tk.BOTH, expand=True)
        ttk.Label(
            frame,
            text=(
                "Downloading landing-zone satellite images.\n"
                "The first start takes longer than later launches."
            ),
            justify=tk.LEFT,
        ).pack(anchor=tk.W)
        self.status = ttk.Label(frame, text="Starting…")
        self.status.pack(anchor=tk.W, pady=(12, 4))
        self.bar = ttk.Progressbar(frame, length=360, maximum=self.total, mode="determinate")
        self.bar.pack(fill=tk.X, pady=4)
        self.eta = ttk.Label(frame, text="")
        self.eta.pack(anchor=tk.W, pady=(4, 0))

    def set_progress(self, done: int, total: int, name: str) -> None:
        self.bar.configure(maximum=max(total, 1), value=done)
        self.status.configure(text=f"{done} of {total}: {name}")
        elapsed = max(time.monotonic() - self.started, 0.001)
        if done <= 0:
            self.eta.configure(text="Estimating time remaining…")
            return
        rate = elapsed / done
        remaining = max(total - done, 0) * rate
        self.eta.configure(text=f"About {_format_seconds(remaining)} remaining")

    def _center_on(self, parent: tk.Misc) -> None:
        self.update_idletasks()
        try:
            px = parent.winfo_rootx()
            py = parent.winfo_rooty()
            pw = parent.winfo_width()
            ph = parent.winfo_height()
        except tk.TclError:
            px = py = 0
            pw = ph = 800
        width = self.winfo_width()
        height = self.winfo_height()
        x = px + max((pw - width) // 2, 0)
        y = py + max((ph - height) // 2, 0)
        self.geometry(f"+{x}+{y}")


def _format_seconds(seconds: float) -> str:
    total = max(int(seconds + 0.5), 0)
    minutes, secs = divmod(total, 60)
    if minutes <= 0:
        return f"{secs}s"
    return f"{minutes}m {secs:02d}s"

