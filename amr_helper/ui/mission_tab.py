from __future__ import annotations

from collections.abc import Callable
from datetime import date
from pathlib import Path
import tkinter as tk
from tkinter import ttk

from amr_helper.dates import MONTHS
from amr_helper.models import Mission
from amr_helper.ui.scroll import scrollable_frame


class MissionTab(ttk.Frame):
    def __init__(
        self,
        parent: tk.Widget,
        mission: Mission,
        on_choose_csv: Callable[[], None] | None = None,
        on_choose_kmz: Callable[[], None] | None = None,
    ):
        super().__init__(parent, padding=8)
        canvas, inner = scrollable_frame(self)
        canvas.pack(fill=tk.BOTH, expand=True)
        self.sources = DataSourcesFrame(inner, on_choose_csv, on_choose_kmz)
        self.sources.pack(fill=tk.X, pady=(0, 10))
        self._date = _DateFields(inner, mission.mission_date)
        self._date.pack(anchor=tk.W, pady=(0, 8))
        self.description = _labeled_text(inner, "Mission description")
        self.remarks = _labeled_text(inner, "Remarks")
        self.defaults = DefaultsFrame(inner, mission)
        self.defaults.pack(fill=tk.X, pady=(12, 0))
        self.description.insert("1.0", mission.mission_description)
        self.remarks.insert("1.0", mission.remarks)

    def collect(self) -> Mission:
        mission = self.defaults.collect()
        mission.mission_date = self._date.get()
        mission.submitted_date = date.today()
        mission.mission_description = self.description.get("1.0", "end").strip()
        mission.remarks = self.remarks.get("1.0", "end").strip()
        return mission

    def set_source_paths(self, csv_path: Path | None, kmz_path: Path | None) -> None:
        self.sources.set_paths(csv_path, kmz_path)


class DataSourcesFrame(ttk.LabelFrame):
    def __init__(
        self,
        parent: tk.Widget,
        on_choose_csv: Callable[[], None] | None,
        on_choose_kmz: Callable[[], None] | None,
    ):
        super().__init__(parent, text="Data sources", padding=8)
        self.csv_var = tk.StringVar(value="(not set)")
        self.kmz_var = tk.StringVar(value="(not set)")
        ttk.Label(self, text="Roster CSV").grid(row=0, column=0, sticky=tk.W)
        ttk.Label(self, textvariable=self.csv_var, width=56).grid(
            row=0, column=1, sticky=tk.W, padx=6
        )
        ttk.Button(self, text="Choose…", command=on_choose_csv or (lambda: None)).grid(
            row=0, column=2, padx=4
        )
        ttk.Label(self, text="LZ KMZ").grid(row=1, column=0, sticky=tk.W, pady=(6, 0))
        ttk.Label(self, textvariable=self.kmz_var, width=56).grid(
            row=1, column=1, sticky=tk.W, padx=6, pady=(6, 0)
        )
        ttk.Button(self, text="Choose…", command=on_choose_kmz or (lambda: None)).grid(
            row=1, column=2, padx=4, pady=(6, 0)
        )

    def set_paths(self, csv_path: Path | None, kmz_path: Path | None) -> None:
        self.csv_var.set(_short_path(csv_path))
        self.kmz_var.set(_short_path(kmz_path))


def _short_path(path: Path | None) -> str:
    if path is None:
        return "(not set)"
    text = str(path)
    return text if len(text) <= 64 else f"…{text[-61:]}"


