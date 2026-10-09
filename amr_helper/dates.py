from __future__ import annotations

from datetime import date

from amr_helper.defaults import LOCAL_UTC_OFFSET_HOURS

MONTHS = (
    "JAN", "FEB", "MAR", "APR", "MAY", "JUN",
    "JUL", "AUG", "SEP", "OCT", "NOV", "DEC",
)


def format_date(value: date) -> str:
    return f"{value.day:02d} {MONTHS[value.month - 1]} {value.strftime('%y')}"


def format_time(hhmm: str) -> str:
    return format_local_zulu(hhmm)


def hhmm_digits(text: str) -> str:
    return "".join(ch for ch in text if ch.isdigit())[:4]


def local_to_zulu(hhmm: str, on_date: date | None = None) -> str:
    digits = hhmm_digits(hhmm)
    minutes = int(digits[:2]) * 60 + int(digits[2:])
    zulu_minutes = (minutes - LOCAL_UTC_OFFSET_HOURS * 60) % (24 * 60)
    return f"{zulu_minutes // 60:02d}{zulu_minutes % 60:02d}"


def format_local_zulu(hhmm: str, on_date: date | None = None) -> str:
    if not is_hhmm(hhmm):
        return ""
    local = hhmm_digits(hhmm)
    return f"{local}L/{local_to_zulu(local, on_date)}Z"


def parse_date(text: str) -> date:
    parts = text.strip().upper().split()
    if len(parts) != 3:
        raise ValueError(f"expected DD MMM YY, got {text!r}")
    day = int(parts[0])
    try:
        month = MONTHS.index(parts[1][:3]) + 1
    except ValueError as exc:
        raise ValueError(f"unknown month in {text!r}") from exc
    year = 2000 + int(parts[2]) if len(parts[2]) == 2 else int(parts[2])
    return date(year, month, day)


def is_hhmm(text: str) -> bool:
    digits = "".join(ch for ch in text if ch.isdigit())
    if len(digits) != 4:
        return False
    hour, minute = int(digits[:2]), int(digits[2:])
    return 0 <= hour <= 23 and 0 <= minute <= 59
