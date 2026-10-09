from __future__ import annotations

import math
from dataclasses import dataclass

from PIL import ImageDraw, ImageFont

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)


@dataclass
class LabelSpot:
    origin: tuple[float, float]
    box: tuple[float, float, float, float]
    anchor: tuple[float, float]


def font(size: int, bold: bool = True) -> ImageFont.ImageFont:
    names = (
        r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\segoeui.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    )
    for path in names:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def text_size(
    draw: ImageDraw.ImageDraw,
    text: str,
    used: ImageFont.ImageFont,
    stroke: int = 5,
):
    box = draw.textbbox((0, 0), text, font=used, stroke_width=stroke)
    return box[2] - box[0], box[3] - box[1]


def draw_halo_text(
    draw: ImageDraw.ImageDraw,
    xy: tuple[float, float],
    text: str,
    used: ImageFont.ImageFont,
    stroke: int = 5,
) -> None:
    draw.text(xy, text, font=used, fill=BLACK, stroke_width=stroke, stroke_fill=WHITE)


def draw_halo_line(
    draw: ImageDraw.ImageDraw,
    start: tuple[float, float],
    end: tuple[float, float],
    width: int = 2,
) -> None:
    draw.line([start, end], fill=WHITE, width=width + 8)
    draw.line([start, end], fill=BLACK, width=width)


def draw_halo_dot(draw: ImageDraw.ImageDraw, xy: tuple[float, float], radius: int = 5):
    x, y = xy
    glow = radius + 3
    draw.ellipse((x - glow, y - glow, x + glow, y + glow), fill=WHITE)
    draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=BLACK)


def draw_halo_arrow(
    draw: ImageDraw.ImageDraw,
    start: tuple[float, float],
    end: tuple[float, float],
    stem_width: float = 48,
    line_width: int = 6,
    halo_width: int = 11,
) -> None:
    """Axis of Advance — Aviation: crossed stem + open hollow head."""
    trimmed = _shorten(start, end, 14, 22)
    if trimmed is None:
        return
    a, tip = trimmed
    ux, uy = _unit(a, tip)
    px, py = -uy, ux
    head_len = stem_width * (2.0 / 3.0)
    stem_len = math.hypot(tip[0] - a[0], tip[1] - a[1]) - head_len
    if stem_len < 12:
        return
    base = (tip[0] - ux * head_len, tip[1] - uy * head_len)
    half = stem_width / 2.0
    head_half = stem_width
    s_hi = (a[0] + px * half, a[1] + py * half)
    s_lo = (a[0] - px * half, a[1] - py * half)
    e_hi = (base[0] + px * half, base[1] + py * half)
    e_lo = (base[0] - px * half, base[1] - py * half)
    left = (base[0] + px * head_half, base[1] + py * head_half)
    right = (base[0] - px * head_half, base[1] - py * head_half)
    # Crossed stem; open V; connectors join head corners to stem ends (stem stays open).
    segments = [
        (s_hi, e_lo),
        (s_lo, e_hi),
        (e_hi, left),
        (e_lo, right),
        (left, tip),
        (tip, right),
    ]
    _draw_halo_segments(draw, segments, line_width, halo_width)


def _draw_halo_segments(
    draw: ImageDraw.ImageDraw,
    segments: list[tuple[tuple[float, float], tuple[float, float]]],
    black_width: int,
    white_width: int,
) -> None:
    for a, b in segments:
        draw.line([a, b], fill=WHITE, width=white_width)
    for a, b in segments:
        draw.line([a, b], fill=BLACK, width=black_width)


def place_lz_labels(
    points: list[tuple[float, float]],
    sizes: list[tuple[float, float]],
    width: int,
    height: int,
) -> list[LabelSpot]:
    groups = _group_by_side(points, sizes, width, height)
    spots: list[LabelSpot | None] = [None] * len(points)
    for side, items in groups.items():
        placed = (
            _place_vertical(side, items, width, height)
            if side in ("left", "right")
            else _place_horizontal(side, items, width, height)
        )
        for index, spot in placed:
            spots[index] = spot
    return [spot for spot in spots if spot is not None]


def _group_by_side(points, sizes, width: int, height: int):
    cx, cy = width / 2, height / 2
    groups = {"left": [], "right": [], "top": [], "bottom": []}
    for index, (point, size) in enumerate(zip(points, sizes)):
        deg = math.degrees(math.atan2(point[1] - cy, point[0] - cx))
        groups[_side_for(deg)].append((index, point, size))
    return groups


def _side_for(deg: float) -> str:
    ad = abs(deg)
    if ad <= 70:
        return "right"
    if ad >= 110:
        return "left"
    if deg > 0:
        return "bottom"
    return "top"


