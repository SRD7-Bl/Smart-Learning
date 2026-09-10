"""Small PyQt compatibility layer for the Smart Learning frontend."""

try:
    from PyQt5.QtCore import QObject, Qt, pyqtSignal
    from PyQt5.QtWidgets import (
        QApplication,
        QCheckBox,
        QComboBox,
        QFrame,
        QGridLayout,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QInputDialog,
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
    MESSAGE_NO = QMessageBox.No
    MESSAGE_YES = QMessageBox.Yes
    NO_FRAME = QFrame.NoFrame
except ImportError:  # pragma: no cover - depends on the local PyQt install.
    from PyQt6.QtCore import QObject, Qt, pyqtSignal
    from PyQt6.QtWidgets import (
        QApplication,
        QCheckBox,
        QComboBox,
        QFrame,
        QGridLayout,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QInputDialog,
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
    MESSAGE_NO = QMessageBox.StandardButton.No
    MESSAGE_YES = QMessageBox.StandardButton.Yes
    NO_FRAME = QFrame.Shape.NoFrame
