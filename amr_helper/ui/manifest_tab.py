from __future__ import annotations

import tkinter as tk
from tkinter import simpledialog, ttk

from amr_helper.models import Leg, Person
from amr_helper.personnel import squads_in_order
from amr_helper.ui.scroll import scrollable_frame


class ManifestTab(ttk.Frame):
    def __init__(self, parent: tk.Widget, roster: list[Person], extras: list[Person]):
        super().__init__(parent, padding=8)
        self.roster = roster
        self.extras = extras
        self.leg_pax: dict[int, list[str]] = {0: []}
        self.current_leg = 0
        self.vars: dict[str, tk.BooleanVar] = {}
        self._build_toolbar()
        canvas, inner = scrollable_frame(self)
        canvas.pack(fill=tk.BOTH, expand=True)
        self.inner = inner
        self.rebuild()

    def _build_toolbar(self) -> None:
        bar = ttk.Frame(self)
        bar.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(bar, text="Leg").pack(side=tk.LEFT)
        self.leg_var = tk.StringVar(value="1")
        self.leg_pick = ttk.Combobox(
            bar, textvariable=self.leg_var, width=5, state="readonly", values=["1"]
        )
        self.leg_pick.pack(side=tk.LEFT, padx=8)
        self.leg_pick.bind("<<ComboboxSelected>>", self._on_leg_change)
        ttk.Button(bar, text="Add person", command=self._add_person).pack(side=tk.LEFT)

    def sync_leg_count(self, count: int) -> None:
        self._save_current()
        self.leg_pick.configure(values=[str(i) for i in range(1, count + 1)])
        for index in range(count):
            self.leg_pax.setdefault(index, [])
        extra_keys = [key for key in self.leg_pax if key >= count]
        for key in extra_keys:
            del self.leg_pax[key]
        if self.current_leg >= count:
            self.current_leg = count - 1
            self.leg_var.set(str(self.current_leg + 1))
        self._load_current()

    def apply_to_legs(self, legs: list[Leg]) -> None:
        self._save_current()
        for index, leg in enumerate(legs):
            leg.passenger_keys = list(self.leg_pax.get(index, []))

    def set_roster(self, roster: list[Person]) -> None:
        self._save_current()
        self.roster = roster
        self.rebuild()

    def rebuild(self) -> None:
        for child in self.inner.winfo_children():
            child.destroy()
        self.vars = {person.key: tk.BooleanVar(value=False) for person in self._people()}
        selected = set(self.leg_pax.get(self.current_leg, []))
        for key in selected:
            if key in self.vars:
                self.vars[key].set(True)
        self._render_groups()

    def _people(self) -> list[Person]:
        return [*self.roster, *self.extras]

    def _save_current(self) -> None:
        ordered = [
            person.key
            for person in self._people()
            if self.vars.get(person.key) and self.vars[person.key].get()
        ]
        self.leg_pax[self.current_leg] = ordered

    def _load_current(self) -> None:
        selected = set(self.leg_pax.get(self.current_leg, []))
        for key, var in self.vars.items():
            var.set(key in selected)

    def _on_leg_change(self, _event: tk.Event | None = None) -> None:
        self._save_current()
        self.current_leg = int(self.leg_var.get()) - 1
        self._load_current()

    def _render_groups(self) -> None:
        grouped: dict[str, list[Person]] = {}
        for person in self._people():
            grouped.setdefault(person.squad or "Added", []).append(person)
        order = squads_in_order(self._people())
        for squad in grouped:
            if squad not in order:
                order.append(squad)
        for squad in order:
            _SquadGroup(self.inner, squad, grouped[squad], self.vars).pack(
                fill=tk.X, pady=6, anchor=tk.W
            )

    def _add_person(self) -> None:
        person = prompt_new_person(self)
        if person is None:
            return
        self._save_current()
        self.extras.append(person)
        self.rebuild()


class _SquadGroup(ttk.LabelFrame):
    def __init__(
        self,
        parent: tk.Widget,
        squad: str,
        members: list[Person],
        vars_map: dict[str, tk.BooleanVar],
    ):
        super().__init__(parent, text=squad, padding=6)
        buttons = ttk.Frame(self)
        buttons.pack(fill=tk.X)
        ttk.Button(
            buttons, text=f"Select {squad}", command=lambda: _set_group(members, vars_map, True)
        ).pack(side=tk.LEFT)
        ttk.Button(
            buttons, text="Clear", command=lambda: _set_group(members, vars_map, False)
        ).pack(side=tk.LEFT, padx=6)
        for person in members:
            ttk.Checkbutton(
                self, text=person.display_name(), variable=vars_map[person.key]
            ).pack(anchor=tk.W)


def _set_group(members: list[Person], vars_map: dict[str, tk.BooleanVar], value: bool) -> None:
    for person in members:
        vars_map[person.key].set(value)


def prompt_new_person(parent: tk.Widget) -> Person | None:
    rank = simpledialog.askstring("Add person", "Rank:", parent=parent)
    if not rank:
        return None
    last = simpledialog.askstring("Add person", "Last name:", parent=parent)
    if not last:
        return None
    last_four = simpledialog.askstring("Add person", "Last 4:", parent=parent)
    if not last_four:
        return None
    squad = simpledialog.askstring("Add person", "Squad (optional):", parent=parent) or "Added"
    return Person(rank=rank.strip(), last_name=last.strip(), last_four=last_four.strip().zfill(4), squad=squad.strip())
