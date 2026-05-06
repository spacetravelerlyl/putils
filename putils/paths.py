from __future__ import annotations

import os
import sys
from pathlib import Path


APP_NAME = "PUtils"


def user_data_dir() -> Path:
    override = os.environ.get("PUTILS_DATA_DIR")
    if override:
        return Path(override).expanduser().resolve()

    if sys.platform.startswith("win"):
        root = os.environ.get("APPDATA")
        if root:
            return Path(root) / APP_NAME
        return Path.home() / "AppData" / "Roaming" / APP_NAME

    xdg_data_home = os.environ.get("XDG_DATA_HOME")
    if xdg_data_home:
        return Path(xdg_data_home) / "putils"
    return Path.home() / ".local" / "share" / "putils"


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

