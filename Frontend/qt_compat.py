"""Small PyQt compatibility layer for the Smart Learning frontend."""

try:
    from PyQt5.QtCore import QDate, QObject, Qt, pyqtSignal
    from PyQt5.QtGui import QColor, QTextCharFormat
    from PyQt5.QtWidgets import (
        QApplication,
        QCalendarWidget,
        QCheckBox,
        QComboBox,
        QDialog,
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

    ECHO_NORMAL = QLineEdit.Normal
    ECHO_PASSWORD = QLineEdit.Password
    EXPANDING_POLICY = QSizePolicy.Expanding
    MESSAGE_NO = QMessageBox.No
    MESSAGE_YES = QMessageBox.Yes
    NO_FRAME = QFrame.NoFrame
    CALENDAR_NO_VERTICAL_HEADER = QCalendarWidget.NoVerticalHeader
    WEEKDAY_VALUES = (
        Qt.Monday,
        Qt.Tuesday,
        Qt.Wednesday,
        Qt.Thursday,
        Qt.Friday,
        Qt.Saturday,
        Qt.Sunday,
    )
except ImportError:  # pragma: no cover - depends on the local PyQt install.
    from PyQt6.QtCore import QDate, QObject, Qt, pyqtSignal
    from PyQt6.QtGui import QColor, QTextCharFormat
    from PyQt6.QtWidgets import (
        QApplication,
        QCalendarWidget,
        QCheckBox,
        QComboBox,
        QDialog,
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

    ECHO_NORMAL = QLineEdit.EchoMode.Normal
    ECHO_PASSWORD = QLineEdit.EchoMode.Password
    EXPANDING_POLICY = QSizePolicy.Policy.Expanding
    MESSAGE_NO = QMessageBox.StandardButton.No
    MESSAGE_YES = QMessageBox.StandardButton.Yes
    NO_FRAME = QFrame.Shape.NoFrame
    CALENDAR_NO_VERTICAL_HEADER = QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader
    WEEKDAY_VALUES = tuple(Qt.DayOfWeek(day) for day in range(1, 8))