def place_leg_label(
    start: tuple[float, float],
    end: tuple[float, float],
    size: tuple[float, float],
    occupied: list[tuple[float, float, float, float]],
    width: int,
    height: int,
) -> LabelSpot | None:
    tw, th = size
    mx, my = (start[0] + end[0]) / 2, (start[1] + end[1]) / 2
    ux, uy = _unit(start, end)
    px, py = -uy, ux
    for dist in (24, 40, 56, 72, -24, -40, -56, -72, 90, -90):
        origin = (mx + px * dist - tw / 2, my + py * dist - th / 2)
        box = _pad_box(origin, tw, th)
        if _fits(box, width, height) and not _hits(box, occupied):
            return LabelSpot(origin, box, (origin[0] + tw / 2, origin[1] + th / 2))
    return None


def _place_vertical(side: str, items, width: int, height: int, margin: float = 10.0):
    items = sorted(items, key=lambda it: it[1][1])
    packed = _spread(
        [it[2][1] for it in items],
        [it[1][1] - it[2][1] / 2 for it in items],
        margin,
        height - margin,
    )
    result = []
    for (index, point, (tw, th)), y in zip(items, packed):
        x = margin if side == "left" else width - margin - tw
        origin = (x, y)
        box = _pad_box(origin, tw, th)
        result.append((index, LabelSpot(origin, box, _box_anchor(box, point))))
    return result


def _place_horizontal(side: str, items, width: int, height: int, margin: float = 10.0):
    items = sorted(items, key=lambda it: it[1][0])
    packed = _spread(
        [it[2][0] for it in items],
        [it[1][0] - it[2][0] / 2 for it in items],
        margin,
        width - margin,
    )
    result = []
    for (index, point, (tw, th)), x in zip(items, packed):
        y = margin if side == "top" else height - margin - th
        origin = (x, y)
        box = _pad_box(origin, tw, th)
        result.append((index, LabelSpot(origin, box, _box_anchor(box, point))))
    return result


def _spread(
    sizes: list[float], desired: list[float], lo: float, hi: float, gap: float = 4.0
) -> list[float]:
    n = len(sizes)
    if n == 0:
        return []
    needed = sum(sizes) + gap * (n - 1)
    usable = hi - lo
    if needed >= usable:
        return _even_pack(sizes, lo, hi, gap)
    pos = []
    cursor = lo
    for size, want in zip(sizes, desired):
        start = max(want, cursor)
        pos.append(start)
        cursor = start + size + gap
    overflow = cursor - gap - hi
    if overflow > 0:
        pos = [p - overflow for p in pos]
        if pos[0] < lo:
            return _even_pack(sizes, lo, hi, gap)
    return pos


def _even_pack(sizes: list[float], lo: float, hi: float, gap: float) -> list[float]:
    cursor = lo
    pos = []
    extra = ((hi - lo) - (sum(sizes) + gap * (len(sizes) - 1))) / max(len(sizes), 1)
    extra = max(extra, 0)
    for size in sizes:
        pos.append(cursor)
        cursor += size + gap + extra
    return pos


def _shorten(start, end, start_pad: float, end_pad: float):
    dx, dy = end[0] - start[0], end[1] - start[1]
    length = math.hypot(dx, dy)
    if length < start_pad + end_pad + 8:
        return None
    ux, uy = dx / length, dy / length
    a = (start[0] + ux * start_pad, start[1] + uy * start_pad)
    b = (end[0] - ux * end_pad, end[1] - uy * end_pad)
    return a, b


def _unit(start, end) -> tuple[float, float]:
    dx, dy = end[0] - start[0], end[1] - start[1]
    length = math.hypot(dx, dy) or 1.0
    return dx / length, dy / length


def _pad_box(origin, tw: float, th: float, pad: float = 3.0):
    x, y = origin
    return (x - pad, y - pad, x + tw + pad, y + th + pad)


def _box_anchor(box, point):
    left, top, right, bottom = box
    ax = min(max(point[0], left), right)
    ay = min(max(point[1], top), bottom)
    return ax, ay


def _fits(box, width: int, height: int, margin: float = 6.0) -> bool:
    return (
        box[0] >= margin
        and box[1] >= margin
        and box[2] <= width - margin
        and box[3] <= height - margin
    )


def _hits(box, occupied) -> bool:
    return any(_overlap(box, other) for other in occupied)


def _overlap(a, b) -> bool:
    return a[0] < b[2] and a[2] > b[0] and a[1] < b[3] and a[3] > b[1]
