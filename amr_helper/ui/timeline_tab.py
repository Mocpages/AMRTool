from __future__ import annotations

from collections.abc import Callable
from datetime import date
import tkinter as tk
from tkinter import messagebox, ttk

from amr_helper.dates import format_date, format_local_zulu, parse_date
from amr_helper.defaults import MAX_TIMELINE_ROWS
from amr_helper.models import Mission, TimelineEvent
from amr_helper.timeline import auto_local_time, default_timeline
from amr_helper.ui.scroll import scrollable_frame

LOCATION_WIDTH = 18


class TimelineTab(ttk.Frame):
    def __init__(
        self,
        parent: tk.Widget,
        lz_mgrs: dict[str, str],
        get_context: Callable[[], Mission],
    ):
        super().__init__(parent, padding=8)
        self.lz_mgrs = lz_mgrs
        self.get_context = get_context
        self.dirty = False
        self.rows: list[TimelineRow] = []
        self._build_toolbar()
        ttk.Label(
            self,
            text="Enter times in local (Arizona MST). Shown and written as HHMML/HHMMZ.",
        ).pack(anchor=tk.W, pady=(0, 6))
        canvas, inner = scrollable_frame(self)
        canvas.pack(fill=tk.BOTH, expand=True)
        self.inner = inner

    def sync_from_legs(self) -> None:
        if self.dirty:
            return
        self._replace(default_timeline(self.get_context(), self.lz_mgrs))

    def set_lz_mgrs(self, lz_mgrs: dict[str, str]) -> None:
        self.lz_mgrs = lz_mgrs
        if not self.dirty:
            self._replace(default_timeline(self.get_context(), self.lz_mgrs))

    def collect(self) -> list[TimelineEvent]:
        return [row.to_event() for row in self.rows]

    def _build_toolbar(self) -> None:
        bar = ttk.Frame(self)
        bar.pack(fill=tk.X, pady=(0, 4))
        ttk.Button(bar, text="Add event", command=self._add_blank).pack(side=tk.LEFT)
        ttk.Button(bar, text="Reset from legs", command=self._reset).pack(
            side=tk.LEFT, padx=8
        )

    def _add_blank(self) -> None:
        context = self.get_context()
        self._add_row(
            TimelineEvent(
                event_date=context.mission_date,
                local_time="",
                event="",
                location="",
            )
        )
        self.dirty = True

    def _delete_row(self, row: TimelineRow) -> None:
        if row not in self.rows:
            return
        self.rows.remove(row)
        row.destroy()
        self.dirty = True

    def _auto_row(self, row: TimelineRow) -> None:
        index = self.rows.index(row)
        if index == 0:
            messagebox.showerror(
                "Auto time", "Need a previous event to estimate time.", parent=self
            )
            return
        prev = self.rows[index - 1]
        try:
            hhmm = auto_local_time(
                prev.time_var.get(),
                prev.loc_var.get(),
                row.loc_var.get(),
                self.lz_mgrs,
            )
        except ValueError as exc:
            messagebox.showerror("Auto time", str(exc), parent=self)
            return
        row.time_var.set(hhmm)
        self.dirty = True

    def _reset(self) -> None:
        self.dirty = False
        self._replace(default_timeline(self.get_context(), self.lz_mgrs))

    def _replace(self, events: list[TimelineEvent]) -> None:
        for row in self.rows:
            row.destroy()
        self.rows = []
        for event in events[:MAX_TIMELINE_ROWS]:
            self._add_row(event)

    def _add_row(self, event: TimelineEvent) -> None:
        if len(self.rows) >= MAX_TIMELINE_ROWS:
            return
        row = TimelineRow(
            self.inner,
            event,
            self._mark_dirty,
            self._move,
            self._delete_row,
            self._auto_row,
        )
        row.pack(fill=tk.X, pady=4)
        self.rows.append(row)

    def _move(self, row: TimelineRow, delta: int) -> None:
        index = self.rows.index(row)
        target = index + delta
        if target < 0 or target >= len(self.rows):
            return
        self.rows[index], self.rows[target] = self.rows[target], self.rows[index]
        self._repack()
        self.dirty = True

    def _repack(self) -> None:
        for row in self.rows:
            row.pack_forget()
        for row in self.rows:
            row.pack(fill=tk.X, pady=4)

    def _mark_dirty(self) -> None:
        self.dirty = True


