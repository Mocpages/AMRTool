from __future__ import annotations

import csv
from pathlib import Path

from amr_helper.models import Person
from amr_helper.paths import csv_path

SQUAD_ORDER = ("HQ", "1st", "2nd", "3rd")


def load_roster(path: Path | None = None) -> list[Person]:
    roster_path = path or csv_path()
    with roster_path.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    people = [_row_to_person(row) for row in rows]
    return [person for person in people if person is not None]


def people_by_key(roster: list[Person], extras: list[Person]) -> dict[str, Person]:
    index = {person.key: person for person in roster}
    for person in extras:
        index[person.key] = person
    return index


def squads_in_order(people: list[Person]) -> list[str]:
    present = {person.squad for person in people if person.squad}
    ordered = [name for name in SQUAD_ORDER if name in present]
    extras = sorted(present - set(SQUAD_ORDER))
    return ordered + extras


def _row_to_person(row: dict[str, str]) -> Person | None:
    rank = (row.get("Rank") or "").strip()
    last = (row.get("Last") or "").strip()
    last_four = (row.get("DODID (L4)") or "").strip().zfill(4)
    squad = (row.get("Squad") or "").strip()
    if not rank or not last or not last_four:
        return None
    return Person(rank=rank, last_name=last, last_four=last_four, squad=squad)
