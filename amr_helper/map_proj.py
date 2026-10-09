from __future__ import annotations

import math

from amr_helper.models import LandingZone

# WGS84 web mercator sphere (EPSG:3857).
_R = 6378137.0
_MAX_LAT = 85.0511287798


def lon_to_x(lon: float) -> float:
    return math.radians(lon) * _R


def lat_to_y(lat: float) -> float:
    clamped = max(min(lat, _MAX_LAT), -_MAX_LAT)
    return _R * math.log(math.tan(math.pi / 4 + math.radians(clamped) / 2))


def x_to_lon(x: float) -> float:
    return math.degrees(x / _R)


def y_to_lat(y: float) -> float:
    return math.degrees(2 * math.atan(math.exp(y / _R)) - math.pi / 2)


def padded_lonlat_bbox(
    zones: list[LandingZone],
    width: int,
    height: int,
    pad_frac: float = 0.20,
) -> tuple[float, float, float, float]:
    xs = [lon_to_x(zone.lon) for zone in zones]
    ys = [lat_to_y(zone.lat) for zone in zones]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    pad_x = (max_x - min_x) * pad_frac or 2500.0
    pad_y = (max_y - min_y) * pad_frac or 2500.0
    min_x, max_x = min_x - pad_x, max_x + pad_x
    min_y, max_y = min_y - pad_y, max_y + pad_y
    min_x, max_x, min_y, max_y = _fit_aspect(
        min_x, max_x, min_y, max_y, width / height
    )
    return x_to_lon(min_x), y_to_lat(min_y), x_to_lon(max_x), y_to_lat(max_y)


def _fit_aspect(
    min_x: float, max_x: float, min_y: float, max_y: float, aspect: float
) -> tuple[float, float, float, float]:
    span_x, span_y = max_x - min_x, max_y - min_y
    current = span_x / span_y
    if current < aspect:
        extra = (aspect * span_y - span_x) / 2
        return min_x - extra, max_x + extra, min_y, max_y
    extra = (span_x / aspect - span_y) / 2
    return min_x, max_x, min_y - extra, max_y + extra


class Projector:
    def __init__(
        self,
        bbox: tuple[float, float, float, float],
        width: int,
        height: int,
    ):
        west, south, east, north = bbox
        self.width = width
        self.height = height
        self.x0, self.y0 = lon_to_x(west), lat_to_y(south)
        self.x1, self.y1 = lon_to_x(east), lat_to_y(north)

    def xy(self, lon: float, lat: float) -> tuple[float, float]:
        mx, my = lon_to_x(lon), lat_to_y(lat)
        x = (mx - self.x0) / (self.x1 - self.x0) * self.width
        y = (self.y1 - my) / (self.y1 - self.y0) * self.height
        return x, y