class TimelineRow(ttk.Frame):
    def __init__(
        self,
        parent: tk.Widget,
        event: TimelineEvent,
        on_edit: Callable[[], None],
        on_move: Callable[[TimelineRow, int], None],
        on_delete: Callable[[TimelineRow], None],
        on_auto: Callable[[TimelineRow], None],
    ):
        super().__init__(parent, padding=2)
        self.on_edit = on_edit
        self.on_move = on_move
        self.on_delete = on_delete
        self.on_auto = on_auto
        self.date_var = tk.StringVar(value=format_date(event.event_date))
        self.time_var = tk.StringVar(value=event.local_time)
        self.event_var = tk.StringVar(value=event.event)
        self.loc_var = tk.StringVar(value=event.location)
        self.shown = ttk.Label(self, width=14)
        self._layout()
        self._bind()
        self._refresh_shown()

    def to_event(self) -> TimelineEvent:
        try:
            event_date = parse_date(self.date_var.get())
        except ValueError:
            event_date = date.today()
        return TimelineEvent(
            event_date=event_date,
            local_time=self.time_var.get().strip(),
            event=self.event_var.get().strip(),
            location=self.loc_var.get().strip()[:LOCATION_WIDTH],
        )

    def _layout(self) -> None:
        ttk.Label(self, text="Date").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(self, textvariable=self.date_var, width=12).grid(
            row=1, column=0, padx=(0, 6)
        )
        ttk.Label(self, text="Local HHMM").grid(row=0, column=1, sticky=tk.W)
        ttk.Entry(self, textvariable=self.time_var, width=8).grid(
            row=1, column=1, padx=(0, 6)
        )
        ttk.Label(self, text="Display").grid(row=0, column=2, sticky=tk.W)
        self.shown.grid(row=1, column=2, padx=(0, 6), sticky=tk.W)
        ttk.Label(self, text="Event").grid(row=0, column=3, sticky=tk.W)
        ttk.Entry(self, textvariable=self.event_var, width=28).grid(
            row=1, column=3, padx=(0, 6), sticky=tk.EW
        )
        ttk.Label(self, text="Location").grid(row=0, column=4, sticky=tk.W)
        ttk.Entry(self, textvariable=self.loc_var, width=LOCATION_WIDTH).grid(
            row=1, column=4, padx=(0, 6)
        )
        ttk.Label(self, text="Actions").grid(row=0, column=5, sticky=tk.W)
        self._action_buttons().grid(row=1, column=5, padx=(6, 0))
        self.columnconfigure(3, weight=1)

    def _action_buttons(self) -> ttk.Frame:
        box = ttk.Frame(self)
        ttk.Button(box, text="Up", width=4, command=lambda: self.on_move(self, -1)).pack(
            side=tk.LEFT
        )
        ttk.Button(box, text="Down", width=4, command=lambda: self.on_move(self, 1)).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Button(box, text="Auto", width=5, command=lambda: self.on_auto(self)).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Button(
            box, text="Delete", width=7, command=lambda: self.on_delete(self)
        ).pack(side=tk.LEFT, padx=2)
        return box

    def _bind(self) -> None:
        for var in (self.date_var, self.time_var, self.event_var, self.loc_var):
            var.trace_add("write", lambda *_args: self._on_change())

    def _on_change(self) -> None:
        self._refresh_shown()
        self.on_edit()

    def _refresh_shown(self) -> None:
        try:
            on_date = parse_date(self.date_var.get())
        except ValueError:
            on_date = None
        self.shown.configure(text=format_local_zulu(self.time_var.get(), on_date) or "—")
