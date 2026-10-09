from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from amr_helper.paths import config_path, default_csv_path, default_kmz_path


@dataclass
class AppConfig:
    csv_path: str = ""
    kmz_path: str = ""


def load_config() -> AppConfig:
    path = config_path()
    if not path.exists():
        return AppConfig()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return AppConfig()
    return AppConfig(
        csv_path=str(raw.get("csv_path") or ""),
        kmz_path=str(raw.get("kmz_path") or ""),
    )


def save_config(cfg: AppConfig) -> None:
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(cfg), indent=2), encoding="utf-8")


def get_csv_path() -> Path | None:
    text = load_config().csv_path.strip()
    if not text:
        return None
    path = Path(text)
    return path if path.is_file() else None


def get_kmz_path() -> Path | None:
    text = load_config().kmz_path.strip()
    if not text:
        return None
    path = Path(text)
    return path if path.is_file() else None


def set_csv_path(path: Path) -> None:
    cfg = load_config()
    cfg.csv_path = str(path.resolve())
    save_config(cfg)


def set_kmz_path(path: Path) -> None:
    cfg = load_config()
    cfg.kmz_path = str(path.resolve())
    save_config(cfg)


def needs_first_run_setup() -> bool:
    return get_csv_path() is None or get_kmz_path() is None


def seed_defaults_if_present() -> AppConfig:
    """Dev helper: if config is empty but repo defaults exist, remember them."""
    cfg = load_config()
    changed = False
    if not cfg.csv_path and default_csv_path().is_file():
        cfg.csv_path = str(default_csv_path().resolve())
        changed = True
    if not cfg.kmz_path and default_kmz_path().is_file():
        cfg.kmz_path = str(default_kmz_path().resolve())
        changed = True
    if changed:
        save_config(cfg)
    return cfg


def ensure_verify_paths() -> None:
    """Point config at repo defaults so tests run without a GUI first-run."""
    set_csv_path(default_csv_path())
    set_kmz_path(default_kmz_path())
