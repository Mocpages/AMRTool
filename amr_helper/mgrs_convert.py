"""WGS84 latitude/longitude to 10-digit MGRS."""

from __future__ import annotations

import math

WGS84_A = 6378137.0
WGS84_E2 = 6.6943799901413165e-3
UTM_K0 = 0.9996
UTM_E0 = 500000.0
LAT_BANDS = "CDEFGHJKLMNPQRSTUVWX"
COL_SETS = ("ABCDEFGH", "JKLMNPQR", "STUVWXYZ")
ROW_LETTERS = "ABCDEFGHJKLMNPQRSTUV"


def from_mgrs(text: str) -> tuple[float, float]:
    zone, band, col, row, east_m, north_m = _parse_mgrs(text)
    easting = _square_easting(zone, col) + east_m + 0.5
    northing = _square_northing(zone, band, row) + north_m + 0.5
    return _utm_to_latlon(zone, easting, northing, _is_south(band))


def to_mgrs(lat: float, lon: float) -> str:
    zone, easting, northing = _latlon_to_utm(lat, lon)
    band = _latitude_band(lat)
    col = _col_letter(zone, easting)
    row = _row_letter(zone, northing)
    e_m = int(easting) % 100000
    n_m = int(northing) % 100000
    return f"{zone:02d}{band} {col}{row} {e_m:05d} {n_m:05d}"


def _latitude_band(lat: float) -> str:
    if lat < -80 or lat > 84:
        raise ValueError(f"latitude {lat} is outside MGRS range")
    if lat >= 72:
        return "X"
    return LAT_BANDS[int((lat + 80) / 8)]


def _col_letter(zone: int, easting: float) -> str:
    letters = COL_SETS[(zone - 1) % 3]
    col = int(easting / 100000) - 1
    if col < 0 or col >= len(letters):
        raise ValueError("easting is outside the UTM 100 km grid")
    return letters[col]


def _row_letter(zone: int, northing: float) -> str:
    idx = int(northing / 100000) % 20
    if zone % 2 == 0:
        idx = (idx + 5) % 20
    return ROW_LETTERS[idx]


def _latlon_to_utm(lat: float, lon: float) -> tuple[int, float, float]:
    zone = int((lon + 180) / 6) + 1
    lat_rad = math.radians(lat)
    lon_rad = math.radians(lon)
    lon0 = math.radians((zone - 1) * 6 - 180 + 3)
    easting, northing = _utm_en(lat_rad, lon_rad, lon0)
    if lat < 0:
        northing += 10_000_000.0
    return zone, easting, northing


def _utm_en(lat_rad: float, lon_rad: float, lon0: float) -> tuple[float, float]:
    e2 = WGS84_E2
    ep2 = e2 / (1 - e2)
    sin_lat = math.sin(lat_rad)
    cos_lat = math.cos(lat_rad)
    n = WGS84_A / math.sqrt(1 - e2 * sin_lat * sin_lat)
    t = math.tan(lat_rad) ** 2
    c = ep2 * cos_lat * cos_lat
    a = cos_lat * (lon_rad - lon0)
    m = _meridian_arc(lat_rad)
    easting = _easting(n, t, c, a, ep2)
    northing = _northing(m, n, lat_rad, t, c, a, ep2)
    return easting, northing


def _meridian_arc(lat_rad: float) -> float:
    e2 = WGS84_E2
    e4 = e2 * e2
    e6 = e4 * e2
    return WGS84_A * (
        (1 - e2 / 4 - 3 * e4 / 64 - 5 * e6 / 256) * lat_rad
        - (3 * e2 / 8 + 3 * e4 / 32 + 45 * e6 / 1024) * math.sin(2 * lat_rad)
        + (15 * e4 / 256 + 45 * e6 / 1024) * math.sin(4 * lat_rad)
        - (35 * e6 / 3072) * math.sin(6 * lat_rad)
    )


def _easting(n: float, t: float, c: float, a: float, ep2: float) -> float:
    a3 = a**3
    a5 = a**5
    term = a + (1 - t + c) * a3 / 6
    term += (5 - 18 * t + t * t + 72 * c - 58 * ep2) * a5 / 120
    return UTM_K0 * n * term + UTM_E0


def _parse_mgrs(text: str) -> tuple[int, str, str, str, int, int]:
    compact = "".join(ch for ch in text.upper() if ch.isalnum())
    if len(compact) < 7:
        raise ValueError(f"invalid MGRS: {text!r}")
    zone = int(compact[:2])
    digits = compact[5:]
    if len(digits) % 2:
        raise ValueError(f"invalid MGRS digits: {text!r}")
    half = len(digits) // 2
    east_m = int(digits[:half].ljust(5, "0")[:5])
    north_m = int(digits[half:].ljust(5, "0")[:5])
    return zone, compact[2], compact[3], compact[4], east_m, north_m


