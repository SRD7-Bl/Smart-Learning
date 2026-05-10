"""User input signal hub for the Smart Learning frontend.

This module centralizes user-triggered signals. Rendering widgets send user
actions here first; later request-sending or backend-facing modules can connect
to this hub without coupling themselves to the window implementation.
"""

from __future__ import annotations

from Frontend.qt_compat import QObject, pyqtSignal


class UserInputModule(QObject):
    """Central relay for user actions from the frontend."""

    refresh_requested = pyqtSignal()
    login_requested = pyqtSignal(str, str)
    settings_requested = pyqtSignal()
    logout_requested = pyqtSignal()

    def request_refresh(self) -> None:
        self.refresh_requested.emit()

    def request_login(self, student_id: str, password: str) -> None:
        self.login_requested.emit(student_id.strip(), password)

    def request_settings(self) -> None:
        self.settings_requested.emit()

    def request_logout(self) -> None:
        self.logout_requested.emit()
