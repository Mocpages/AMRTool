from __future__ import annotations

import os
import sys
from pathlib import Path

TEMPLATE_NAME = "Current AMR Template (VER. 4.0 JUL26).pdf"
KMZ_NAME = "chosen-plt-map.kmz"
CSV_NAME = "Chosen Info - Sheet1 (1).csv"
LZ_IMAGES_DIR = "lz_images"
CONFIG_NAME = "config.json"
APP_DATA_NAME = "AMR Helper"


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def app_dir() -> Path:
    """Writable directory next to the exe (frozen) or the project root (dev)."""
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def resource_dir() -> Path:
    """Bundled read-only assets (PyInstaller _MEIPASS or project root)."""
    if is_frozen():
        return Path(getattr(sys, "_MEIPASS", app_dir()))
    return app_dir()


def user_data_dir() -> Path:
    base = Path(os.environ.get("LOCALAPPDATA", str(app_dir()))) / APP_DATA_NAME
    base.mkdir(parents=True, exist_ok=True)
    return base


def config_path() -> Path:
    return user_data_dir() / CONFIG_NAME


def template_path() -> Path:
    for root in (app_dir(), resource_dir()):
        candidate = root / TEMPLATE_NAME
        if candidate.exists():
            return candidate
    return resource_dir() / TEMPLATE_NAME


def default_kmz_path() -> Path:
    return app_dir() / KMZ_NAME


def default_csv_path() -> Path:
    return app_dir() / CSV_NAME


def kmz_path() -> Path:
    from amr_helper import config

    configured = config.get_kmz_path()
    if configured is not None:
        return configured
    return default_kmz_path()


def csv_path() -> Path:
    from amr_helper import config

    configured = config.get_csv_path()
    if configured is not None:
        return configured
    return default_csv_path()


def lz_images_dir() -> Path:
    folder = user_data_dir() / LZ_IMAGES_DIR
    folder.mkdir(parents=True, exist_ok=True)
    return folder


# Back-compat alias used by older call sites.
def project_root() -> Path:
    return app_dir()