def _square_easting(zone: int, col_letter: str) -> float:
    letters = COL_SETS[(zone - 1) % 3]
    return (letters.index(col_letter) + 1) * 100000.0


def _square_northing(zone: int, band: str, row_letter: str) -> float:
    target = ROW_LETTERS.index(row_letter)
    lat_min, lat_max = _band_limits(band)
    for cycle in range(100):
        if _row_index(zone, cycle) != target:
            continue
        base = cycle * 100000.0
        lat, _lon = _utm_to_latlon(zone, UTM_E0, base + 50000.0, _is_south(band))
        if lat_min <= lat < lat_max:
            return base
    raise ValueError(f"no 100 km row {row_letter} in band {band}")


def _row_index(zone: int, cycle: int) -> int:
    idx = cycle % 20
    if zone % 2 == 0:
        idx = (idx + 5) % 20
    return idx


def _band_limits(band: str) -> tuple[float, float]:
    if band == "X":
        return 72.0, 84.1
    idx = LAT_BANDS.index(band)
    south = -80.0 + idx * 8
    return south, south + 8


def _is_south(band: str) -> bool:
    return LAT_BANDS.index(band) < LAT_BANDS.index("N")


def _utm_to_latlon(
    zone: int, easting: float, northing: float, southern: bool
) -> tuple[float, float]:
    if southern:
        northing -= 10_000_000.0
    x = easting - UTM_E0
    e2 = WGS84_E2
    ep2 = e2 / (1 - e2)
    m = northing / UTM_K0
    mu = m / (WGS84_A * (1 - e2 / 4 - 3 * e2**2 / 64 - 5 * e2**3 / 256))
    fp = _footprint_lat(mu, e2)
    lat_rad = _utm_lat(x, fp, e2, ep2)
    lon_rad = _utm_lon(x, fp, e2, ep2)
    lon0 = math.radians((zone - 1) * 6 - 180 + 3)
    return math.degrees(lat_rad), math.degrees(lon0 + lon_rad)


def _footprint_lat(mu: float, e2: float) -> float:
    e1 = (1 - math.sqrt(1 - e2)) / (1 + math.sqrt(1 - e2))
    return (
        mu
        + (3 * e1 / 2 - 27 * e1**3 / 32) * math.sin(2 * mu)
        + (21 * e1**2 / 16 - 55 * e1**4 / 32) * math.sin(4 * mu)
        + (151 * e1**3 / 96) * math.sin(6 * mu)
    )


def _utm_lon(x: float, fp: float, e2: float, ep2: float) -> float:
    sin_fp = math.sin(fp)
    cos_fp = math.cos(fp)
    n1 = WGS84_A / math.sqrt(1 - e2 * sin_fp * sin_fp)
    t1 = math.tan(fp) ** 2
    c1 = ep2 * cos_fp * cos_fp
    d = x / (n1 * UTM_K0)
    term = d - (1 + 2 * t1 + c1) * d**3 / 6
    term += (5 - 2 * c1 + 28 * t1 - 3 * c1**2 + 8 * ep2 + 24 * t1**2) * d**5 / 120
    return term / cos_fp


def _utm_lat(x: float, fp: float, e2: float, ep2: float) -> float:
    sin_fp = math.sin(fp)
    cos_fp = math.cos(fp)
    tan_fp = math.tan(fp)
    n1 = WGS84_A / math.sqrt(1 - e2 * sin_fp * sin_fp)
    t1 = tan_fp * tan_fp
    c1 = ep2 * cos_fp * cos_fp
    r1 = WGS84_A * (1 - e2) / (1 - e2 * sin_fp * sin_fp) ** 1.5
    d = x / (n1 * UTM_K0)
    d2, d4, d6 = d**2, d**4, d**6
    term = d2 / 2 - (5 + 3 * t1 + 10 * c1 - 4 * c1 * c1 - 9 * ep2) * d4 / 24
    term += (61 + 90 * t1 + 298 * c1 + 45 * t1 * t1 - 252 * ep2 - 3 * c1 * c1) * d6 / 720
    return fp - (n1 * tan_fp / r1) * term


def _northing(
    m: float, n: float, lat_rad: float, t: float, c: float, a: float, ep2: float
) -> float:
    a2 = a**2
    a4 = a**4
    a6 = a**6
    term = a2 / 2 + (5 - t + 9 * c + 4 * c * c) * a4 / 24
    term += (61 - 58 * t + t * t + 600 * c - 330 * ep2) * a6 / 720
    return UTM_K0 * (m + n * math.tan(lat_rad) * term)
