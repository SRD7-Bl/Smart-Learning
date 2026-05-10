"""Application controller for Smart Learning backend workflow coordination."""

from __future__ import annotations

from Backend.Authentication import AuthenticationModule
from Backend.Data_Access import DataAccessModule
from Backend.Processer import DataProcessingModule
from Frontend.qt_compat import QObject, pyqtSignal


class ApplicationController(QObject):
    """Coordinate frontend requests and backend modules."""

    login_succeeded = pyqtSignal(dict)
    login_failed = pyqtSignal(str)
    refresh_succeeded = pyqtSignal(dict)
    refresh_failed = pyqtSignal(str)
    controller_status = pyqtSignal(str)

    def __init__(
        self,
        parent: QObject | None = None,
        data_access_module: DataAccessModule | None = None,
        authentication_module: AuthenticationModule | None = None,
        processor_module: DataProcessingModule | None = None,
    ) -> None:
        super().__init__(parent)
        self.data_access_module = data_access_module or DataAccessModule(self)
        self.authentication_module = authentication_module or AuthenticationModule(self)
        self.processor_module = processor_module or DataProcessingModule(self)
        self._pending_login_credentials: tuple[str, str] | None = None
        self._connect_modules()

    def _connect_modules(self) -> None:
        self.data_access_module.user_settings_loaded.connect(self._check_login_against_settings)
        self.data_access_module.data_access_failed.connect(self._handle_data_access_failure)
        self.authentication_module.authentication_succeeded.connect(self._run_refresh_pipeline)
        self.authentication_module.authentication_failed.connect(self.refresh_failed.emit)
        self.processor_module.processing_succeeded.connect(self._finish_refresh)
        self.processor_module.processing_failed.connect(self.refresh_failed.emit)

    def handle_login_request(self, student_id: str, password: str) -> None:
        self._pending_login_credentials = (student_id, password)
        self.controller_status.emit("AC received login request. Loading local user settings.")
        self.data_access_module.request_user_settings()

    def handle_refresh_request(self) -> None:
        self.controller_status.emit("AC received refresh request. Starting authentication.")
        self.authentication_module.request_authentication()

    def _check_login_against_settings(self, user_settings: dict) -> None:
        if self._pending_login_credentials is None:
            return

        student_id, password = self._pending_login_credentials
        self._pending_login_credentials = None
        auth_settings = user_settings.get("auth", {})
        expected_student_id = str(auth_settings.get("student_id", ""))
        expected_password = str(auth_settings.get("password", ""))

        if student_id == expected_student_id and password == expected_password:
            self.login_succeeded.emit(user_settings)
            self.controller_status.emit("Login credentials matched local user settings.")
            return

        self.login_failed.emit("Login failed: student ID or password does not match local settings.")

    def _run_refresh_pipeline(self) -> None:
        self.controller_status.emit("Authentication succeeded. Running placeholder data pipeline.")
        self.processor_module.run_placeholder_pipeline()

    def _finish_refresh(self, academic_info: dict) -> None:
        self.refresh_succeeded.emit(academic_info)
        self.controller_status.emit("Refresh pipeline completed.")

    def _handle_data_access_failure(self, message: str) -> None:
        if self._pending_login_credentials is not None:
            self._pending_login_credentials = None
            self.login_failed.emit(message)
            return

        self.refresh_failed.emit(message)
