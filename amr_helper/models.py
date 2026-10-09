from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from amr_helper import defaults


@dataclass(frozen=True)
class LandingZone:
    name: str
    lon: float
    lat: float
    mgrs: str


@dataclass
class Person:
    rank: str
    last_name: str
    last_four: str
    squad: str = ""

    @property
    def key(self) -> str:
        return f"{self.rank}|{self.last_name}|{self.last_four}"

    def display_name(self) -> str:
        return f"{self.rank} {self.last_name} {self.last_four}"


@dataclass
class Leg:
    start_lz: str = ""
    end_lz: str = ""
    dep_time: str = ""
    arr_time: str = ""
    passenger_keys: list[str] = field(default_factory=list)

    def pax_count(self) -> int:
        return len(self.passenger_keys)


@dataclass
class TimelineEvent:
    event_date: date
    local_time: str
    event: str
    location: str = ""


@dataclass
class Mission:
    mission_date: date = field(default_factory=date.today)
    submitted_date: date = field(default_factory=date.today)
    unit: str = defaults.REQUESTING_UNIT
    poc_name: str = defaults.SUPPORTED_UNIT_POC
    poc_phone: str = defaults.SUPPORTED_UNIT_POC_PHONE
    poc_email: str = defaults.REQUESTOR_EMAIL
    reviewer_name: str = defaults.SUPPORTED_UNIT_REVIEWER
    reviewer_email: str = defaults.UNIT_REVIEWER_EMAIL
    mission_statement: str = defaults.MISSION_STATEMENT
    training_intent: str = defaults.TRAINING_INTENT
    task_1: str = defaults.TASK_1
    purpose_1: str = defaults.PURPOSE_1
    mission_description: str = ""
    remarks: str = ""
    legs: list[Leg] = field(default_factory=list)
    extra_people: list[Person] = field(default_factory=list)
    timeline: list[TimelineEvent] = field(default_factory=list)

    def max_pax(self) -> int:
        if not self.legs:
            return 0
        return max(leg.pax_count() for leg in self.legs)

    def unique_lz_names(self) -> list[str]:
        seen: list[str] = []
        for leg in self.legs:
            for name in (leg.start_lz, leg.end_lz):
                if name and name not in seen:
                    seen.append(name)
        return seen
