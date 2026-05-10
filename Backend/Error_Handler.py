"""Backend error handling module for Smart Learning."""

from __future__ import annotations

from Frontend.qt_compat import QObject, pyqtSignal


class ErrorHandlingModule(QObject):
    """Normalize backend pipeline errors before returning them to the AC."""

    error_ready = pyqtSignal(str)

    def handle_pipeline_error(self, message: str) -> None:
        self.error_ready.emit(f"Pipeline error: {message}")

    def handle_authentication_error(self, message: str) -> None:
        self.error_ready.emit(f"Authentication error: {message}")

    def handle_data_access_error(self, message: str) -> None:
        self.error_ready.emit(f"Data access error: {message}")

    def handle_error(self, message: str) -> None:
        self.error_ready.emit(message)
