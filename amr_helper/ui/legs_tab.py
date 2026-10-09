from __future__ import annotations

from collections.abc import Callable
import tkinter as tk
from tkinter import ttk

from amr_helper.defaults import MAX_LEGS
from amr_helper.models import Leg
from amr_helper.ui.scroll import scrollable_frame
from amr_helper.ui.searchable import SearchableDropdown


class LegsTab(ttk.Frame):
    def __init__(
        self,
        parent: tk.Widget,
        lz_names: list[str],
        on_change: Callable[[], None] | None = None,
    ):
        super().__init__(parent, padding=8)
        self.lz_names = lz_names
        self.on_change = on_change
        buttons = ttk.Frame(self)
        buttons.pack(fill=tk.X, pady=(0, 8))
        ttk.Button(buttons, text="Add leg", command=self.add_leg).pack(side=tk.LEFT)
        ttk.Button(buttons, text="Remove last", command=self.remove_last).pack(
            side=tk.LEFT, padx=8
        )
        ttk.Label(self, text="Set departure and arrival times on the Timeline tab.").pack(
            anchor=tk.W, pady=(0, 6)
        )
        canvas, inner = scrollable_frame(self)
        canvas.pack(fill=tk.BOTH, expand=True)
        self.inner = inner
        self.rows: list[LegRow] = []
        self.add_leg()

    def add_leg(self) -> None:
        if len(self.rows) >= MAX_LEGS:
            return
        start = self.rows[-1].end.get() if self.rows else ""
        row = LegRow(self.inner, len(self.rows) + 1, self.lz_names, start)
        row.pack(fill=tk.X, pady=6)
        self.rows.append(row)
        self._notify()

    def remove_last(self) -> None:
        if len(self.rows) <= 1:
            return
        row = self.rows.pop()
        row.destroy()
        self._notify()

    def _notify(self) -> None:
        if self.on_change:
            self.on_change()

    def collect_legs(self) -> list[Leg]:
        return [row.to_leg() for row in self.rows]

    def set_lz_names(self, names: list[str]) -> None:
        self.lz_names = list(names)
        for row in self.rows:
            row.start.set_options(self.lz_names)
            row.end.set_options(self.lz_names)

    def refresh_labels(self) -> None:
        for index, row in enumerate(self.rows, start=1):
            row.set_index(index)


class LegRow(ttk.LabelFrame):
    def __init__(
        self, parent: tk.Widget, index: int, lz_names: list[str], start: str
    ):
        super().__init__(parent, text=f"Leg {index}", padding=8)
        self.start = SearchableDropdown(self, lz_names)
        self.end = SearchableDropdown(self, lz_names)
        if start:
            self.start.set(start)
        ttk.Label(self, text="Start LZ").grid(row=0, column=0, sticky=tk.W)
        self.start.grid(row=0, column=1, sticky=tk.EW, padx=4)
        ttk.Label(self, text="End LZ").grid(row=0, column=2, sticky=tk.W, padx=(12, 0))
        self.end.grid(row=0, column=3, sticky=tk.EW, padx=4)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(3, weight=1)

    def set_index(self, index: int) -> None:
        self.configure(text=f"Leg {index}")

    def to_leg(self) -> Leg:
        return Leg(start_lz=self.start.get(), end_lz=self.end.get())
