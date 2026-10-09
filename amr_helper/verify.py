"""Fill a sample AMR and check key PDF field values."""

from __future__ import annotations

import os
import re
import tempfile
from datetime import date
from pathlib import Path

import fitz

from amr_helper.config import ensure_verify_paths
from amr_helper.defaults import ARF_LZ_NAME, NO_TROOPS_LABEL
from amr_helper.imagery import ensure_lz_images, route_images
from amr_helper.kmz_lzs import load_landing_zones
from amr_helper.manifest import page_values as manifest_pages
from amr_helper.models import Leg, Mission, Person
from amr_helper.overview_map import _used_zones, build_overview
from amr_helper.paths import app_dir
from amr_helper.personnel import load_roster, people_by_key
from amr_helper.pdf_fields import build_field_values
from amr_helper.pdf_fill import fill_pdf
from amr_helper.timeline import add_hhmm, auto_local_time, flight_minutes
from amr_helper.validate import validate_mission

MGRS_RE = re.compile(r"^\d{2}[A-Z] [A-Z]{2} \d{5} \d{5}$")


def main() -> None:
    ensure_verify_paths()
    values, filled = _write_sample()
    try:
        _assert_fields(values, filled)
    finally:
        filled.unlink(missing_ok=True)
    _assert_overflow_page()
    _assert_arf_excluded()
    _assert_auto_time()
    print("verify_fill: ok")


def _assert_auto_time() -> None:
    if flight_minutes(0) != 15:
        raise AssertionError("zero distance should be 15 min")
    if flight_minutes(10) != 15:  # 3 min raw → min 15
        raise AssertionError("short hop should floor at 15")
    if flight_minutes(60) != 20:  # 18 min → ceil 20
        raise AssertionError("60 km @ 200 kph should round to 20")
    if add_hhmm("1400", 20) != "1420":
        raise AssertionError("add_hhmm failed")
    zones = load_landing_zones()
    lz_mgrs = {zone.name: zone.mgrs for zone in zones}
    apache, cali = lz_mgrs["LZ APACHE"], lz_mgrs["LZ CALI"]
    got = auto_local_time("1400", apache, cali, lz_mgrs)
    if not got or len(got) != 4:
        raise AssertionError(f"auto_local_time bad: {got!r}")


def _write_sample() -> tuple[dict[str, str | bool], Path]:
    zones = load_landing_zones()
    roster = load_roster()
    squad = [person for person in roster if person.squad == "2-1"]
    mission = Mission(
        mission_date=date(2026, 8, 24),
        submitted_date=date(2026, 8, 24),
        mission_description="Move 1st squad from LZ APACHE to LZ CALI.",
        remarks="N/A",
        legs=[
            Leg(
                start_lz="LZ APACHE",
                end_lz="LZ CALI",
                dep_time="1400",
                arr_time="1430",
                passenger_keys=[person.key for person in squad],
            ),
            Leg(start_lz="LZ CALI", end_lz="LZ BAKER", dep_time="1500", arr_time="1530"),
        ],
    )
    known = {zone.name for zone in zones}
    errors = validate_mission(mission, known)
    if errors:
        raise AssertionError(errors)
    lz_mgrs = {zone.name: zone.mgrs for zone in zones}
    values = build_field_values(mission, lz_mgrs, people_by_key(roster, []))
    images = app_dir() / "lz_images"
    photos = route_images(mission.unique_lz_names(), ensure_lz_images(zones, images))
    overview = build_overview(zones, mission.legs, images)
    handle, name = tempfile.mkstemp(suffix=".pdf")
    os.close(handle)
    dest = Path(name)
    fill_pdf(values, dest, lz_images=photos, overview=overview)
    return values, dest


def _assert_fields(values: dict[str, str | bool], filled: Path) -> None:
    got = _read_fields(filled)
    checks = {
        "Passenger Count": "8",
        "FROM1": "LZ APACHE",
        "TO1": "LZ CALI",
        "1Row1": "X",
        "PickUp LocationRow1": "LZ APACHE",
        "DropOff LocationRow1": "LZ CALI",
        "Group1": "No",
        "HLZ NameRow1": "LZ APACHE",
        "EventRow1": "DEPART LZ APACHE",
        "Time(MPT)1": "1400L/2100Z",
        "RankRow1": "SGT",
        "Last NameRow1": "Lister",
        "Last NameRow9": NO_TROOPS_LABEL,
        "PickUp LocationRow9": "LZ CALI",
        "DropOff LocationRow9": "LZ BAKER",
        "2Row9": "X",
    }
    for name, expected in checks.items():
        if got.get(name) != expected:
            raise AssertionError(f"{name}: {got.get(name)!r} != {expected!r}")
    grid = str(got.get("GridsRow1", ""))
    if not MGRS_RE.match(grid):
        raise AssertionError(f"GridsRow1 not 10-digit MGRS: {grid!r}")
    if values["Passenger Count"] != "8":
        raise AssertionError("passenger count in values dict")
    if values.get("RankRow9"):
        raise AssertionError("NO TROOPS row should leave Rank blank")
    doc = fitz.open(filled)
    try:
        if len(doc[2].get_images()) != 4:
            raise AssertionError("page 3 should contain overview plus 3 LZ images")
        if doc.page_count != 4:
            raise AssertionError("sample should stay on 4 pages")
    finally:
        doc.close()


