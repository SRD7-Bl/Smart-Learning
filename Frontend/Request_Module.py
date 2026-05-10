"""Request sending placeholder for the Smart Learning frontend."""

from __future__ import annotations

from Frontend.qt_compat import QObject, pyqtSignal


class RequestSendingModule(QObject):
    """Temporary request boundary for login and refresh actions."""

    request_queued = pyqtSignal(str)

    def send_login_request(self, student_id: str, password: str) -> None:
        self.request_queued.emit(f"Login request queued for {student_id}.")

    def send_refresh_request(self) -> None:
        self.request_queued.emit("Refresh request queued.")
