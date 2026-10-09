from __future__ import annotations

import tkinter as tk
from tkinter import ttk


def matching_names(options: list[str], query: str) -> list[str]:
    needle = " ".join(query.strip().lower().split())
    if not needle:
        return list(options)
    hits = [name for name in options if needle in name.lower()]
    return sorted(hits, key=lambda name: _match_rank(name, needle))


def _match_rank(name: str, needle: str) -> tuple[int, str]:
    lower = name.lower()
    bare = lower.removeprefix("lz ").strip()
    if lower.startswith(needle) or bare.startswith(needle):
        return (0, name)
    return (1, name)


class SearchableDropdown(ttk.Frame):
    def __init__(self, parent: tk.Widget, options: list[str], width: int = 28):
        super().__init__(parent)
        self.options = list(options)
        self.var = tk.StringVar()
        self._open = False
        self._build(width)
        self._bind()

    def get(self) -> str:
        return self.var.get().strip()

    def set(self, value: str) -> None:
        self.var.set(value)
        self._hide()

    def set_options(self, options: list[str]) -> None:
        self.options = list(options)

    def _build(self, width: int) -> None:
        row = ttk.Frame(self)
        row.pack(fill=tk.X)
        self.entry = ttk.Entry(row, textvariable=self.var, width=width)
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.button = ttk.Button(row, text="v", width=2, command=self._toggle)
        self.button.pack(side=tk.LEFT)
        self.listbox = tk.Listbox(self, height=8, exportselection=False)

    def _bind(self) -> None:
        self.entry.bind("<KeyRelease>", self._on_key)
        self.entry.bind("<Down>", self._move_selection)
        self.entry.bind("<Up>", self._move_selection)
        self.entry.bind("<Return>", self._apply_selection)
        self.entry.bind("<Escape>", lambda _e: self._hide())
        self.entry.bind("<FocusOut>", self._schedule_hide)
        self.listbox.bind("<ButtonRelease-1>", self._apply_selection)
        self.listbox.bind("<Return>", self._apply_selection)
        self.listbox.bind("<FocusOut>", self._schedule_hide)

    def _on_key(self, event: tk.Event) -> None:
        if event.keysym in {"Up", "Down", "Return", "Escape", "Tab"}:
            return
        self._show(matching_names(self.options, self.var.get()))

    def _toggle(self) -> None:
        if self._open:
            self._hide()
            return
        self.entry.focus_set()
        self._show(list(self.options))

    def _show(self, matches: list[str]) -> None:
        self.listbox.delete(0, tk.END)
        for name in matches:
            self.listbox.insert(tk.END, name)
        self.listbox.configure(height=min(8, max(1, len(matches))))
        if not self._open:
            self.listbox.pack(fill=tk.X, pady=(2, 0))
            self._open = True
        self.listbox.selection_clear(0, tk.END)
        if matches:
            self.listbox.selection_set(0)
            self.listbox.see(0)

    def _hide(self) -> None:
        if not self._open:
            return
        self.listbox.pack_forget()
        self._open = False

    def _schedule_hide(self, _event: tk.Event) -> None:
        self.after(150, self._hide_if_focus_left)

    def _hide_if_focus_left(self) -> None:
        focused = self.focus_get()
        if focused in (self.entry, self.listbox, self.button):
            return
        self._hide()

    def _move_selection(self, event: tk.Event) -> str:
        already_open = self._open
        if not already_open:
            self._show(matching_names(self.options, self.var.get()))
        size = self.listbox.size()
        if size == 0:
            return "break"
        current = self.listbox.curselection()
        index = int(current[0]) if current else 0
        if already_open:
            index = index + 1 if event.keysym == "Down" else index - 1
        index = max(0, min(size - 1, index))
        self.listbox.selection_clear(0, tk.END)
        self.listbox.selection_set(index)
        self.listbox.see(index)
        return "break"

    def _apply_selection(self, _event: tk.Event | None = None) -> str:
        selection = self.listbox.curselection()
        if self._open and selection:
            self.var.set(self.listbox.get(selection[0]))
            self.entry.icursor(tk.END)
        self._hide()
        return "break"