class DefaultsFrame(ttk.LabelFrame):
    def __init__(self, parent: tk.Widget, mission: Mission):
        super().__init__(parent, text="Autofilled (editable)", padding=8)
        self.vars = {
            "unit": tk.StringVar(value=mission.unit),
            "poc_name": tk.StringVar(value=mission.poc_name),
            "poc_phone": tk.StringVar(value=mission.poc_phone),
            "poc_email": tk.StringVar(value=mission.poc_email),
            "reviewer_name": tk.StringVar(value=mission.reviewer_name),
            "reviewer_email": tk.StringVar(value=mission.reviewer_email),
            "task_1": tk.StringVar(value=mission.task_1),
            "purpose_1": tk.StringVar(value=mission.purpose_1),
        }
        self.statement = _add_default_rows(self, self.vars, mission)

    def collect(self) -> Mission:
        values = {key: var.get().strip() for key, var in self.vars.items()}
        return Mission(
            unit=values["unit"],
            poc_name=values["poc_name"],
            poc_phone=values["poc_phone"],
            poc_email=values["poc_email"],
            reviewer_name=values["reviewer_name"],
            reviewer_email=values["reviewer_email"],
            task_1=values["task_1"],
            purpose_1=values["purpose_1"],
            mission_statement=self.statement.get("1.0", "end").strip(),
            training_intent=self.training_intent.get("1.0", "end").strip(),
        )


def _add_default_rows(
    frame: DefaultsFrame, vars_map: dict[str, tk.StringVar], mission: Mission
) -> tk.Text:
    labels = [
        ("Unit", "unit"),
        ("POC", "poc_name"),
        ("POC phone", "poc_phone"),
        ("POC email", "poc_email"),
        ("Reviewer / BDE BAE", "reviewer_name"),
        ("Reviewer email", "reviewer_email"),
        ("T1", "task_1"),
        ("P1", "purpose_1"),
    ]
    for row, (label, key) in enumerate(labels):
        ttk.Label(frame, text=label).grid(row=row, column=0, sticky=tk.W, pady=2)
        ttk.Entry(frame, textvariable=vars_map[key], width=48).grid(
            row=row, column=1, sticky=tk.EW, pady=2
        )
    frame.columnconfigure(1, weight=1)
    ttk.Label(frame, text="Mission statement").grid(
        row=len(labels), column=0, sticky=tk.NW, pady=4
    )
    statement = tk.Text(frame, height=3, wrap=tk.WORD)
    statement.grid(row=len(labels), column=1, sticky=tk.EW, pady=4)
    statement.insert("1.0", mission.mission_statement)
    ttk.Label(frame, text="Training intent").grid(
        row=len(labels) + 1, column=0, sticky=tk.NW, pady=4
    )
    intent = tk.Text(frame, height=3, wrap=tk.WORD)
    intent.grid(row=len(labels) + 1, column=1, sticky=tk.EW, pady=4)
    intent.insert("1.0", mission.training_intent)
    frame.training_intent = intent
    return statement


class _DateFields(ttk.Frame):
    def __init__(self, parent: tk.Widget, initial: date):
        super().__init__(parent)
        ttk.Label(self, text="Mission date").pack(side=tk.LEFT, padx=(0, 8))
        self.day = ttk.Combobox(
            self, width=4, values=[f"{day:02d}" for day in range(1, 32)]
        )
        self.month = ttk.Combobox(self, width=5, values=list(MONTHS))
        years = [str(year) for year in range(initial.year - 1, initial.year + 4)]
        self.year = ttk.Combobox(self, width=6, values=years)
        self.day.set(f"{initial.day:02d}")
        self.month.set(MONTHS[initial.month - 1])
        self.year.set(str(initial.year))
        self.day.pack(side=tk.LEFT)
        self.month.pack(side=tk.LEFT, padx=4)
        self.year.pack(side=tk.LEFT)

    def get(self) -> date:
        return date(
            int(self.year.get()), MONTHS.index(self.month.get()) + 1, int(self.day.get())
        )


def _labeled_text(parent: tk.Widget, label: str) -> tk.Text:
    ttk.Label(parent, text=label).pack(anchor=tk.W, pady=(8, 2))
    text = tk.Text(parent, height=5, wrap=tk.WORD)
    text.pack(fill=tk.X)
    return text
