from __future__ import annotations

from amr_helper import defaults
from amr_helper.dates import format_date, format_local_zulu
from amr_helper.manifest import page_values as manifest_page_values
from amr_helper.models import Mission, Person, TimelineEvent
from amr_helper.timeline import default_timeline, times_for_leg


def build_field_values(
    mission: Mission,
    lz_mgrs: dict[str, str],
    people: dict[str, Person],
) -> dict[str, str | bool]:
    values: dict[str, str | bool] = {}
    values.update(_admin_fields(mission))
    values.update(_planning_fields(mission))
    values.update(_hlz_table_fields(mission))
    values.update(_section3_fields())
    values.update(_conop_fields(mission, lz_mgrs))
    pages = manifest_page_values(mission, people)
    if pages:
        values.update(pages[0])
    return values


def _admin_fields(mission: Mission) -> dict[str, str]:
    mission_date = format_date(mission.mission_date)
    return {
        "MSN Dates": mission_date,
        "Mission Date": mission_date,
        "DTG Request Submitted": format_date(mission.submitted_date),
        "Supported Unit": mission.unit,
        "Supported Unit POC": mission.poc_name,
        "Supported Unit POC Phone": mission.poc_phone,
        "Supported Unit POC Email": mission.poc_email,
        "Supported Unit Reviewer": mission.reviewer_name,
        "Unit Reviewer Email": mission.reviewer_email,
        "Mission Priority Number:": defaults.MISSION_PRIORITY,
    }


def _planning_fields(mission: Mission) -> dict[str, str]:
    return {
        "Supported Unit Mission StatementRow1": mission.mission_statement,
        "Supported Unit Training Intent  End StateRow1": mission.training_intent,
        "T1": mission.task_1,
        "P1": mission.purpose_1,
        "Passenger Count": str(mission.max_pax()),
        "Weight  Person": defaults.WEIGHT_PER_PERSON,
        "UH_2": defaults.AIRCRAFT_ASSIGNED,
        "Special-Instructions1": mission.mission_description,
        "Remarks": mission.remarks,
    }


def _hlz_table_fields(mission: Mission) -> dict[str, str]:
    values: dict[str, str] = {}
    events = mission.timeline or default_timeline(mission, {})
    used: set[int] = set()
    for index, leg in enumerate(mission.legs, start=1):
        dep, arr = times_for_leg(leg, events, used)
        values[f"Dep Time{index}"] = format_local_zulu(dep)
        values[f"FROM{index}"] = leg.start_lz
        values[f"TO{index}"] = leg.end_lz
        values[f"Arr Time{index}"] = format_local_zulu(arr)
        values[f"{index}Total Pax Count Per Leg"] = str(leg.pax_count())
    return values


def _section3_fields() -> dict[str, str | bool]:
    values: dict[str, str | bool] = {"Group1": "No"}
    for index in range(1, 7):
        yes_name = "Yes" if index == 1 else f"Yes{index}"
        no_name = "No" if index == 1 else f"No{index}"
        values[yes_name] = False
        values[no_name] = True
    for index in range(1, 6):
        values[f"waiver{index}"] = "No"
    for index in range(1, 9):
        values[f"Special{index}"] = "No"
    return values


def _conop_fields(mission: Mission, lz_mgrs: dict[str, str]) -> dict[str, str]:
    values = _timeline_fields(mission, lz_mgrs)
    for index, name in enumerate(mission.unique_lz_names(), start=1):
        if index > defaults.MAX_HLZ_ROWS:
            break
        values[f"HLZ NameRow{index}"] = name
        values[f"GridsRow{index}"] = lz_mgrs.get(name, "")
    return values


def _timeline_fields(mission: Mission, lz_mgrs: dict[str, str]) -> dict[str, str]:
    values: dict[str, str] = {}
    events = mission.timeline or default_timeline(mission, lz_mgrs)
    events = [
        event
        for event in events
        if event.event or event.local_time
    ]
    for row, event in enumerate(events[: defaults.MAX_TIMELINE_ROWS], start=1):
        values.update(_timeline_row(row, event))
    return values


def _timeline_row(row: int, event: TimelineEvent) -> dict[str, str]:
    return {
        f"Date {row}": format_date(event.event_date),
        f"Time(MPT){row}": format_local_zulu(event.local_time, event.event_date),
        f"EventRow{row}": event.event,
        f"LocationRow{row}": event.location,
    }


