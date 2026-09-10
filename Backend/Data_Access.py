"""Local data access module for Smart Learning."""

from __future__ import annotations

import json
import secrets
from pathlib import Path
from typing import Any

from Backend.Encryption import EncryptionService
from Backend.Storage_Paths import default_storage_dir
from Frontend.qt_compat import QObject, pyqtSignal


class DataAccessModule(QObject):
    """Read local user settings and academic information."""

    user_settings_loaded = pyqtSignal(dict)
    auth_credentials_loaded = pyqtSignal(str, str)
    academic_info_loaded = pyqtSignal(dict)
    all_data_loaded = pyqtSignal(dict, dict)
    data_access_failed = pyqtSignal(str)
    auth_credentials_updated = pyqtSignal()
    academic_info_saved = pyqtSignal()
    local_data_deleted = pyqtSignal()

    def __init__(
        self,
        parent: QObject | None = None,
        storage_dir: Path | None = None,
    ) -> None:
        super().__init__(parent)
        self.storage_dir = storage_dir or default_storage_dir()
        self.user_settings_path = self.storage_dir / "User_setting.js"
        self.academic_info_path = self.storage_dir / "Academic_info.js"
        self._ensure_storage_files()
        self.encryption_service = EncryptionService(self.storage_dir / ".sl_key")

    def request_user_settings(self) -> None:
        try:
            user_settings = self._read_user_settings()
        except ValueError as error:
            self.data_access_failed.emit(str(error))
            return

        self.user_settings_loaded.emit(user_settings)

    """获取登录信息"""
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

        self.auth_credentials_loaded.emit(student_id, password)

    """更新(用户修改了)登录信息"""
    def update_auth_credentials(
        self,
        username: str,
        password: str,
        current_password: str = "",
    ) -> None:
        username = username.strip()
        if not username or not password:
            self.data_access_failed.emit("Username and password are required.")
            return

        try:
            user_settings = self._read_user_settings()
            self._require_current_password(user_settings, current_password, allow_missing=True)
            user_settings["auth"] = {
                "student_id": username,
                "password": password,
            }
            self._write_json_file(self.user_settings_path, self._encrypted_user_settings(user_settings))
        except ValueError as error:
            self.data_access_failed.emit(str(error))
            return

        self.auth_credentials_updated.emit()

    def delete_local_data(self, current_password: str) -> None:
        """Delete stored credentials and cached academic information after password verification."""
        try:
            user_settings = self._read_user_settings()
            self._require_current_password(user_settings, current_password)
            self._clear_local_data()
        except ValueError as error:
            self.data_access_failed.emit(str(error))
            return

        self.local_data_deleted.emit()

    def reset_local_data(self) -> None:
        """Reset recoverable local data when the stored password is unavailable."""
        try:
            self._clear_local_data()
        except ValueError as error:
            self.data_access_failed.emit(str(error))
            return

        self.local_data_deleted.emit()

    """中转函数：获取学术信息"""
    def request_academic_info(self) -> None:
        try:
            academic_info = self._read_academic_info()
        except ValueError as error:
            self.data_access_failed.emit(str(error))
            return

        self.academic_info_loaded.emit(academic_info)

    def load_academic_info_snapshot(self) -> dict[str, Any]:
        return self._read_academic_info()
    
    """保存学术信息"""
    def save_academic_info(self, academic_info: dict[str, Any]) -> None:
        if not isinstance(academic_info, dict):
            self.data_access_failed.emit("Academic info must be a JSON object before saving.")
            return

        try:
            self._write_json_file(self.academic_info_path, self._encrypted_academic_info(academic_info))
        except ValueError as error:
            self.data_access_failed.emit(str(error))
            return

        self.academic_info_saved.emit()
    
    """调试函数：同时获取所有信息"""
    def request_all_data(self) -> None:
        try:
            user_settings = self._read_user_settings()
            academic_info = self._read_academic_info()
        except ValueError as error:
            self.data_access_failed.emit(str(error))
            return

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

    def _ensure_storage_files(self) -> None:
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        if not self.user_settings_path.exists() or self.user_settings_path.stat().st_size == 0:
            self._write_json_file(
                self.user_settings_path,
                {"auto_login": False, "is_first_use": True},
            )
        if not self.academic_info_path.exists() or self.academic_info_path.stat().st_size == 0:
            self._write_json_file(self.academic_info_path, {})

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

    """解密User Setting"""
    def _read_user_settings(self) -> dict[str, Any]:
        user_settings = self._read_json_file(self.user_settings_path)
        encrypted_auth = user_settings.get("auth_encrypted")
        if encrypted_auth:
            user_settings["auth"] = self.encryption_service.decrypt_to_dict(str(encrypted_auth))

        return user_settings

    """解密key academic info."""
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

    def _require_current_password(
        self,
        user_settings: dict[str, Any],
        supplied_password: str,
        allow_missing: bool = False,
    ) -> None:
        auth = user_settings.get("auth", {})
        if not isinstance(auth, dict):
            raise ValueError("Stored authentication information is invalid.")

        expected_password = str(auth.get("password", ""))
        if not expected_password:
            if allow_missing:
                return
            raise ValueError("No stored password is available to authorize this operation.")

        if not secrets.compare_digest(
            supplied_password.encode("utf-8"),
            expected_password.encode("utf-8"),
        ):
            raise ValueError("Current password is incorrect.")

    def _clear_local_data(self) -> None:
        self._write_json_file(
            self.user_settings_path,
            {"auto_login": False, "is_first_use": True},
        )
        self._write_json_file(self.academic_info_path, {})

    def _write_json_file(self, path: Path, data: dict[str, Any]) -> None:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("w", encoding="utf-8") as data_file:
                json.dump(data, data_file, indent=2, ensure_ascii=False)
                data_file.write("\n")
        except OSError as error:
            raise ValueError(f"Local data file could not be written: {path.name}") from error
