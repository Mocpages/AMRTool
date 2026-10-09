from __future__ import annotations

import math
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from io import BytesIO
from pathlib import Path
from urllib.request import Request, urlopen

from PIL import Image, ImageDraw, ImageFont

from amr_helper.defaults import is_arf_lz
from amr_helper.models import LandingZone
from amr_helper.paths import lz_images_dir

EXPORT_URL = (
    "https://services.arcgisonline.com/ArcGIS/rest/services/"
    "World_Imagery/MapServer/export"
)
METERS = 250
PIXELS = 512
PAGE3_SLOTS = ("Image13_af_image", "Image14_af_image", "Image15_af_image")
ProgressFn = Callable[[int, int, str], None]


def image_path_for(name: str, dest_dir: Path | None = None) -> Path:
    folder = dest_dir or lz_images_dir()
    safe = "".join(ch if ch.isalnum() else "_" for ch in name).strip("_")
    return folder / f"{safe}.jpg"


def missing_lz_images(
    zones: list[LandingZone], dest_dir: Path | None = None
) -> list[LandingZone]:
    folder = dest_dir or lz_images_dir()
    return [
        zone
        for zone in zones
        if _has_imagery(zone) and not image_path_for(zone.name, folder).exists()
    ]


def ensure_lz_images(
    zones: list[LandingZone],
    dest_dir: Path | None = None,
    on_progress: ProgressFn | None = None,
) -> dict[str, Path]:
    folder = dest_dir or lz_images_dir()
    folder.mkdir(parents=True, exist_ok=True)
    mappable = [zone for zone in zones if _has_imagery(zone)]
    _fetch_missing(mappable, folder, on_progress)
    saved = {}
    for zone in mappable:
        path = image_path_for(zone.name, folder)
        if path.exists():
            saved[zone.name] = path
    return saved


def _has_imagery(zone: LandingZone) -> bool:
    return bool(zone.mgrs) and not is_arf_lz(zone.name)


def _fetch_missing(
    zones: list[LandingZone],
    folder: Path,
    on_progress: ProgressFn | None,
) -> None:
    missing = [
        zone for zone in zones if not image_path_for(zone.name, folder).exists()
    ]
    if not missing:
        return
    total = len(missing)
    done = 0
    with ThreadPoolExecutor(max_workers=6) as pool:
        jobs = {
            pool.submit(save_lz_image, zone, image_path_for(zone.name, folder)): zone
            for zone in missing
        }
        for future in as_completed(jobs):
            zone = jobs[future]
            try:
                future.result()
            except Exception as exc:
                print(f"skip {zone.name}: {exc}")
            done += 1
            if on_progress:
                on_progress(done, total, zone.name)


def save_lz_image(zone: LandingZone, dest: Path) -> Path:
    raw = _download_chip(zone.lat, zone.lon)
    image = _caption(raw, zone.name)
    dest.parent.mkdir(parents=True, exist_ok=True)
    image.save(dest, format="JPEG", quality=90)
    return dest


def route_images(
    lz_names: list[str], saved: dict[str, Path], limit: int = 3
) -> list[Path]:
    paths: list[Path] = []
    for name in lz_names:
        if is_arf_lz(name):
            continue
        path = saved.get(name)
        if path is None or not path.exists():
            continue
        paths.append(path)
        if len(paths) >= limit:
            break
    return paths


def download_extent(
    west: float,
    south: float,
    east: float,
    north: float,
    width: int,
    height: int,
    timeout: int = 20,
) -> bytes:
    query = (
        f"{EXPORT_URL}?bbox={west},{south},{east},{north}"
        f"&bboxSR=4326&imageSR=3857&size={width},{height}"
        f"&format=jpg&f=image"
    )
    request = Request(query, headers={"User-Agent": "AMR-Helper/1.0"})
    with urlopen(request, timeout=timeout) as response:
        data = response.read()
    if len(data) < 1000:
        raise RuntimeError("satellite image response was empty")
    return data


def _download_chip(lat: float, lon: float) -> bytes:
    west, south, east, north = _bbox_250m(lat, lon)
    return download_extent(west, south, east, north, PIXELS, PIXELS)


def _bbox_250m(lat: float, lon: float) -> tuple[float, float, float, float]:
    half = METERS / 2.0
    m_per_deg_lat = 111_320.0
    m_per_deg_lon = 111_320.0 * math.cos(math.radians(lat))
    dlat = half / m_per_deg_lat
    dlon = half / m_per_deg_lon
    return lon - dlon, lat - dlat, lon + dlon, lat + dlat


def _caption(raw: bytes, title: str) -> Image.Image:
    image = Image.open(BytesIO(raw)).convert("RGB")
    draw = ImageDraw.Draw(image)
    width, height = image.size
    bar = max(36, height // 9)
    draw.rectangle((0, height - bar, width, height), fill=(0, 0, 0))
    font = _font(max(18, bar // 2))
    text_w, text_h = _text_size(draw, title, font)
    x = max(8, (width - text_w) / 2)
    y = height - bar + max(4, (bar - text_h) / 2)
    draw.text((x, y), title, fill=(255, 255, 255), font=font)
    return image


def _font(size: int) -> ImageFont.ImageFont:
    for path in (
        r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\segoeui.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ):
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _text_size(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont):
    box = draw.textbbox((0, 0), text, font=font)
    return box[2] - box[0], box[3] - box[1]


if __name__ == "__main__":
    from amr_helper.kmz_lzs import load_landing_zones

    paths = ensure_lz_images(load_landing_zones())
    print(f"saved {len(paths)} LZ images to {lz_images_dir()}")

