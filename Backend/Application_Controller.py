"""Application controller for Smart Learning backend workflow coordination."""

from __future__ import annotations

from Backend.Authentication import AuthenticationModule
from Backend.Data_Acquisition import InformationAcquisitionModule
from Backend.Data_Access import DataAccessModule
from Backend.Error_Handler import ErrorHandlingModule
from Backend.Parser import ParserModule
from Backend.Processer import DataProcessingModule
from Frontend.qt_compat import QObject, pyqtSignal


class ApplicationController(QObject):
    """Coordinate frontend requests and backend modules."""
    """信号插"""
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
        acquisition_module: InformationAcquisitionModule | None = None,
        parser_module: ParserModule | None = None,
        processor_module: DataProcessingModule | None = None,
        error_handler: ErrorHandlingModule | None = None,
    ) -> None:
        super().__init__(parent)
        self.data_access_module = data_access_module or DataAccessModule(self)
        self.authentication_module = authentication_module or AuthenticationModule(
            self,
            data_access_module=self.data_access_module,
        )
        self.acquisition_module = acquisition_module or InformationAcquisitionModule(self)
        self.parser_module = parser_module or ParserModule(self)
        self.processor_module = processor_module or DataProcessingModule(self)
        self.error_handler = error_handler or ErrorHandlingModule(self)
        self._pending_login_credentials: tuple[str, str] | None = None
        self._pending_refresh_mode = "both" """默认是both，也就是assignment + Schedule"""
        self._pending_schedule_day_count = 1
        self._pending_parsed_schedule: dict | None = None
        self._connect_modules()

    """连接插槽"""
    def _connect_modules(self) -> None:
        self.data_access_module.user_settings_loaded.connect(self._check_login_against_settings)
        self.data_access_module.data_access_failed.connect(self._handle_data_access_failure)
        self.authentication_module.authentication_succeeded.connect(self._run_refresh_pipeline)
        self.authentication_module.authentication_failed.connect(self.error_handler.handle_authentication_error)
        self.authentication_module.authentication_status.connect(self.controller_status.emit)
        self.acquisition_module.course_info_acquired.connect(self._handle_course_info_acquired)
        self.acquisition_module.schedule_info_acquired.connect(self._handle_schedule_info_acquired)
        self.acquisition_module.acquisition_failed.connect(self.error_handler.handle_pipeline_error)
        self.acquisition_module.acquisition_status.connect(self.controller_status.emit)
        self.parser_module.parsing_succeeded.connect(self._handle_parsed_course_info)
        self.parser_module.schedule_parsing_succeeded.connect(self._handle_parsed_schedule_info)
        self.parser_module.parsing_failed.connect(self.error_handler.handle_pipeline_error)
        self.parser_module.parsing_status.connect(self.controller_status.emit)
        self.processor_module.processing_succeeded.connect(self._finish_refresh)
        self.processor_module.processing_failed.connect(self.error_handler.handle_pipeline_error)
        self.processor_module.processing_status.connect(self.controller_status.emit)
        self.error_handler.error_ready.connect(self._handle_backend_error)

    def handle_login_request(self, student_id: str, password: str) -> None:
        self._pending_login_credentials = (student_id, password)
        self.controller_status.emit("AC received login request. Loading local user settings.")
        self.data_access_module.request_user_settings()

    def handle_refresh_request(self, refresh_mode: str = "both", schedule_day_count: int = 1) -> None:
        self._pending_refresh_mode = self._normalize_refresh_mode(refresh_mode)
        self._pending_schedule_day_count = self._normalize_schedule_day_count(schedule_day_count)
        self._pending_parsed_schedule = None
        self.controller_status.emit(f"AC received refresh request: {self._pending_refresh_mode}. Starting authentication.")
        self.authentication_module.request_authentication()

    def _check_login_against_settings(self, user_settings: dict) -> None:
        if self._pending_login_credentials is None:
            return

        student_id, password = self._pending_login_credentials
        self._pending_login_credentials = None
        auth_settings = user_settings.get("auth", {})
        expected_student_id = str(auth_settings.get("student_id", ""))
        expected_password = str(auth_settings.get("password", ""))
        """Basic login info. check"""
        if student_id == expected_student_id and password == expected_password:
            self.login_succeeded.emit(user_settings)
            self.controller_status.emit("Login credentials matched local user settings.")
            return

        self.login_failed.emit("Login failed: student ID or password does not match local settings.")

    def _run_refresh_pipeline(self, driver: object) -> None:
        refresh_mode = self._pending_refresh_mode
        """优先refresh schedule"""
        if refresh_mode == "schedule":
            self.controller_status.emit("Authentication succeeded. Acquiring schedule information.")
            self.acquisition_module.acquire_schedule_info(driver, day_count=self._pending_schedule_day_count)
            return
        """再refresh key academic info."""
        include_schedule = refresh_mode == "both"
        self.controller_status.emit("Authentication succeeded. Acquiring course information.")
        self.acquisition_module.acquire_course_info(
            driver,
            include_schedule=include_schedule,
            schedule_day_count=self._pending_schedule_day_count,
        )

    """处理schedule部分"""
    def _handle_schedule_info_acquired(self, schedule: dict) -> None:
        self.controller_status.emit("Schedule acquired. Parsing schedule information.")
        self.parser_module.parse_schedule_info(schedule)

    def _handle_parsed_schedule_info(self, schedule_info: dict) -> None:
        day_count = len(schedule_info.get("schedule_days", []))
        self.controller_status.emit(f"Parsed {day_count} schedule day(s).")
        if self._pending_refresh_mode == "both":
            self._pending_parsed_schedule = schedule_info
            return

        self.controller_status.emit("Running schedule data processing pipeline.")
        self.processor_module.process_academic_info(schedule_info)

    def _handle_course_info_acquired(self, courses: list) -> None:
        self.controller_status.emit(f"Acquired {len(courses)} course cards. Parsing course information.")
        self.parser_module.parse_course_info(courses)

    def _handle_parsed_course_info(self, academic_info: dict) -> None:
        course_count = len(academic_info.get("courses", []))
        self.controller_status.emit(f"Parsed {course_count} course(s). Running data processing pipeline.")
        if self._pending_parsed_schedule:
            academic_info = {
                **academic_info,
                "schedule_days": self._pending_parsed_schedule.get("schedule_days", []),
            }
            self._pending_parsed_schedule = None

        self.processor_module.process_academic_info(academic_info)

    def _finish_refresh(self, academic_info: dict) -> None:
        self.refresh_succeeded.emit(academic_info)
        self.controller_status.emit("Refresh pipeline completed.")
        self.authentication_module.close_driver()

    def _handle_data_access_failure(self, message: str) -> None:
        self.error_handler.handle_data_access_error(message)

    def _handle_backend_error(self, message: str) -> None:
        if self._pending_login_credentials is not None:
            self._pending_login_credentials = None
            self.login_failed.emit(message)
            return

        self._pending_parsed_schedule = None
        self.authentication_module.close_driver()
        self.refresh_failed.emit(message)

    def _normalize_refresh_mode(self, refresh_mode: str) -> str:
        if refresh_mode in {"assignments", "schedule", "both"}:
            return refresh_mode

        return "both"

    def _normalize_schedule_day_count(self, schedule_day_count: int) -> int:
        try:
            value = int(schedule_day_count)
        except (TypeError, ValueError):
            return 1

        return max(1, min(value, 31))
