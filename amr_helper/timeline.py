from __future__ import annotations

import math

from amr_helper.dates import hhmm_digits, is_hhmm
from amr_helper.mgrs_convert import from_mgrs
from amr_helper.models import Leg, Mission, TimelineEvent

CRUISE_KPH = 200.0
MIN_FLIGHT_MINUTES = 15
ROUND_UP_MINUTES = 5


def default_timeline(mission: Mission, lz_mgrs: dict[str, str]) -> list[TimelineEvent]:
    events: list[TimelineEvent] = []
    for leg in mission.legs:
        events.append(
            _leg_event(mission, leg.dep_time, f"DEPART {leg.start_lz}", leg.start_lz, lz_mgrs)
        )
        events.append(
            _leg_event(mission, leg.arr_time, f"ARRIVE {leg.end_lz}", leg.end_lz, lz_mgrs)
        )
    return events


def times_for_leg(
    leg: Leg, events: list[TimelineEvent], used: set[int]
) -> tuple[str, str]:
    dep = _take_time(events, used, "DEPART", leg.start_lz) or leg.dep_time
    arr = _take_time(events, used, "ARRIVE", leg.end_lz) or leg.arr_time
    return dep, arr


def _take_time(
    events: list[TimelineEvent], used: set[int], verb: str, lz_name: str
) -> str:
    if not lz_name:
        return ""
    verb_u, lz_u = verb.upper(), lz_name.upper()
    for index, event in enumerate(events):
        if index in used:
            continue
        text = event.event.upper()
        if verb_u in text and lz_u in text:
            used.add(index)
            return event.local_time
    return ""


def auto_local_time(
    prev_hhmm: str,
    prev_location: str,
    curr_location: str,
    lz_mgrs: dict[str, str],
) -> str:
    if not is_hhmm(prev_hhmm):
        raise ValueError("previous event needs a local HHMM time")
    minutes = flight_minutes(
        distance_km(
            _latlon(prev_location, lz_mgrs),
            _latlon(curr_location, lz_mgrs),
        )
    )
    return add_hhmm(prev_hhmm, minutes)


def flight_minutes(km: float) -> int:
    if km <= 0:
        return MIN_FLIGHT_MINUTES
    raw = km / CRUISE_KPH * 60.0
    rounded = math.ceil(raw / ROUND_UP_MINUTES) * ROUND_UP_MINUTES
    return max(MIN_FLIGHT_MINUTES, int(rounded))


def distance_km(a: tuple[float, float], b: tuple[float, float]) -> float:
    lat1, lon1 = map(math.radians, a)
    lat2, lon2 = map(math.radians, b)
    dlat, dlon = lat2 - lat1, lon2 - lon1
    chord = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )
    return 6371.0 * 2 * math.asin(min(1.0, math.sqrt(chord)))


def add_hhmm(hhmm: str, minutes: int) -> str:
    digits = hhmm_digits(hhmm)
    total = (int(digits[:2]) * 60 + int(digits[2:]) + minutes) % (24 * 60)
    return f"{total // 60:02d}{total % 60:02d}"


def _latlon(location: str, lz_mgrs: dict[str, str]) -> tuple[float, float]:
    text = location.strip()
    if not text:
        raise ValueError("location is empty")
    mgrs = lz_mgrs.get(text, text)
    if not mgrs:
        raise ValueError(f"no grid for {text!r}")
    return from_mgrs(mgrs)


def _leg_event(
    mission: Mission,
    local_time: str,
    event: str,
    lz_name: str,
    lz_mgrs: dict[str, str],
) -> TimelineEvent:
    return TimelineEvent(
        event_date=mission.mission_date,
        local_time=local_time,
        event=event,
        location=lz_mgrs.get(lz_name, lz_name),
    )
