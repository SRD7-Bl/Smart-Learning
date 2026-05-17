"""Local data access module for Smart Learning."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from Backend.Encryption import EncryptionService
from Frontend.qt_compat import QObject, pyqtSignal


class DataAccessModule(QObject):
    """Read local user settings and academic information."""

    user_settings_loaded = pyqtSignal(dict)
    auth_credentials_loaded = pyqtSignal(str, str)
    academic_info_loaded = pyqtSignal(dict)
    all_data_loaded = pyqtSignal(dict, dict)
    data_access_failed = pyqtSignal(str)
    auth_credentials_updated = pyqtSignal()

    def __init__(
        self,
        parent: QObject | None = None,
        storage_dir: Path | None = None,
    ) -> None:
        super().__init__(parent)
        self.storage_dir = storage_dir or Path(__file__).resolve().parents[1] / "Storage"
        self.user_settings_path = self.storage_dir / "User_setting.js"
        self.academic_info_path = self.storage_dir / "Academic_info.js"
        self.encryption_service = EncryptionService(self.storage_dir / ".sl_key")

    def request_user_settings(self) -> None:
        try:
            user_settings = self._read_user_settings()
        except ValueError as error:
            self.data_access_failed.emit(str(error))
            return

        self._print_user_settings_summary(user_settings)
        self.user_settings_loaded.emit(user_settings)

    def request_auth_credentials(self) -> None:
        try:
            user_settings = self._read_user_settings()
            auth = user_settings.get("auth", {})
            student_id = str(auth.get("student_id", "")).strip()
            password = str(auth.get("password", ""))
        except ValueError as error:
            self.data_access_failed.emit(str(error))
            return

        if not student_id or not password:
            self.data_access_failed.emit("Local auth credentials are missing student ID or password.")
            return

        self._print_user_settings_summary(user_settings)
        self.auth_credentials_loaded.emit(student_id, password)

    def update_auth_credentials(self, username: str, password: str) -> None:
        username = username.strip()
        if not username or not password:
            self.data_access_failed.emit("Username and password are required.")
            return

        try:
            user_settings = self._read_user_settings()
            user_settings["auth"] = {
                "student_id": username,
                "password": password,
            }
            self._write_json_file(self.user_settings_path, self._encrypted_user_settings(user_settings))
        except ValueError as error:
            self.data_access_failed.emit(str(error))
            return

        self.auth_credentials_updated.emit()

    def request_academic_info(self) -> None:
        try:
            academic_info = self._read_academic_info()
        except ValueError as error:
            self.data_access_failed.emit(str(error))
            return

        self._print_academic_info_summary(academic_info)
        self.academic_info_loaded.emit(academic_info)

    def request_all_data(self) -> None:
        try:
            user_settings = self._read_user_settings()
            academic_info = self._read_academic_info()
        except ValueError as error:
            self.data_access_failed.emit(str(error))
            return

        self._print_user_settings_summary(user_settings)
        self._print_academic_info_summary(academic_info)
        self.all_data_loaded.emit(user_settings, academic_info)

    def encrypt_existing_storage(self) -> None:
        """Convert current local storage files to the encrypted MVP format."""
        try:
            user_settings = self._read_user_settings()
            academic_info = self._read_academic_info()
            self._write_json_file(self.user_settings_path, self._encrypted_user_settings(user_settings))
            self._write_json_file(self.academic_info_path, self._encrypted_academic_info(academic_info))
        except ValueError as error:
            self.data_access_failed.emit(str(error))

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

    def _read_user_settings(self) -> dict[str, Any]:
        user_settings = self._read_json_file(self.user_settings_path)
        encrypted_auth = user_settings.get("auth_encrypted")
        if encrypted_auth:
            user_settings["auth"] = self.encryption_service.decrypt_to_dict(str(encrypted_auth))

        return user_settings

    def _read_academic_info(self) -> dict[str, Any]:
        academic_info = self._read_json_file(self.academic_info_path)
        if academic_info.get("encrypted") is True:
            payload = academic_info.get("payload")
            if not isinstance(payload, str):
                raise ValueError("Encrypted academic info is missing its payload.")
            return self.encryption_service.decrypt_to_dict(payload)

        return academic_info

    def _encrypted_user_settings(self, user_settings: dict[str, Any]) -> dict[str, Any]:
        auth = user_settings.get("auth", {})
        if not isinstance(auth, dict):
            raise ValueError("User settings auth field must be a JSON object.")

        encrypted_settings = dict(user_settings)
        encrypted_settings.pop("auth", None)
        encrypted_settings["auth_encrypted"] = self.encryption_service.encrypt_dict(auth)
        encrypted_settings["encryption_version"] = 1
        return encrypted_settings

    def _encrypted_academic_info(self, academic_info: dict[str, Any]) -> dict[str, Any]:
        return {
            "encrypted": True,
            "encryption_version": 1,
            "payload": self.encryption_service.encrypt_dict(academic_info),
        }

    def _write_json_file(self, path: Path, data: dict[str, Any]) -> None:
        try:
            with path.open("w", encoding="utf-8") as data_file:
                json.dump(data, data_file, indent=2, ensure_ascii=False)
                data_file.write("\n")
        except OSError as error:
            raise ValueError(f"Local data file could not be written: {path.name}") from error

    def _print_user_settings_summary(self, user_settings: dict[str, Any]) -> None:
        student = user_settings.get("student", {})
        print(
            "DataAccessModule user settings loaded:",
            {
                "student_id": student.get("student_id", "Unknown"),
                "auto_login": user_settings.get("auto_login", False),
                "auth_encrypted": "auth_encrypted" in user_settings,
            },
        )

    def _print_academic_info_summary(self, academic_info: dict[str, Any]) -> None:
        print(
            "DataAccessModule academic info loaded:",
            {
                "student_name": academic_info.get("student_name", "Unknown"),
                "courses": len(academic_info.get("courses", [])),
                "schedule_days": len(academic_info.get("schedule_days", [])),
            },
        )