def _assert_overflow_page() -> None:
    extras = [Person("PVT", f"Pax{index:02d}", f"{index:04d}") for index in range(31)]
    mission = Mission(
        mission_description="Overflow manifest.",
        remarks="N/A",
        legs=[
            Leg(
                start_lz="LZ APACHE",
                end_lz="LZ CALI",
                passenger_keys=[person.key for person in extras],
            )
        ],
    )
    dest = _temp_pdf()
    try:
        _write_mission(mission, extras, dest, overview=False)
        doc = fitz.open(dest)
        try:
            if doc.page_count != 5:
                raise AssertionError(f"expected 5 pages, got {doc.page_count}")
            first = {
                w.field_name: str(w.field_value) for w in doc[3].widgets() or []
            }
            overflow_widgets = list(doc[4].widgets() or [])
        finally:
            doc.close()
        if first.get("Last NameRow1") != "Pax00":
            raise AssertionError(f"first page row1 overwritten: {first.get('Last NameRow1')!r}")
        if first.get("Last NameRow30") != "Pax29":
            raise AssertionError(f"first page row30: {first.get('Last NameRow30')!r}")
        if first.get("Last NameRow1") == "Pax30":
            raise AssertionError("overflow overwrote first-page beginning")
        if overflow_widgets:
            raise AssertionError("overflow page should be baked (no form widgets)")
        text = _page_text(dest, 4)
        if "Pax30" not in text:
            raise AssertionError("overflow page missing continuation row Pax30")
        if "Pax00" in text:
            raise AssertionError("overflow page still shows first-page rows")
    finally:
        dest.unlink(missing_ok=True)


def _page_text(path: Path, page_index: int) -> str:
    doc = fitz.open(path)
    try:
        return doc[page_index].get_text()
    finally:
        doc.close()


def _assert_arf_excluded() -> None:
    zones = load_landing_zones()
    if not any(zone.name == ARF_LZ_NAME for zone in zones):
        raise AssertionError("ARF LZ missing from dropdown list")
    names = [ARF_LZ_NAME, "LZ APACHE", "LZ CALI"]
    photos = route_images(names, ensure_lz_images(zones, app_dir() / "lz_images"))
    if len(photos) != 2:
        raise AssertionError("ARF should not get a micro picture")
    used = _used_zones(
        zones,
        [Leg(start_lz="LZ APACHE", end_lz=ARF_LZ_NAME), Leg(start_lz="LZ APACHE", end_lz="LZ CALI")],
    )
    if any(zone.name == ARF_LZ_NAME for zone in used):
        raise AssertionError("ARF should not appear on the map")
    if [zone.name for zone in used] != ["LZ APACHE", "LZ CALI"]:
        raise AssertionError(f"map LZs { [z.name for z in used] }")


def _write_mission(
    mission: Mission,
    extras: list[Person],
    dest: Path,
    overview: bool,
) -> None:
    zones = load_landing_zones()
    roster = load_roster()
    people = people_by_key(roster, extras)
    lz_mgrs = {zone.name: zone.mgrs for zone in zones}
    values = build_field_values(mission, lz_mgrs, people)
    extra = manifest_pages(mission, people)[1:]
    images = app_dir() / "lz_images"
    map_path = build_overview(zones, mission.legs, images) if overview else None
    fill_pdf(values, dest, extra_manifest=extra, overview=map_path)


def _temp_pdf() -> Path:
    handle, name = tempfile.mkstemp(suffix=".pdf")
    os.close(handle)
    return Path(name)


def _read_fields(path: Path) -> dict[str, str]:
    doc = fitz.open(path)
    got: dict[str, str] = {}
    try:
        for page in doc:
            for widget in page.widgets() or []:
                got[widget.field_name] = str(widget.field_value)
    finally:
        doc.close()
    return got


if __name__ == "__main__":
    main()
