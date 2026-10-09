from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

from amr_helper import config


def prompt_for_sources(parent: tk.Misc) -> bool:
    """Ask for roster CSV and LZ KMZ if not configured. Returns False if cancelled."""
    if not _ensure_csv(parent):
        return False
    if not _ensure_kmz(parent):
        return False
    return True


def choose_csv(parent: tk.Misc) -> Path | None:
    path = filedialog.askopenfilename(
        parent=parent,
        title="Select roster CSV (manifest personnel)",
        filetypes=[("CSV", "*.csv"), ("All files", "*.*")],
    )
    if not path:
        return None
    chosen = Path(path)
    config.set_csv_path(chosen)
    return chosen


def choose_kmz(parent: tk.Misc) -> Path | None:
    path = filedialog.askopenfilename(
        parent=parent,
        title="Select LZ KMZ",
        filetypes=[("KMZ", "*.kmz"), ("All files", "*.*")],
    )
    if not path:
        return None
    chosen = Path(path)
    config.set_kmz_path(chosen)
    return chosen


def _ensure_csv(parent: tk.Misc) -> bool:
    if config.get_csv_path() is not None:
        return True
    messagebox.showinfo(
        "First-time setup",
        "Select the CSV file with manifest personnel "
        "(Rank, Last, DODID (L4), Squad).",
        parent=parent,
    )
    if choose_csv(parent) is None:
        messagebox.showerror(
            "Setup required",
            "A roster CSV is required to run AMR Helper.",
            parent=parent,
        )
        return False
    return True


def _ensure_kmz(parent: tk.Misc) -> bool:
    if config.get_kmz_path() is not None:
        return True
    messagebox.showinfo(
        "First-time setup",
        "Select the KMZ file that contains landing-zone placemarks.",
        parent=parent,
    )
    if choose_kmz(parent) is None:
        messagebox.showerror(
            "Setup required",
            "An LZ KMZ is required to run AMR Helper.",
            parent=parent,
        )
        return False
    return True

