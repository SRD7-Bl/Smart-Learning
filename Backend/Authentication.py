"""Authentication module placeholder for Smart Learning."""

from __future__ import annotations

from Frontend.qt_compat import QObject, pyqtSignal


class AuthenticationModule(QObject):
    """Placeholder for future TigerNet authentication automation."""

    authentication_succeeded = pyqtSignal()
    authentication_failed = pyqtSignal(str)

    def request_authentication(self) -> None:
        self.authentication_succeeded.emit()
