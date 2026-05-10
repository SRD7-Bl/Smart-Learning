"""Local data access module for Smart Learning.

The module reads JSON-formatted local data from the Storage layer and emits
signals for callers. Encryption is intentionally out of scope for this A4 step.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from Frontend.qt_compat import QObject, pyqtSignal


class DataAccessModule(QObject):
    """Read local user settings and academic information."""

    user_settings_loaded = pyqtSignal(dict)
    academic_info_loaded = pyqtSignal(dict)
    all_data_loaded = pyqtSignal(dict, dict)
    data_access_failed = pyqtSignal(str)

    def __init__(
        self,
        parent: QObject | None = None,
        storage_dir: Path | None = None,
    ) -> None:
        super().__init__(parent)
        self.storage_dir = storage_dir or Path(__file__).resolve().parents[1] / "Storage"
        self.user_settings_path = self.storage_dir / "User_setting.js"
        self.academic_info_path = self.storage_dir / "Academic_info.js"

    def request_user_settings(self) -> None:
        try:
            user_settings = self._read_json_file(self.user_settings_path)
        except ValueError as error:
            self.data_access_failed.emit(str(error))
            return

        print("DataAccessModule user settings:", user_settings)
        self.user_settings_loaded.emit(user_settings)

    def request_academic_info(self) -> None:
        try:
            academic_info = self._read_json_file(self.academic_info_path)
        except ValueError as error:
            self.data_access_failed.emit(str(error))
            return

        print("DataAccessModule academic info:", academic_info)
        self.academic_info_loaded.emit(academic_info)

    def request_all_data(self) -> None:
        try:
            user_settings = self._read_json_file(self.user_settings_path)
            academic_info = self._read_json_file(self.academic_info_path)
        except ValueError as error:
            self.data_access_failed.emit(str(error))
            return

        print("DataAccessModule user settings:", user_settings)
        print("DataAccessModule academic info:", academic_info)
        self.all_data_loaded.emit(user_settings, academic_info)

    def _read_json_file(self, path: Path) -> dict[str, Any]:
        if not path.exists():
            raise ValueError(f"Local data file does not exist: {path.name}")

        if path.stat().st_size == 0:
            raise ValueError(f"Local data file is empty: {path.name}")

        try:
            with path.open("r", encoding="utf-8") as data_file:
                data = json.load(data_file)
        except json.JSONDecodeError as error:
            raise ValueError(f"Local data file is not valid JSON: {path.name}") from error
        except OSError as error:
            raise ValueError(f"Local data file could not be read: {path.name}") from error

        if not isinstance(data, dict):
            raise ValueError(f"Local data file must contain a JSON object: {path.name}")

        return data
