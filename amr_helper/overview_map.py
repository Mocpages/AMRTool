from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

from amr_helper.imagery import download_extent
from amr_helper.map_overlay import (
    draw_halo_arrow,
    draw_halo_dot,
    draw_halo_line,
    draw_halo_text,
    font,
    place_leg_label,
    place_lz_labels,
    text_size,
)
from amr_helper.defaults import is_arf_lz, touches_arf
from amr_helper.map_proj import Projector, padded_lonlat_bbox
from amr_helper.models import LandingZone, Leg
from amr_helper.paths import lz_images_dir

# Matches Image2_af_image on the CONOP page (~329.7 x 319.3 pt).
WIDTH, HEIGHT = 1648, 1596
PAD_FRAC = 0.20


def build_overview(
    zones: list[LandingZone],
    legs: list[Leg],
    dest_dir: Path | None = None,
) -> Path:
    folder = dest_dir or lz_images_dir()
    folder.mkdir(parents=True, exist_ok=True)
    used = _used_zones(zones, legs)
    if not used:
        raise RuntimeError("no landing zones on the route")
    bbox = padded_lonlat_bbox(used, WIDTH, HEIGHT, pad_frac=PAD_FRAC)
    base = _ensure_base(bbox, folder)
    image = _draw_overlays(base, used, legs, bbox)
    dest = folder / "overview.jpg"
    image.save(dest, format="JPEG", quality=90)
    return dest


def _used_zones(zones: list[LandingZone], legs: list[Leg]) -> list[LandingZone]:
    by_name = {zone.name: zone for zone in zones}
    used: list[LandingZone] = []
    seen: set[str] = set()
    for leg in legs:
        if touches_arf(leg.start_lz, leg.end_lz):
            continue
        for name in (leg.start_lz, leg.end_lz):
            if not name or is_arf_lz(name) or name in seen or name not in by_name:
                continue
            seen.add(name)
            used.append(by_name[name])
    return used


def _ensure_base(
    bbox: tuple[float, float, float, float], folder: Path
) -> Image.Image:
    path = _base_path(folder, bbox)
    if path.exists():
        image = Image.open(path).convert("RGB")
        if image.size == (WIDTH, HEIGHT):
            return image
    raw = download_extent(*bbox, WIDTH, HEIGHT, timeout=45)
    tmp = path.with_suffix(".tmp.jpg")
    tmp.write_bytes(raw)
    tmp.replace(path)
    return Image.open(path).convert("RGB")


def _base_path(folder: Path, bbox: tuple[float, float, float, float]) -> Path:
    west, south, east, north = bbox
    key = f"{west:.4f}_{south:.4f}_{east:.4f}_{north:.4f}"
    return folder / f"overview_base_{key}.jpg"


def _draw_overlays(
    base: Image.Image,
    zones: list[LandingZone],
    legs: list[Leg],
    bbox: tuple[float, float, float, float],
) -> Image.Image:
    image = base.copy()
    draw = ImageDraw.Draw(image)
    proj = Projector(bbox, WIDTH, HEIGHT)
    by_name = {zone.name: zone for zone in zones}
    points = [proj.xy(zone.lon, zone.lat) for zone in zones]
    routes = _leg_pixels(legs, by_name, proj)
    for _label, start, end in routes:
        draw_halo_arrow(draw, start, end)
    occupied = _draw_lz_marks(draw, zones, points)
    _draw_leg_labels(draw, routes, occupied)
    return image


def _leg_pixels(
    legs: list[Leg],
    by_name: dict[str, LandingZone],
    proj: Projector,
) -> list[tuple[str, tuple[float, float], tuple[float, float]]]:
    groups: dict[tuple[str, str], list[int]] = {}
    order: list[tuple[str, str]] = []
    for index, leg in enumerate(legs, start=1):
        if touches_arf(leg.start_lz, leg.end_lz):
            continue
        start_z, end_z = by_name.get(leg.start_lz), by_name.get(leg.end_lz)
        if start_z is None or end_z is None:
            continue
        key = (leg.start_lz, leg.end_lz)
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append(index)
    routes = []
    for start_name, end_name in order:
        start_z, end_z = by_name[start_name], by_name[end_name]
        label = ",".join(str(n) for n in groups[(start_name, end_name)])
        routes.append(
            (label, proj.xy(start_z.lon, start_z.lat), proj.xy(end_z.lon, end_z.lat))
        )
    return routes


def _draw_lz_marks(
    draw: ImageDraw.ImageDraw,
    zones: list[LandingZone],
    points: list[tuple[float, float]],
) -> list[tuple[float, float, float, float]]:
    used = font(34)
    sizes = [text_size(draw, zone.name, used) for zone in zones]
    spots = place_lz_labels(points, sizes, WIDTH, HEIGHT)
    occupied = []
    for point, zone, spot in zip(points, zones, spots):
        draw_halo_line(draw, spot.anchor, point, width=3)
        draw_halo_dot(draw, point, radius=8)
        draw_halo_text(draw, spot.origin, zone.name, used, stroke=5)
        occupied.append(spot.box)
        occupied.append((point[0] - 14, point[1] - 14, point[0] + 14, point[1] + 14))
    return occupied


def _draw_leg_labels(
    draw: ImageDraw.ImageDraw,
    routes: list[tuple[str, tuple[float, float], tuple[float, float]]],
    occupied: list[tuple[float, float, float, float]],
) -> None:
    used = font(42)
    for numbers, start, end in routes:
        label = f"Leg {numbers}"
        spot = place_leg_label(
            start, end, text_size(draw, label, used), occupied, WIDTH, HEIGHT
        )
        if spot is None:
            continue
        draw_halo_text(draw, spot.origin, label, used, stroke=5)
        occupied.append(spot.box)


if __name__ == "__main__":
    from amr_helper.kmz_lzs import load_landing_zones

    sample = [
        Leg(start_lz="LZ APACHE", end_lz="LZ CALI"),
        Leg(start_lz="LZ CALI", end_lz="LZ BAKER"),
    ]
    path = build_overview(load_landing_zones(), sample)
    print(f"wrote {path}")
