from __future__ import annotations

from dataclasses import dataclass

from amr_helper import defaults
from amr_helper.models import Leg, Mission, Person


@dataclass
class ManifestLine:
    last_name: str
    rank: str = ""
    last_four: str = ""
    pickup: str = ""
    dropoff: str = ""
    leg_number: int | None = None
    no_troops: bool = False

    def fields(self, row: int) -> dict[str, str]:
        if self.no_troops:
            return {
                f"Last NameRow{row}": self.last_name,
                f"PickUp LocationRow{row}": self.pickup,
                f"DropOff LocationRow{row}": self.dropoff,
                f"{self.leg_number}Row{row}": "X",
            }
        return {
            f"RankRow{row}": self.rank,
            f"Last NameRow{row}": self.last_name,
            f"NationalityRow{row}": defaults.NATIONALITY,
            f"ServiceRow{row}": defaults.SERVICE,
            f"Last 4 IDSSNRow{row}": self.last_four,
            f"PickUp LocationRow{row}": self.pickup,
            f"DropOff LocationRow{row}": self.dropoff,
            f"{self.leg_number}Row{row}": "X",
        }


def page_values(mission: Mission, people: dict[str, Person]) -> list[dict[str, str]]:
    lines = build_lines(mission, people)
    size = defaults.MAX_MANIFEST_ROWS
    if not lines:
        return [{}]
    return [_fields_for_page(lines[start : start + size]) for start in range(0, len(lines), size)]


def row_count(mission: Mission) -> int:
    return sum(leg.pax_count() or 1 for leg in mission.legs)


def build_lines(mission: Mission, people: dict[str, Person]) -> list[ManifestLine]:
    lines: list[ManifestLine] = []
    for number, leg in enumerate(mission.legs, start=1):
        if not leg.passenger_keys:
            lines.append(_no_troops_line(number, leg))
            continue
        lines.extend(_pax_lines(number, leg, people))
    return lines


def _no_troops_line(leg_number: int, leg: Leg) -> ManifestLine:
    return ManifestLine(
        last_name=defaults.NO_TROOPS_LABEL,
        pickup=leg.start_lz,
        dropoff=leg.end_lz,
        leg_number=leg_number,
        no_troops=True,
    )


def _pax_lines(number: int, leg: Leg, people: dict[str, Person]) -> list[ManifestLine]:
    lines = []
    for key in leg.passenger_keys:
        person = people.get(key)
        if person is None:
            continue
        lines.append(
            ManifestLine(
                last_name=person.last_name,
                rank=person.rank,
                last_four=person.last_four,
                pickup=leg.start_lz,
                dropoff=leg.end_lz,
                leg_number=number,
            )
        )
    return lines


def _fields_for_page(lines: list[ManifestLine]) -> dict[str, str]:
    values: dict[str, str] = {}
    for row, line in enumerate(lines, start=1):
        values.update(line.fields(row))
    return values
