"""Runtime storage paths for Smart Learning."""

from __future__ import annotations

import os
import sys
from pathlib import Path


APP_NAME = "Smart Learning"


def user_data_dir() -> Path:
    """Return the per-user application data directory for the current OS."""
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / APP_NAME

    if sys.platform.startswith("win"):
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata) / APP_NAME
        return Path.home() / "AppData" / "Roaming" / APP_NAME

    xdg_data_home = os.environ.get("XDG_DATA_HOME")
    if xdg_data_home:
        return Path(xdg_data_home) / APP_NAME
    return Path.home() / ".local" / "share" / APP_NAME


def default_storage_dir() -> Path:
    """Return the directory used for local mutable app storage."""
    return user_data_dir() / "Storage"
