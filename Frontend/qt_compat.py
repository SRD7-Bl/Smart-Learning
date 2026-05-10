"""Small PyQt compatibility layer for the Smart Learning frontend."""

try:
    from PyQt5.QtCore import QObject, Qt, pyqtSignal
    from PyQt5.QtWidgets import (
        QApplication,
        QFrame,
        QGridLayout,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QMainWindow,
        QMessageBox,
        QPushButton,
        QScrollArea,
        QSizePolicy,
        QSpacerItem,
        QTabWidget,
        QVBoxLayout,
        QWidget,
    )

    ECHO_PASSWORD = QLineEdit.Password
    EXPANDING_POLICY = QSizePolicy.Expanding
    NO_FRAME = QFrame.NoFrame
except ImportError:  # pragma: no cover - depends on the local PyQt install.
    from PyQt6.QtCore import QObject, Qt, pyqtSignal
    from PyQt6.QtWidgets import (
        QApplication,
        QFrame,
        QGridLayout,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QMainWindow,
        QMessageBox,
        QPushButton,
        QScrollArea,
        QSizePolicy,
        QSpacerItem,
        QTabWidget,
        QVBoxLayout,
        QWidget,
    )

    ECHO_PASSWORD = QLineEdit.EchoMode.Password
    EXPANDING_POLICY = QSizePolicy.Policy.Expanding
    NO_FRAME = QFrame.Shape.NoFrame
