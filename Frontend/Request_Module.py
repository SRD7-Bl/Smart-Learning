"""Request sending module for the Smart Learning frontend."""

from __future__ import annotations

from Backend.Application_Controller import ApplicationController
from Frontend.qt_compat import QObject, pyqtSignal


class RequestSendingModule(QObject):
    """Forward accepted frontend requests to the application controller."""

    request_queued = pyqtSignal(str)
    request_failed = pyqtSignal(str)
    login_succeeded = pyqtSignal(dict)
    login_failed = pyqtSignal(str)
    refresh_succeeded = pyqtSignal(dict)
    refresh_failed = pyqtSignal(str)

    def __init__(
        self,
        parent: QObject | None = None,
        application_controller: ApplicationController | None = None,
    ) -> None:
        super().__init__(parent)
        self.application_controller = application_controller or ApplicationController(self)
        self._connect_application_controller()

    def _connect_application_controller(self) -> None:
        self.application_controller.controller_status.connect(self.request_queued.emit)
        self.application_controller.login_succeeded.connect(self.login_succeeded.emit)
        self.application_controller.login_failed.connect(self.request_failed.emit)
        self.application_controller.login_failed.connect(self.login_failed.emit)
        self.application_controller.refresh_succeeded.connect(self.refresh_succeeded.emit)
        self.application_controller.refresh_failed.connect(self.request_failed.emit)
        self.application_controller.refresh_failed.connect(self.refresh_failed.emit)

    def send_login_request(self, student_id: str, password: str) -> None:
        self.request_queued.emit(f"RS forwarding login request for {student_id}.")
        self.application_controller.handle_login_request(student_id, password)

    def send_refresh_request(self) -> None:
        self.request_queued.emit("RS forwarding refresh request.")
        self.application_controller.handle_refresh_request()
