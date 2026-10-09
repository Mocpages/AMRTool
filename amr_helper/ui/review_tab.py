from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from amr_helper.dates import format_local_zulu
from amr_helper.defaults import MAX_MANIFEST_ROWS
from amr_helper.manifest import row_count
from amr_helper.models import LandingZone, Mission
from amr_helper.timeline import times_for_leg


class ReviewTab(ttk.Frame):
    def __init__(self, parent: tk.Widget):
        super().__init__(parent, padding=8)
        self.summary = tk.Text(self, height=24, wrap=tk.WORD, state=tk.DISABLED)
        self.summary.pack(fill=tk.BOTH, expand=True)

    def show(self, mission: Mission, zones: list[LandingZone]) -> None:
        mgrs = {zone.name: zone.mgrs for zone in zones}
        lines = _summary_lines(mission, mgrs)
        self.summary.configure(state=tk.NORMAL)
        self.summary.delete("1.0", tk.END)
        self.summary.insert("1.0", "\n".join(lines))
        self.summary.configure(state=tk.DISABLED)


def _summary_lines(mission: Mission, mgrs: dict[str, str]) -> list[str]:
    rows = row_count(mission)
    pages = (rows + MAX_MANIFEST_ROWS - 1) // MAX_MANIFEST_ROWS if rows else 0
    lines = [
        f"Mission date: {mission.mission_date.isoformat()}",
        f"Unit: {mission.unit}",
        f"Passenger count (largest leg): {mission.max_pax()}",
        f"Manifest rows: {rows} ({pages} page{'s' if pages != 1 else ''})",
        "",
        "Legs:",
    ]
    used: set[int] = set()
    for index, leg in enumerate(mission.legs, start=1):
        dep, arr = times_for_leg(leg, mission.timeline, used)
        lines.append(
            f"  {index}. {leg.start_lz} -> {leg.end_lz}  "
            f"{format_local_zulu(dep) or dep}/"
            f"{format_local_zulu(arr) or arr}  "
            f"pax {leg.pax_count()}"
        )
    lines.append("")
    lines.append("Timeline:")
    for event in mission.timeline:
        shown = format_local_zulu(event.local_time, event.event_date) or event.local_time
        lines.append(f"  {event.event_date.isoformat()} {shown}  {event.event}  {event.location}")
    lines.append("")
    lines.append("HLZs (MGRS):")
    for name in mission.unique_lz_names():
        lines.append(f"  {name}: {mgrs.get(name, 'unknown')}")
    return lines
