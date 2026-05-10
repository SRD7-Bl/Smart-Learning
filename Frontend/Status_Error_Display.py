"""Frontend status and error display module for Smart Learning."""

from __future__ import annotations

from Frontend.qt_compat import QMessageBox, QObject, pyqtSignal


class StatusErrorDisplayModule(QObject):
    """Display status text and user-visible error popups."""

    status_ready = pyqtSignal(str)

    def __init__(self, parent: QObject | None = None, dialog_parent: object | None = None) -> None:
        super().__init__(parent)
        self.dialog_parent = dialog_parent

    def set_dialog_parent(self, dialog_parent: object) -> None:
        self.dialog_parent = dialog_parent

    def display_status(self, message: str) -> None:
        self.status_ready.emit(message)

    def display_error(self, message: str) -> None:
        QMessageBox.information(self.dialog_parent, "Smart Learning", message)
