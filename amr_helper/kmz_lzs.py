from __future__ import annotations

import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from amr_helper import defaults
from amr_helper.mgrs_convert import from_mgrs, to_mgrs
from amr_helper.models import LandingZone
from amr_helper.paths import kmz_path

KML_NS = {"kml": "http://www.opengis.net/kml/2.2"}


def load_landing_zones(path: Path | None = None) -> list[LandingZone]:
    kml_bytes = _read_kml(path or kmz_path())
    root = ET.fromstring(kml_bytes)
    from_kmz = [z for z in (_placemark_to_lz(pm) for pm in root.findall(".//kml:Placemark", KML_NS)) if z]
    return sorted(_with_virtual(_with_extras(from_kmz)), key=lambda zone: zone.name)


def _with_extras(zones: list[LandingZone]) -> list[LandingZone]:
    known = {zone.name.upper() for zone in zones}
    extras = []
    for name, mgrs in defaults.EXTRA_LANDING_ZONES:
        if name.upper() in known:
            continue
        lat, lon = from_mgrs(mgrs)
        extras.append(LandingZone(name=name, lon=lon, lat=lat, mgrs=mgrs))
    return [*zones, *extras]


def _with_virtual(zones: list[LandingZone]) -> list[LandingZone]:
    known = {zone.name.upper() for zone in zones}
    if defaults.ARF_LZ_NAME.upper() in known:
        return zones
    virtual = LandingZone(name=defaults.ARF_LZ_NAME, lon=0.0, lat=0.0, mgrs="")
    return [*zones, virtual]


def _read_kml(path: Path) -> bytes:
    with zipfile.ZipFile(path) as archive:
        for name in archive.namelist():
            if name.lower().endswith(".kml"):
                return archive.read(name)
    raise FileNotFoundError(f"no KML inside {path}")


def _placemark_to_lz(placemark: ET.Element) -> LandingZone | None:
    name = (placemark.findtext("kml:name", default="", namespaces=KML_NS) or "").strip()
    if not name.upper().startswith("LZ "):
        return None
    coords = placemark.find(".//kml:Point/kml:coordinates", KML_NS)
    if coords is None or not (coords.text or "").strip():
        return None
    lon_s, lat_s, *_rest = coords.text.strip().split(",")
    lon, lat = float(lon_s), float(lat_s)
    return LandingZone(name=name, lon=lon, lat=lat, mgrs=to_mgrs(lat, lon))
