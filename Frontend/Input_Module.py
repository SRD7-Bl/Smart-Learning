"""User input coordinator for the Smart Learning frontend.

This module is the frontend gatekeeper for user actions. It performs light
validation and login-state checks before allowing requests to continue toward
the request-sending layer.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from Frontend.Request_Module import RequestSendingModule
from Frontend.qt_compat import QObject, pyqtSignal


class UserInputModule(QObject):
    """Central validation and dispatch layer for user actions."""

    content_access_changed = pyqtSignal(bool)
    auto_login_changed = pyqtSignal(bool)
    login_request_accepted = pyqtSignal(str, str)
    logout_requested = pyqtSignal()
    refresh_request_accepted = pyqtSignal()
    settings_requested = pyqtSignal()
    validation_failed = pyqtSignal(str)
    status_changed = pyqtSignal(str)

    def __init__(
        self,
        parent: QObject | None = None,
        settings_path: Path | None = None,
        request_module: RequestSendingModule | None = None,
    ) -> None:
        super().__init__(parent)
        self.settings_path = settings_path or self._default_settings_path()
        self.request_module = request_module or RequestSendingModule(self)
        self.is_logged_in = False
        self.auto_login_enabled = False
        self._connect_request_module()
        self._bootstrap_login_state()

    def _connect_request_module(self) -> None:
        self.login_request_accepted.connect(self.request_module.send_login_request)
        self.refresh_request_accepted.connect(self.request_module.send_refresh_request)
        self.request_module.login_succeeded.connect(self._handle_login_success)
        self.request_module.login_failed.connect(self._handle_login_failure)

    def request_login(self, student_id: str, password: str) -> None:
        student_id = student_id.strip()
        if not student_id:
            self.validation_failed.emit("Student ID is required before login.")
            return

        if not password:
            self.validation_failed.emit("Password is required before login.")
            return

        self.login_request_accepted.emit(student_id, password)
        self.status_changed.emit("Login request accepted. Waiting for backend check.")

    def request_settings(self) -> None:
        self.settings_requested.emit()

    def request_logout(self) -> None:
        self.is_logged_in = False
        self.auto_login_enabled = False
        self._write_auto_login(False)
        self.content_access_changed.emit(False)
        self.auto_login_changed.emit(False)
        self.logout_requested.emit()
        self.status_changed.emit("Logged out. Auto login is disabled.")

    def request_refresh(self) -> None:
        if not self.is_logged_in:
            self.validation_failed.emit("Please login before refreshing academic information.")
            return

        self.refresh_request_accepted.emit()
        self.status_changed.emit("Refresh request accepted.")

    def _handle_login_success(self, user_settings: dict) -> None:
        self.is_logged_in = True
        self.auto_login_enabled = True
        self._write_auto_login(True)
        self.content_access_changed.emit(True)
        self.auto_login_changed.emit(True)
        display_name = user_settings.get("student", {}).get("display_name", "student")
        self.status_changed.emit(f"Login succeeded for {display_name}. Auto login is enabled.")

    def _handle_login_failure(self, message: str) -> None:
        self.is_logged_in = False
        self.auto_login_enabled = False
        self._write_auto_login(False)
        self.content_access_changed.emit(False)
        self.auto_login_changed.emit(False)
        self.status_changed.emit(message)

    def _bootstrap_login_state(self) -> None:
        settings = self._read_settings()
        self.auto_login_enabled = bool(settings.get("auto_login", False))
        self.is_logged_in = self.auto_login_enabled

    def emit_initial_state(self) -> None:
        self.content_access_changed.emit(self.is_logged_in)
        self.auto_login_changed.emit(self.auto_login_enabled)
        if self.is_logged_in:
            self.status_changed.emit("Auto login is enabled. Showing local academic information.")
        else:
            self.status_changed.emit("Login is required before viewing academic information.")

    def _read_settings(self) -> dict[str, Any]:
        if not self.settings_path.exists() or self.settings_path.stat().st_size == 0:
            return {}

        try:
            with self.settings_path.open("r", encoding="utf-8") as settings_file:
                data = json.load(settings_file)
        except (OSError, json.JSONDecodeError):
            self.validation_failed.emit("User settings could not be read. Please login manually.")
            return {}

        return data if isinstance(data, dict) else {}

    def _write_auto_login(self, enabled: bool) -> None:
        settings = self._read_settings()
        settings["auto_login"] = enabled
        self.settings_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with self.settings_path.open("w", encoding="utf-8") as settings_file:
                json.dump(settings, settings_file, indent=2)
        except OSError:
            self.validation_failed.emit("Auto login setting could not be updated.")

    def _default_settings_path(self) -> Path:
        return Path(__file__).resolve().parents[1] / "Storage" / "User_setting.js"
