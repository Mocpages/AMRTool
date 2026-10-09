from __future__ import annotations

import re
from pathlib import Path

import fitz

from amr_helper.imagery import PAGE3_SLOTS
from amr_helper.paths import template_path

OVERVIEW_SLOT = "Image2_af_image"
MANIFEST_PAGE = 3
_ROW_FIELD = re.compile(
    r"^(?:Rank|Last Name|Nationality|Service|Last 4 IDSSN|"
    r"PickUp Location|DropOff Location|\d+)Row\d+$"
)
_HEADER_FIELDS = (
    "Supported Unit POC",
    "Supported Unit POC Email",
    "Supported Unit POC Phone",
    "Supporting Unit POC",
    "Supporting Unit POC Email",
    "Supporting Unit POC Phone",
)


def fill_pdf(
    values: dict[str, str | bool],
    dest: Path,
    template: Path | None = None,
    lz_images: list[Path] | None = None,
    overview: Path | None = None,
    extra_manifest: list[dict[str, str]] | None = None,
) -> None:
    source = template or template_path()
    doc = fitz.open(source)
    try:
        _apply_values(doc, values)
        page = doc[2]
        if overview:
            _embed_named_image(page, OVERVIEW_SLOT, overview)
        if lz_images:
            _embed_page3_images(page, lz_images)
        if extra_manifest:
            _append_manifest_pages(doc, extra_manifest, source, values)
        dest.parent.mkdir(parents=True, exist_ok=True)
        doc.save(dest, incremental=False, encryption=fitz.PDF_ENCRYPT_NONE)
    finally:
        doc.close()


def _apply_values(doc: fitz.Document, values: dict[str, str | bool]) -> None:
    for page in doc:
        for widget in page.widgets() or []:
            name = widget.field_name
            if name not in values:
                continue
            _set_widget(widget, values[name])


def _set_widget(widget: fitz.Widget, value: str | bool) -> None:
    kind = widget.field_type_string
    if kind == "CheckBox":
        widget.field_value = _checkbox_value(widget, value)
    else:
        widget.field_value = value
    widget.update()


def _embed_page3_images(page: fitz.Page, image_paths: list[Path]) -> None:
    slots = [_take_widget_rect(page, name) for name in PAGE3_SLOTS]
    for rect, path in zip((r for r in slots if r is not None), image_paths):
        page.insert_image(rect, filename=str(path), keep_proportion=True, overlay=True)


def _embed_named_image(page: fitz.Page, name: str, path: Path) -> None:
    rect = _take_widget_rect(page, name)
    if rect is None:
        return
    page.insert_image(rect, filename=str(path), keep_proportion=True, overlay=True)


def _take_widget_rect(page: fitz.Page, name: str) -> fitz.Rect | None:
    for widget in page.widgets() or []:
        if widget.field_name != name:
            continue
        rect = fitz.Rect(widget.rect)
        page.delete_widget(widget)
        return rect
    return None


def _append_manifest_pages(
    doc: fitz.Document,
    extras: list[dict[str, str]],
    template: Path,
    values: dict[str, str | bool],
) -> None:
    headers = {name: str(values.get(name, "")) for name in _HEADER_FIELDS}
    for chunk in extras:
        baked = _build_baked_manifest_page(template, headers, chunk)
        try:
            doc.insert_pdf(baked)
        finally:
            baked.close()


def _build_baked_manifest_page(
    template: Path, headers: dict[str, str], chunk: dict[str, str]
) -> fitz.Document:
    """Fill a blank manifest page, then bake widgets so fields cannot merge."""
    source = fitz.open(template)
    overflow = fitz.open()
    try:
        overflow.insert_pdf(source, from_page=MANIFEST_PAGE, to_page=MANIFEST_PAGE)
    finally:
        source.close()
    page = overflow[0]
    combined = {**headers, **chunk}
    for widget in list(page.widgets() or []):
        name = widget.field_name or ""
        if name in combined:
            _set_widget(widget, combined[name])
        elif _ROW_FIELD.match(name):
            _set_widget(widget, "")
    overflow.bake(widgets=True)
    return overflow


def _checkbox_value(widget: fitz.Widget, value: str | bool) -> str | bool:
    on_state = widget.on_state() if callable(getattr(widget, "on_state", None)) else None
    if value in (True, "Yes", "On", on_state):
        return on_state if on_state is not None else True
    return False
