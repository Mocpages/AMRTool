from __future__ import annotations

from amr_helper.dates import is_hhmm
from amr_helper.defaults import MAX_HLZ_ROWS, MAX_LEGS, MAX_TIMELINE_ROWS
from amr_helper.models import Mission


def validate_mission(mission: Mission, known_lzs: set[str]) -> list[str]:
    errors: list[str] = []
    errors.extend(_mission_text_errors(mission))
    errors.extend(_leg_errors(mission, known_lzs))
    errors.extend(_timeline_errors(mission))
    if len(mission.unique_lz_names()) > MAX_HLZ_ROWS:
        errors.append(
            f"{len(mission.unique_lz_names())} unique LZs; CONOP table allows {MAX_HLZ_ROWS}"
        )
    return errors


def _mission_text_errors(mission: Mission) -> list[str]:
    errors: list[str] = []
    if not mission.mission_description.strip():
        errors.append("mission description is required")
    if not mission.remarks.strip():
        errors.append("remarks are required")
    if not mission.legs:
        errors.append("add at least one leg")
    if len(mission.legs) > MAX_LEGS:
        errors.append(f"at most {MAX_LEGS} legs")
    return errors


def _leg_errors(mission: Mission, known_lzs: set[str]) -> list[str]:
    errors: list[str] = []
    for index, leg in enumerate(mission.legs, start=1):
        prefix = f"leg {index}"
        if not leg.start_lz or not leg.end_lz:
            errors.append(f"{prefix}: select start and end LZs")
        elif leg.start_lz == leg.end_lz:
            errors.append(f"{prefix}: start and end LZ must differ")
        for name in (leg.start_lz, leg.end_lz):
            if name and name not in known_lzs:
                errors.append(f"{prefix}: unknown LZ {name}")
    return errors


def _timeline_errors(mission: Mission) -> list[str]:
    events = [event for event in mission.timeline if event.event or event.local_time]
    errors: list[str] = []
    if len(events) > MAX_TIMELINE_ROWS:
        errors.append(f"timeline has {len(events)} events; PDF allows {MAX_TIMELINE_ROWS}")
    for index, event in enumerate(events, start=1):
        if not is_hhmm(event.local_time):
            errors.append(f"timeline {index}: time must be local HHMM")
        if not event.event:
            errors.append(f"timeline {index}: event text is required")
    return errors
