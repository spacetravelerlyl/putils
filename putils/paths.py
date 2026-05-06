from __future__ import annotations

import json
import os
import sys
from pathlib import Path


APP_NAME = "PUtils"
LOCATOR_FILE = "data_dir.json"


def default_user_data_dir() -> Path:
    if sys.platform.startswith("win"):
        root = os.environ.get("APPDATA")
        if root:
            return Path(root) / APP_NAME
        return Path.home() / "AppData" / "Roaming" / APP_NAME

    xdg_data_home = os.environ.get("XDG_DATA_HOME")
    if xdg_data_home:
        return Path(xdg_data_home) / "putils"
    return Path.home() / ".local" / "share" / "putils"


def locator_path() -> Path:
    return default_user_data_dir() / LOCATOR_FILE


def read_configured_data_dir() -> Path | None:
    path = locator_path()
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    configured = data.get("data_dir")
    if not isinstance(configured, str) or not configured.strip():
        return None
    return Path(configured).expanduser().resolve()


def write_configured_data_dir(data_dir: Path) -> None:
    path = locator_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"data_dir": str(data_dir.expanduser().resolve())}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def user_data_dir() -> Path:
    override = os.environ.get("PUTILS_DATA_DIR")
    if override:
        return Path(override).expanduser().resolve()

    configured = read_configured_data_dir()
    if configured is not None:
        return configured

    return default_user_data_dir()


def ensure_data_dir() -> Path:
    data_dir = user_data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def config_db_path() -> Path:
    return ensure_data_dir() / "config.sqlite3"


def log_db_path() -> Path:
    return ensure_data_dir() / "logs.sqlite3"


def bundled_plugins_dir() -> Path:
    return Path(__file__).resolve().parent / "plugins"
