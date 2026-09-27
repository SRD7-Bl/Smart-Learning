"""Rendering module for the Smart Learning desktop application.

Day 1 focuses on a usable PyQt window and display framework. Interactive
widgets are wired into the User Input Module, but no backend workflow is
connected.
"""

from __future__ import annotations

import re
import sys
from datetime import date, datetime
from typing import Any

from Backend.Data_Access import DataAccessModule
from Frontend.Input_Module import UserInputModule
from Frontend.Request_Module import RequestSendingModule
from Frontend.Status_Error_Display import StatusErrorDisplayModule
from Frontend.qt_compat import (
    QApplication,
    ECHO_NORMAL,
    ECHO_PASSWORD,
    MESSAGE_NO,
    MESSAGE_YES,
    NO_FRAME,
    QCheckBox,
    QComboBox,
    QDialog,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)


MOCK_ACADEMIC_INFO = {
    "student_name": "Test Student",
    "student_id": "000000",
    "last_updated": "Not synced yet",
    "summary": {
        "courses": 4,
        "assignments_due": 3,
        "notices": 2,
    },
    "schedule_days": [
        {
            "date": "2026-05-11",
            "day_type": "A Day",
            "classes": [
                {
                    "time": "08:30 - 09:45",
                    "course_name": "Mathematics",
                    "block": "A",
                    "teacher": "Ms. Smith",
                    "detail": "Room 204 - Algebra practice and worksheet review",
                },
                {
                    "time": "10:00 - 11:15",
                    "course_name": "Computer Science",
                    "block": "B",
                    "teacher": "Dr. Lee",
                    "detail": "Lab 3 - Project checkpoint discussion",
                },
                {
                    "time": "12:45 - 14:00",
                    "course_name": "English Literature",
                    "block": "C",
                    "teacher": "Mr. Brown",
                    "detail": "Room 118 - Group reading response",
                },
            ],
        },
        {
            "date": "2026-05-12",
            "day_type": "B Day",
            "classes": [
                {
                    "time": "08:30 - 09:45",
                    "course_name": "History",
                    "block": "D",
                    "teacher": "Ms. Chen",
                    "detail": "Room 215 - Quiz review",
                },
                {
                    "time": "10:00 - 11:15",
                    "course_name": "Mathematics",
                    "block": "E",
                    "teacher": "Ms. Smith",
                    "detail": "Room 204 - Chapter 4 practice",
                },
            ],
        },
        {
            "date": "2026-05-13",
            "day_type": "A Day",
            "classes": [
                {
                    "time": "08:30 - 09:45",
                    "course_name": "Computer Science",
                    "block": "A",
                    "teacher": "Dr. Lee",
                    "detail": "Lab 3 - Debugging workshop",
                },
                {
                    "time": "12:45 - 14:00",
                    "course_name": "English Literature",
                    "block": "C",
                    "teacher": "Mr. Brown",
                    "detail": "Room 118 - Reading discussion",
                },
            ],
        },
    ],
    "courses": [
        {
            "name": "Mathematics",
            "description": "Algebra, functions, and problem-solving practice.",
            "teacher": "Ms. Smith",
            "grade": "A",
            "status": "Current",
            "next_item": "Algebra worksheet due Friday",
            "assignments": [
                {
                    "name": "Algebra Worksheet",
                    "grade": "7/8",
                    "type": "Criteria A",
                    "comment": "Strong method, minor arithmetic error.",
                },
                {
                    "name": "Chapter 4 Review",
                    "grade": "8/8",
                    "type": "Criteria C",
                    "comment": "Clear reasoning and complete explanations.",
                },
            ],
        },
        {
            "name": "English Literature",
            "description": "Reading comprehension, written response, and discussion.",
            "teacher": "Mr. Brown",
            "grade": "B+",
            "status": "Current",
            "next_item": "Reading response pending",
            "assignments": [
                {
                    "name": "Reading Response",
                    "grade": "6/8",
                    "type": "Criteria B",
                    "comment": "Good interpretation; add more textual evidence.",
                },
            ],
        },
        {
            "name": "Computer Science",
            "description": "Programming fundamentals, debugging, and project design.",
            "teacher": "Dr. Lee",
            "grade": "A-",
            "status": "Current",
            "next_item": "Project checkpoint upcoming",
            "assignments": [
                {
                    "name": "Project Checkpoint",
                    "grade": "7/8",
                    "type": "Criteria D",
                    "comment": "Good progress; improve documentation.",
                },
                {
                    "name": "Debugging Journal",
                    "grade": "8/8",
                    "type": "Criteria C",
                    "comment": "Detailed reflection and useful test cases.",
                },
            ],
        },
        {
            "name": "History",
            "description": "Historical sources, argument writing, and quiz review.",
            "teacher": "Ms. Chen",
            "grade": "B",
            "status": "Current",
            "next_item": "Quiz review available",
            "assignments": [
                {
                    "name": "Quiz Review Notes",
                    "grade": "6/8",
                    "type": "Criteria A",
                    "comment": "Accurate facts; needs stronger organization.",
                },
            ],
        },
    ],
    "notices": [
        "Mock data is displayed for the A4 rendering skeleton.",
        "Refresh, login, and settings controls are placeholders.",
    ],
}


class SmartLearningWindow(QMainWindow):
    """Main PyQt window for the frontend rendering module."""

    def __init__(
        self,
        academic_info: dict[str, Any] | None = None,
        input_module: UserInputModule | None = None,
        request_module: RequestSendingModule | None = None,
        data_access_module: DataAccessModule | None = None,
        status_error_display: StatusErrorDisplayModule | None = None,
    ) -> None:
        super().__init__()
        self.academic_info = academic_info or MOCK_ACADEMIC_INFO
        self.request_module = request_module or RequestSendingModule(self)
        self.input_module = input_module or UserInputModule(self, request_module=self.request_module)
        if input_module is not None:
            self.request_module = input_module.request_module
        self.data_access_module = data_access_module or DataAccessModule(self)
        self.status_error_display = status_error_display or StatusErrorDisplayModule(self, self)
        self.status_error_display.set_dialog_parent(self)
        self.current_courses: list[dict[str, Any]] = []
        self.current_schedule_days: list[dict[str, Any]] = []
        self.has_configured_account = False
        self.onboarding_active = False
        self.onboarding_step = 1

        self.setWindowTitle("Smart Learning")
        self.setMinimumSize(980, 680)
        self.resize(1120, 760)

        self._build_ui()
        self._connect_signal_board()
        self.render_academic_info(self.academic_info)
        self.data_access_module.request_user_settings()
        self.data_access_module.request_academic_info()
        self.input_module.emit_initial_state()

    def _build_ui(self) -> None:
        root = QWidget()
        root.setObjectName("root")
        self.setCentralWidget(root)

        main_layout = QVBoxLayout(root)
        main_layout.setContentsMargins(24, 20, 24, 18)
        main_layout.setSpacing(16)

        main_layout.addWidget(self._build_header())
        self.help_hint = self._build_help_hint()
        main_layout.addWidget(self.help_hint)
        self.onboarding_panel = self._build_onboarding_panel()
        main_layout.addWidget(self.onboarding_panel)
        main_layout.addWidget(self._build_content_area(), stretch=1)
        main_layout.addWidget(self._build_status_bar())

        self._base_stylesheet = """
            QWidget {
                background: #f6f7f9;
                color: #20242a;
                font-family: Arial, Helvetica, sans-serif;
                font-size: 14px;
            }
            QLabel#appTitle {
                font-size: 28px;
                font-weight: 700;
                color: #1f5fbf;
            }
            QLabel#sectionTitle {
                font-size: 16px;
                font-weight: 700;
            }
            QLabel#loginNotice {
                background: #fff4d8;
                border: 1px solid #e1ad3d;
                border-radius: 6px;
                color: #5f3b00;
                font-weight: 700;
                padding: 8px 10px;
            }
            QLabel#helpHint {
                background: #e9f2ff;
                border: 2px solid #2364c8;
                border-radius: 8px;
                color: #153f78;
                font-size: 15px;
                font-weight: 700;
                padding: 10px 12px;
            }
            QFrame#onboardingPanel {
                background: #fff8e8;
                border: 2px solid #e8a126;
                border-radius: 10px;
            }
            QLabel#onboardingTitle {
                background: transparent;
                color: #744500;
                font-size: 17px;
                font-weight: 700;
            }
            QLabel#onboardingProgress {
                background: #ffffff;
                border: 1px solid #e4c27d;
                border-radius: 6px;
                color: #6a4a12;
                font-weight: 700;
                padding: 6px 9px;
            }
            QLabel#onboardingBody {
                background: transparent;
                color: #4d3a17;
                font-weight: 600;
            }
            QLabel#mutedText {
                color: #667085;
            }
            QGroupBox {
                background: #ffffff;
                border: 1px solid #d7dce3;
                border-radius: 8px;
                margin-top: 10px;
                padding: 14px;
                font-weight: 700;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 4px;
            }
            QGroupBox#accountManagement {
                background: #f7f3ff;
                border: 2px solid #b8a3e8;
            }
            QLineEdit {
                background: #ffffff;
                border: 1px solid #cbd3df;
                border-radius: 6px;
                padding: 8px 10px;
            }
            QCheckBox {
                background: #ffffff;
                border: 2px solid #98a6b8;
                border-radius: 7px;
                color: #283442;
                font-weight: 600;
                padding: 7px 10px;
                spacing: 8px;
            }
            QCheckBox:hover {
                background: #f4f8ff;
                border-color: #2364c8;
            }
            QCheckBox:checked {
                background: #dceaff;
                border-color: #2364c8;
                color: #174b91;
            }
            QCheckBox:disabled {
                background: #edf0f4;
                border-color: #aeb8c5;
                color: #4b5563;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
            QPushButton {
                background: #ffffff;
                border: 1px solid #b9c3d0;
                border-radius: 6px;
                padding: 8px 14px;
                font-weight: 600;
            }
            QPushButton#primaryButton {
                background: #2364c8;
                border-color: #2364c8;
                color: #ffffff;
            }
            QPushButton#accountButton {
                background: #6842c2;
                border: 2px solid #5533a6;
                color: #ffffff;
                font-weight: 700;
                min-width: 190px;
            }
            QPushButton#accountButton:hover {
                background: #7a52d1;
                border-color: #40227f;
            }
            QPushButton#onboardingAction {
                background: #e89a18;
                border: 2px solid #b86e00;
                color: #ffffff;
                font-weight: 700;
                min-width: 160px;
            }
            QPushButton#onboardingAction:hover {
                background: #f2aa31;
            }
            QPushButton#accountButton[onboardingTarget="true"],
            QPushButton#loginButton[onboardingTarget="true"],
            QPushButton#primaryButton[onboardingTarget="true"] {
                border: 3px solid #f0a020;
            }
            QLineEdit[onboardingTarget="true"] {
                border: 3px solid #f0a020;
                background: #fffdf5;
            }
            QPushButton#helpButton {
                background: #f5a623;
                border: 2px solid #c97800;
                color: #2b1a00;
                font-weight: 700;
                min-width: 130px;
            }
            QPushButton#helpButton:hover {
                background: #ffbd4a;
                border-color: #9d5e00;
            }
            QPushButton#dangerButton {
                background: #ffffff;
                border-color: #c73737;
                color: #a52727;
            }
            QPushButton:hover {
                border-color: #2364c8;
            }
            QComboBox {
                background: #ffffff;
                border: 1px solid #c8d0dc;
                border-radius: 6px;
                min-height: 34px;
                padding: 6px 10px;
            }
            QFrame#courseCard {
                background: #ffffff;
                border: 1px solid #d7dce3;
                border-radius: 8px;
            }
            QFrame#assignmentCard {
                background: #ffffff;
                border: 1px solid #d7dce3;
                border-radius: 8px;
            }
            QFrame#filterPanel {
                background: #f8fafc;
                border: 1px solid #d7dce3;
                border-radius: 8px;
            }
            QFrame#scheduleCard {
                background: #ffffff;
                border: 1px solid #cbd8ea;
                border-radius: 12px;
            }
            QFrame#scheduleCard[cardVariant="alternate"] {
                background: #fcfbff;
                border-color: #d8cbed;
            }
            QFrame#scheduleAccent {
                background: #2364c8;
                border: none;
                border-radius: 3px;
            }
            QFrame#scheduleAccent[accentVariant="alternate"] {
                background: #7650c7;
            }
            QFrame#scheduleDetails {
                background: #f4f7fb;
                border: 1px solid #e0e7f0;
                border-radius: 7px;
            }
            QFrame#scheduleDaySection {
                background: #f8fbff;
                border: 1px solid #c7d8ee;
                border-radius: 12px;
            }
            QFrame#scheduleDayBanner {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #1f5fbf, stop: 1 #4e7fd0
                );
                border: none;
                border-radius: 9px;
            }
            QLabel#scheduleDateTitle {
                background: transparent;
                color: #ffffff;
                font-size: 18px;
                font-weight: 700;
            }
            QLabel#scheduleDayBadge {
                background: #ffffff;
                border: 1px solid #d9e6f8;
                border-radius: 7px;
                color: #174b91;
                font-weight: 700;
                padding: 6px 10px;
            }
            QLabel#scheduleTime {
                background: #e5efff;
                border: 1px solid #9bb9e8;
                border-radius: 7px;
                color: #174b91;
                font-weight: 700;
                padding: 6px 9px;
            }
            QLabel#scheduleCourseTitle {
                background: transparent;
                color: #202a38;
                font-size: 16px;
                font-weight: 700;
            }
            QLabel#scheduleBlockBadge {
                background: #fff0d6;
                border: 2px solid #e7a32f;
                border-radius: 8px;
                color: #704200;
                font-weight: 700;
                padding: 6px 10px;
            }
            QLabel#scheduleTeacher {
                background: transparent;
                color: #52657d;
                font-weight: 600;
            }
            QLabel#scheduleDetailKey {
                background: transparent;
                color: #52657d;
                font-weight: 700;
            }
            QFrame#statusFrame {
                background: #ffffff;
                border: 1px solid #d7dce3;
                border-radius: 8px;
            }
            QTabWidget::pane {
                border: 1px solid #d7dce3;
                border-radius: 8px;
                background: #ffffff;
                top: -1px;
            }
            QTabBar::tab {
                background: #edf0f4;
                border: 1px solid #d7dce3;
                border-bottom: none;
                min-width: 190px;
                padding: 11px 24px;
                margin-right: 4px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                font-weight: 600;
            }
            QTabBar::tab:selected {
                background: #ffffff;
                color: #1f5fbf;
            }
            """
        self.setStyleSheet(self._base_stylesheet)

    def _dark_theme_stylesheet(self) -> str:
        return """
            QWidget {
                background: #161b22;
                color: #e6edf3;
            }
            QLabel {
                background: transparent;
            }
            QLabel#appTitle {
                color: #79b8ff;
            }
            QLabel#mutedText {
                color: #9eafc2;
            }
            QLabel#loginNotice {
                background: #392d15;
                border-color: #bd8427;
                color: #ffd98c;
            }
            QLabel#helpHint {
                background: #172b45;
                border-color: #4e8ed8;
                color: #cce3ff;
            }
            QFrame#onboardingPanel {
                background: #332711;
                border-color: #d28b1d;
            }
            QLabel#onboardingTitle,
            QLabel#onboardingBody {
                color: #ffe1a3;
            }
            QLabel#onboardingProgress {
                background: #211c14;
                border-color: #8e6b2d;
                color: #ffd98c;
            }
            QGroupBox {
                background: #1d232d;
                border-color: #3b4655;
            }
            QGroupBox#accountManagement {
                background: #28213a;
                border-color: #7958bd;
            }
            QLineEdit,
            QComboBox {
                background: #10151c;
                border-color: #536174;
                color: #f0f4f8;
            }
            QComboBox QAbstractItemView {
                background: #1d232d;
                color: #f0f4f8;
                selection-background-color: #285f9e;
            }
            QCheckBox {
                background: #202733;
                border-color: #536174;
                color: #e6edf3;
            }
            QCheckBox:hover {
                background: #263448;
                border-color: #64a6ed;
            }
            QCheckBox:checked {
                background: #18375e;
                border-color: #64a6ed;
                color: #d9ecff;
            }
            QCheckBox:disabled {
                background: #252b34;
                border-color: #46515f;
                color: #8c99a8;
            }
            QPushButton {
                background: #252d38;
                border-color: #536174;
                color: #edf2f7;
            }
            QPushButton:hover {
                background: #303a48;
                border-color: #64a6ed;
            }
            QPushButton#primaryButton {
                background: #2c70c9;
                border-color: #5c9dea;
                color: #ffffff;
            }
            QPushButton#accountButton {
                background: #7250c7;
                border-color: #a287e0;
                color: #ffffff;
            }
            QPushButton#dangerButton {
                background: #302024;
                border-color: #e06c75;
                color: #ff9da5;
            }
            QPushButton#themeToggle {
                background: #252d38;
                border-color: #536174;
                color: #f2d479;
            }
            QFrame#courseCard,
            QFrame#assignmentCard,
            QFrame#filterPanel,
            QFrame#scheduleCard,
            QFrame#scheduleDaySection,
            QFrame#statusFrame {
                background: #1d232d;
                border-color: #3b4655;
            }
            QFrame#scheduleCard[cardVariant="alternate"] {
                background: #221f2d;
                border-color: #56466d;
            }
            QFrame#scheduleDetails {
                background: #151b23;
                border-color: #364252;
            }
            QLabel#scheduleCourseTitle {
                color: #f1f5fa;
            }
            QLabel#scheduleTeacher,
            QLabel#scheduleDetailKey {
                color: #aabbd0;
            }
            QLabel#scheduleTime {
                background: #193b64;
                border-color: #487ebd;
                color: #cfe7ff;
            }
            QLabel#scheduleBlockBadge {
                background: #3a2a11;
                border-color: #d99525;
                color: #ffd181;
            }
            QLabel#scheduleDayBadge {
                background: #182536;
                border-color: #6b91c2;
                color: #d9eaff;
            }
            QTabWidget::pane {
                background: #161b22;
                border-color: #3b4655;
            }
            QTabBar::tab {
                background: #242b35;
                border-color: #3b4655;
                color: #abb8c7;
            }
            QTabBar::tab:selected {
                background: #1d232d;
                color: #79b8ff;
            }
            QScrollArea,
            QScrollArea > QWidget > QWidget {
                background: #161b22;
            }
            QScrollBar:vertical {
                background: #161b22;
                width: 12px;
            }
            QScrollBar::handle:vertical {
                background: #4b5868;
                border-radius: 5px;
                min-height: 24px;
            }
        """

    def _scoped_dark_theme_stylesheet(self) -> str:
        """Raise dark-theme selector priority without duplicating the base stylesheet."""

        def scope_rule(match: re.Match[str]) -> str:
            boundary, selectors = match.groups()
            scoped_selectors = []
            for selector in selectors.split(","):
                selector = selector.strip()
                if selector:
                    scoped_selectors.append(
                        f'QWidget#root[darkMode="true"] {selector}'
                    )
            return f"{boundary}\n{', '.join(scoped_selectors)} {{"

        scoped_rules = re.sub(
            r"(^|})\s*([^{}]+)\{",
            scope_rule,
            self._dark_theme_stylesheet(),
        )
        return (
            'QWidget#root[darkMode="true"] {'
            "background: #161b22; color: #e6edf3;"
            "}"
            + scoped_rules
        )

    '''因为有3个tab，因此分开渲染，这里是顶部不变的展示条'''
    def _build_header(self) -> QWidget:
        header = QWidget()
        layout = QHBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 0)

        title_area = QVBoxLayout()
        self.title_label = QLabel("Smart Learning")
        self.title_label.setObjectName("appTitle")
        title_area.addWidget(self.title_label)

        self.help_button = QPushButton("Help / 使用教程")
        self.help_button.setObjectName("helpButton")
        self.theme_toggle = QPushButton("☾ Dark")
        self.theme_toggle.setObjectName("themeToggle")
        self.theme_toggle.setCheckable(True)
        self.theme_toggle.setFixedWidth(88)
        self.theme_toggle.setToolTip("Switch between light and dark themes")
        self.logout_button = QPushButton("Log out")
        self.login_state_label = QLabel()
        self.login_state_label.setToolTip(
            "Shows whether locally stored academic data is currently unlocked."
        )
        self._set_login_status(False)

        layout.addLayout(title_area, stretch=1)
        layout.addWidget(self.theme_toggle)
        layout.addWidget(self.login_state_label)
        layout.addWidget(self.help_button)
        layout.addWidget(self.logout_button)
        return header

    def _build_help_hint(self) -> QLabel:
        hint = QLabel(
            "第一次使用或不知道下一步做什么？请点击右上角的“Help / 使用教程”，"
            "查看账户设置、使用步骤和安全说明。"
        )
        hint.setObjectName("helpHint")
        hint.setWordWrap(True)
        return hint

    def _build_onboarding_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("onboardingPanel")
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(14, 11, 14, 11)
        layout.setSpacing(14)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(5)
        self.onboarding_title = QLabel()
        self.onboarding_title.setObjectName("onboardingTitle")
        self.onboarding_progress = QLabel()
        self.onboarding_progress.setObjectName("onboardingProgress")
        self.onboarding_body = QLabel()
        self.onboarding_body.setObjectName("onboardingBody")
        self.onboarding_body.setWordWrap(True)
        text_layout.addWidget(self.onboarding_title)
        text_layout.addWidget(self.onboarding_progress)
        text_layout.addWidget(self.onboarding_body)

        self.onboarding_action_button = QPushButton()
        self.onboarding_action_button.setObjectName("onboardingAction")
        self.onboarding_action_button.clicked.connect(self._run_onboarding_action)

        layout.addLayout(text_layout, stretch=1)
        layout.addWidget(self.onboarding_action_button)
        panel.hide()
        return panel

    def _build_input_panel(self) -> QGroupBox:
        panel = QGroupBox("Account and Data Controls")
        layout = QVBoxLayout(panel)
        layout.setSpacing(10)

        self.student_id_input = QLineEdit()
        self.student_id_input.setPlaceholderText("Email Address")

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(ECHO_PASSWORD)
        self.password_visibility_button = QPushButton("Show")
        self.password_visibility_button.setCheckable(True)
        self.password_visibility_button.setToolTip("Show or hide the password")

        self.login_button = QPushButton("Login")
        self.login_button.setObjectName("loginButton")
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setObjectName("primaryButton")
        self.refresh_mode_selector = QComboBox()
        self.refresh_mode_selector.addItem("Both", "both")
        self.refresh_mode_selector.addItem("Assignments only", "assignments")
        self.refresh_mode_selector.addItem("Schedule only", "schedule")
        self.refresh_mode_selector.setMinimumWidth(170)
        self.schedule_day_count_selector = QComboBox()
        for day_count in (1, 3, 5, 7, 14, 31):
            self.schedule_day_count_selector.addItem(f"{day_count} day(s)", day_count)
        self.schedule_day_count_selector.setMinimumWidth(120)
        self.update_auth_button = QPushButton("Create a New Account")
        self.update_auth_button.setObjectName("accountButton")
        self.auto_login_checkbox = QCheckBox("Auto login on startup")
        self.auto_login_checkbox.setToolTip(
            "Automatically unlock locally stored data when the application starts."
        )
        self.first_use_checkbox = QCheckBox("First time using this application")
        self.first_use_checkbox.setToolTip(
            "Check to start the setup guide, or uncheck to dismiss it."
        )
        self.delete_local_data_button = QPushButton("Delete Local Data")
        self.delete_local_data_button.setObjectName("dangerButton")
        self.reset_local_data_button = QPushButton("Forgot Password / Reset App")
        self.reset_local_data_button.setObjectName("dangerButton")
        self.login_notice = QLabel("请使用与 TigerNet 登录相同的邮箱和密码")
        self.login_notice.setObjectName("loginNotice")
        self.login_notice.setWordWrap(True)

        login_row = QHBoxLayout()
        login_row.addWidget(QLabel("Email Address"))
        login_row.addWidget(self.student_id_input, stretch=1)
        login_row.addWidget(QLabel("Password"))
        login_row.addWidget(self.password_input, stretch=1)
        login_row.addWidget(self.password_visibility_button)
        login_row.addWidget(self.login_button)

        refresh_row = QHBoxLayout()
        refresh_row.addWidget(QLabel("Refresh"))
        refresh_row.addWidget(self.refresh_mode_selector)
        refresh_row.addWidget(self.schedule_day_count_selector)
        refresh_row.addWidget(self.refresh_button)
        refresh_row.addStretch(1)

        preference_row = QHBoxLayout()
        preference_row.addWidget(self.auto_login_checkbox)
        preference_row.addWidget(self.first_use_checkbox)
        preference_row.addStretch(1)

        layout.addWidget(self.login_notice)
        layout.addLayout(login_row)
        layout.addLayout(refresh_row)
        layout.addLayout(preference_row)
        return panel

    def _build_account_management_panel(self) -> QGroupBox:
        panel = QGroupBox("Account Management")
        panel.setObjectName("accountManagement")
        layout = QHBoxLayout(panel)
        layout.setSpacing(10)
        layout.addWidget(self.update_auth_button)
        layout.addWidget(self.delete_local_data_button)
        layout.addWidget(self.reset_local_data_button)
        layout.addStretch(1)
        return panel

    def _build_content_area(self) -> QTabWidget:
        self.tabs = QTabWidget()

        #一共有3个tab
        self.basic_tab = self._build_basic_tab()
        self.schedule_tab = self._build_schedule_tab()
        self.course_tab = self._build_course_tab()

        self.tabs.addTab(self.basic_tab, "Basic Info")
        self.tabs.addTab(self.schedule_tab, "Schedule")
        self.tabs.addTab(self.course_tab, "Courses & Assignments")
        self.tabs.setCurrentIndex(1)
        return self.tabs

    #info tab：账号管理以及刷新等信息
    def _build_basic_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)

        self.basic_content = QWidget()
        content_layout = QVBoxLayout(self.basic_content)
        content_layout.setContentsMargins(14, 14, 14, 14)
        content_layout.setSpacing(14)
        self.basic_content.setMinimumHeight(475)

        input_panel = self._build_input_panel()
        self.account_controls_group = input_panel
        self.account_controls_group.setMinimumHeight(215)
        self.account_management_group = self._build_account_management_panel()
        self.account_management_group.setMinimumHeight(90)
        content_layout.addWidget(self.account_management_group)
        content_layout.addWidget(input_panel)
        self.profile_group = QGroupBox("Student Overview")
        self.profile_group.setMinimumHeight(95)
        self.profile_layout = QGridLayout(self.profile_group)

        content_layout.addWidget(self.profile_group)
        content_layout.addStretch(1)

        self.basic_scroll = QScrollArea()
        self.basic_scroll.setObjectName("basicScroll")
        self.basic_scroll.setWidgetResizable(True)
        self.basic_scroll.setFrameShape(NO_FRAME)
        self.basic_scroll.setWidget(self.basic_content)
        layout.addWidget(self.basic_scroll)
        return tab

    def _build_schedule_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(14)

        self.schedule_group = QGroupBox("Schedule")
        schedule_group_layout = QVBoxLayout(self.schedule_group)

        schedule_picker = QHBoxLayout()
        self.schedule_day_selector = QComboBox()
        self.schedule_day_selector.setMinimumWidth(320)
        self.schedule_day_selector.currentIndexChanged.connect(self._select_schedule_day)
        self.schedule_day_meta_label = QLabel()
        self.schedule_day_meta_label.setObjectName("mutedText")
        schedule_picker.addWidget(QLabel("Day"))
        schedule_picker.addWidget(self.schedule_day_selector)
        schedule_picker.addWidget(self.schedule_day_meta_label)
        schedule_picker.addStretch(1)
        schedule_group_layout.addLayout(schedule_picker)

        self.schedule_list = QWidget()
        self.schedule_list_layout = QVBoxLayout(self.schedule_list)
        self.schedule_list_layout.setContentsMargins(0, 0, 0, 0)
        self.schedule_list_layout.setSpacing(10)

        schedule_scroll = QScrollArea()
        schedule_scroll.setWidgetResizable(True)
        schedule_scroll.setFrameShape(NO_FRAME)
        schedule_scroll.setWidget(self.schedule_list)
        schedule_group_layout.addWidget(schedule_scroll)

        layout.addWidget(self.schedule_group, stretch=1)
        return tab

    def _build_course_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(14)

        self.course_selector_group = QGroupBox("Select Course")
        self.course_selector_layout = QVBoxLayout(self.course_selector_group)
        self.course_selector_layout.setSpacing(8)
        self.course_selector = QComboBox()
        self.course_selector.setMinimumWidth(360)
        self.course_selector.currentIndexChanged.connect(self._select_course)
        self.course_selector_layout.addWidget(self.course_selector)

        self.course_detail_group = QGroupBox("Course Details")
        course_detail_group_layout = QVBoxLayout(self.course_detail_group)
        self.course_detail = QWidget()
        self.course_detail_layout = QVBoxLayout(self.course_detail)
        self.course_detail_layout.setContentsMargins(0, 0, 0, 0)
        self.course_detail_layout.setSpacing(10)

        course_scroll = QScrollArea()
        course_scroll.setWidgetResizable(True)
        course_scroll.setFrameShape(NO_FRAME)
        course_scroll.setWidget(self.course_detail)
        course_detail_group_layout.addWidget(course_scroll)

        layout.addWidget(self.course_selector_group)
        layout.addWidget(self.course_detail_group, stretch=1)
        return tab

    def _build_status_bar(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("statusFrame")
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(12, 10, 12, 10)

        self.status_label = QLabel()
        self.status_label.setObjectName("mutedText")
        self.error_label = QLabel("No errors")
        self.error_label.setObjectName("mutedText")

        layout.addWidget(self.status_label, stretch=1)
        layout.addWidget(self.error_label)
        return frame

    def _connect_signal_board(self) -> None:
        self.refresh_button.clicked.connect(self._send_refresh_input)
        self.help_button.clicked.connect(self._show_help_dialog)
        self.logout_button.clicked.connect(self.input_module.request_logout)
        self.login_button.clicked.connect(self._send_login_input)
        self.password_visibility_button.toggled.connect(self._set_password_visibility)
        self.update_auth_button.clicked.connect(self._update_auth_credentials)
        self.theme_toggle.toggled.connect(self.input_module.request_dark_mode_change)
        self.auto_login_checkbox.toggled.connect(self.input_module.request_auto_login_change)
        self.first_use_checkbox.toggled.connect(self.input_module.request_first_use_change)
        self.delete_local_data_button.clicked.connect(self._delete_local_data)
        self.reset_local_data_button.clicked.connect(self._reset_local_data)
        self.input_module.content_access_changed.connect(self._set_content_access)
        self.input_module.auto_login_changed.connect(self._set_auto_login_checkbox)
        self.input_module.first_use_changed.connect(self._set_first_use_checkbox)
        self.input_module.dark_mode_changed.connect(self._set_dark_mode)
        self.input_module.privacy_notice_requested.connect(self._show_privacy_notice)
        self.input_module.validation_failed.connect(self.status_error_display.display_error)
        self.input_module.status_changed.connect(self.status_error_display.display_status)
        self.request_module.request_queued.connect(self.status_error_display.display_status)
        self.request_module.request_failed.connect(self.status_error_display.display_error)
        self.request_module.login_succeeded.connect(self._handle_login_succeeded)
        self.request_module.refresh_succeeded.connect(self._handle_refresh_succeeded)
        self.input_module.logout_requested.connect(self._clear_login_inputs)
        self.data_access_module.all_data_loaded.connect(self._show_data_access_result)
        self.data_access_module.user_settings_loaded.connect(self._handle_user_settings_loaded)
        self.data_access_module.academic_info_loaded.connect(self.render_academic_info)
        self.data_access_module.data_access_failed.connect(self.status_error_display.display_error)
        self.data_access_module.auth_credentials_updated.connect(self._show_auth_update_success)
        self.data_access_module.local_data_deleted.connect(self._handle_local_data_deleted)
        self.status_error_display.status_ready.connect(self.set_status)

    def _show_help_dialog(self) -> None:
        dialog = self._build_help_dialog()
        if hasattr(dialog, "exec"):
            dialog.exec()
        else:  # pragma: no cover - retained for older PyQt5 builds.
            dialog.exec_()

    def _build_help_dialog(self) -> QDialog:
        dialog = QDialog(self)
        dialog.setWindowTitle("Smart Learning Help")
        dialog.setMinimumSize(680, 560)
        dialog.resize(720, 620)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)

        title = QLabel("Smart Learning User Guide")
        title.setObjectName("appTitle")
        introduction = QLabel(
            "Use this guide to set up the application, refresh TigerNet information, "
            "and understand how your local data is handled."
        )
        introduction.setWordWrap(True)
        introduction.setObjectName("mutedText")
        layout.addWidget(title)
        layout.addWidget(introduction)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(NO_FRAME)
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(2, 2, 8, 2)
        content_layout.setSpacing(10)

        sections = (
            (
                "What This Application Does",
                "Smart Learning is a local desktop dashboard for Ridley College students. "
                "It retrieves schedules, courses, assignments, grades, and teacher comments from TigerNet, "
                "organizes them into simpler views, and keeps the most recently refreshed information available locally.",
            ),
            (
                "Account Setup",
                "First setup\n"
                "1. Select Create a New Account.\n"
                "2. Enter the same TigerNet email address and password used on the school website.\n"
                "3. Enter those credentials in the login fields to unlock the application.\n\n"
                "Later changes require the currently stored password. If it has been forgotten, use "
                "Forgot Password / Reset App. Resetting removes all local login and academic data before a new account can be configured.",
            ),
            (
                "How to Use Smart Learning",
                "• Login unlocks the Schedule and Courses & Assignments tabs.\n"
                "• Refresh Both to update assignments and schedules together, or select one data type.\n"
                "• Choose how many schedule days to retrieve before refreshing.\n"
                "• Use the course selector and assignment filters to find specific results.\n"
                "• Auto login is optional. When enabled, anyone using this macOS account can open the cached information without entering the TigerNet password.\n"
                "• Log out to lock the academic tabs and disable auto login.\n"
                "• Delete Local Data requires the current password. The reset option is only for cases where that password is no longer available.",
            ),
            (
                "Security and Privacy",
                "The TigerNet login and cached academic information are stored only on this Mac. "
                "The local files are encrypted, and their encryption key is kept in macOS Keychain.\n\n"
                "The password is sent directly to the TigerNet/Microsoft login page only when authentication is required. "
                "Smart Learning does not send passwords, grades, assignments, schedules, or teacher comments to the developer or to any other third party.\n\n"
                "Deleting or resetting local data cannot be undone inside the application. The academic information can be retrieved again from TigerNet after configuring a valid account.",
            ),
        )

        for section_title, section_text in sections:
            group = QGroupBox(section_title)
            group_layout = QVBoxLayout(group)
            body = QLabel(section_text)
            body.setWordWrap(True)
            body.setStyleSheet("font-weight: 400;")
            group_layout.addWidget(body)
            content_layout.addWidget(group)

        content_layout.addStretch(1)
        scroll.setWidget(content)
        layout.addWidget(scroll, stretch=1)

        button_row = QHBoxLayout()
        button_row.addStretch(1)
        close_button = QPushButton("Close")
        close_button.setObjectName("primaryButton")
        close_button.clicked.connect(dialog.accept)
        button_row.addWidget(close_button)
        layout.addLayout(button_row)
        return dialog

    def _send_login_input(self) -> None:
        self.input_module.request_login(
            self.student_id_input.text().strip(),
            self.password_input.text(),
        )
        self._clear_login_inputs()

    def _send_refresh_input(self) -> None:
        self.input_module.request_refresh(
            str(self.refresh_mode_selector.currentData()),
            int(self.schedule_day_count_selector.currentData()),
        )

    def render_academic_info(self, data: dict[str, Any]) -> None:
        self.academic_info = data
        self._clear_layout(self.profile_layout)
        self._clear_layout(self.schedule_list_layout)
        self._clear_layout(self.course_detail_layout)
        self.course_selector.blockSignals(True)
        self.course_selector.clear()
        self.course_selector.blockSignals(False)

        self._render_profile(data)
        self._render_schedule(data.get("schedule_days", data.get("schedule", [])))
        self._render_courses(data.get("courses", []))

    def set_status(self, message: str) -> None:
        self.status_label.setText(message)

    def set_error(self, message: str | None) -> None:
        self.error_label.setText(message or "No errors")

    def show_message(self, message: str) -> None:
        QMessageBox.information(self, "Smart Learning", message)

    def _show_data_access_result(self, user_settings: dict[str, Any], academic_info: dict[str, Any]) -> None:
        student = user_settings.get("student", {})
        courses = academic_info.get("courses", [])
        schedule_days = academic_info.get("schedule_days", [])
        message = (
            "Data Access Module loaded local data.\n\n"
            f"Student: {student.get('display_name', 'Unknown')}\n"
            f"Student ID: {student.get('student_id', 'Unknown')}\n"
            f"Auto login: {user_settings.get('auto_login', False)}\n"
            f"Courses loaded: {len(courses)}\n"
            f"Schedule days loaded: {len(schedule_days)}"
        )
        QMessageBox.information(self, "Data Access Test", message)

    def _handle_login_succeeded(self, user_settings: dict[str, Any]) -> None:
        self._clear_login_inputs()
        self._clear_layout(self.profile_layout)
        student = user_settings.get("student", {})
        self._render_profile(
            {
                "student_name": self.academic_info.get("student_name") or student.get("display_name", "Unknown"),
                "student_id": self.academic_info.get("student_id") or student.get("student_id", "Unknown"),
                "last_updated": self.academic_info.get("last_updated", "Never"),
            }
        )
        if self.onboarding_active:
            self._show_onboarding_step(3)

    def _handle_refresh_succeeded(self, academic_info: dict[str, Any]) -> None:
        self.render_academic_info(academic_info)

    def _clear_login_inputs(self) -> None:
        self.student_id_input.clear()
        self.password_input.clear()
        self.password_visibility_button.blockSignals(True)
        self.password_visibility_button.setChecked(False)
        self.password_visibility_button.blockSignals(False)
        self._set_password_visibility(False)

    def _set_password_visibility(self, visible: bool) -> None:
        self.password_input.setEchoMode(ECHO_NORMAL if visible else ECHO_PASSWORD)
        self.password_visibility_button.setText("Hide" if visible else "Show")

    def _update_auth_credentials(self) -> None:
        current_password = ""
        dialog_title = "Create a New Account"
        if self.has_configured_account:
            dialog_title = "Change TigerNet Login"
            current_password, current_password_ok = QInputDialog.getText(
                self,
                "Authorize Credential Change",
                "Current password:",
                ECHO_PASSWORD,
            )
            if not current_password_ok:
                return

        username, username_ok = QInputDialog.getText(
            self,
            dialog_title,
            "Email Address:",
        )
        if not username_ok:
            return

        password, password_ok = QInputDialog.getText(
            self,
            dialog_title,
            "Password:",
            ECHO_PASSWORD,
        )
        if not password_ok:
            return

        self.data_access_module.update_auth_credentials(
            username,
            password,
            current_password=current_password,
        )

    def _delete_local_data(self) -> None:
        current_password, password_ok = QInputDialog.getText(
            self,
            "Delete Local Data",
            "Enter the current password to authorize deletion:",
            ECHO_PASSWORD,
        )
        if not password_ok:
            return

        confirmation = QMessageBox.question(
            self,
            "Delete Local Data",
            "Permanently delete the locally stored login information, courses, assignments, and schedule?",
            MESSAGE_YES | MESSAGE_NO,
            MESSAGE_NO,
        )
        if confirmation != MESSAGE_YES:
            return

        self.data_access_module.delete_local_data(current_password)

    def _handle_local_data_deleted(self) -> None:
        self.academic_info = {}
        self.render_academic_info({})
        self._set_account_configuration_state(False)
        self.input_module.request_logout()
        self.input_module.restart_first_use()
        self.status_error_display.display_status("Local data and login information deleted.")
        QMessageBox.information(self, "Smart Learning", "Local data and login information deleted.")

    def _reset_local_data(self) -> None:
        confirmation = QMessageBox.question(
            self,
            "Reset Smart Learning",
            "Forgotten passwords cannot be recovered. Resetting deletes all local login and academic data. Continue?",
            MESSAGE_YES | MESSAGE_NO,
            MESSAGE_NO,
        )
        if confirmation != MESSAGE_YES:
            return

        confirmation_text, confirmation_ok = QInputDialog.getText(
            self,
            "Confirm Reset",
            "Type RESET to permanently clear this application:",
        )
        if not confirmation_ok:
            return
        if confirmation_text.strip() != "RESET":
            self.status_error_display.display_error("Reset cancelled because the confirmation text did not match.")
            return

        self.data_access_module.reset_local_data()

    def _set_auto_login_checkbox(self, enabled: bool) -> None:
        self.auto_login_checkbox.blockSignals(True)
        self.auto_login_checkbox.setChecked(enabled)
        self.auto_login_checkbox.blockSignals(False)

    def _set_dark_mode(self, enabled: bool) -> None:
        self.theme_toggle.blockSignals(True)
        self.theme_toggle.setChecked(enabled)
        self.theme_toggle.setText("☀ Light" if enabled else "☾ Dark")
        self.theme_toggle.blockSignals(False)
        self.centralWidget().setProperty("darkMode", "true" if enabled else "false")
        stylesheet = self._base_stylesheet
        if enabled:
            stylesheet += self._scoped_dark_theme_stylesheet()
        self.setStyleSheet(stylesheet)

        tab_stylesheet = self._dark_theme_stylesheet() if enabled else ""
        for tab in (self.basic_tab, self.schedule_tab, self.course_tab):
            tab.setStyleSheet(tab_stylesheet)

    def _set_first_use_checkbox(self, enabled: bool) -> None:
        self.first_use_checkbox.blockSignals(True)
        self.first_use_checkbox.setChecked(enabled)
        self.first_use_checkbox.blockSignals(False)
        self.onboarding_active = enabled
        self.onboarding_panel.setVisible(enabled)
        self.help_hint.setVisible(not enabled)
        if enabled:
            self._sync_onboarding_step()
        else:
            self._clear_onboarding_targets()

    def _show_privacy_notice(self) -> None:
        QMessageBox.information(
            self,
            "How Smart Learning Handles Your Data",
            "Smart Learning stores your TigerNet login and cached academic information only on this Mac.\n\n"
            "Your password is sent directly to the TigerNet/Microsoft login page only when authentication is needed. "
            "The application does not send your password, grades, assignments, or schedule to the developer or "
            "to any other third party.",
        )

    def _show_auth_update_success(self) -> None:
        account_was_configured = self.has_configured_account
        self._set_account_configuration_state(True)
        if account_was_configured:
            message = "TigerNet login credentials updated."
        else:
            message = "Smart Learning account created using your TigerNet credentials."
        self.status_error_display.display_status(message)
        QMessageBox.information(self, "Smart Learning", message)

    def _handle_user_settings_loaded(self, user_settings: dict[str, Any]) -> None:
        auth = user_settings.get("auth", {})
        has_credentials = bool(
            isinstance(auth, dict)
            and str(auth.get("student_id", "")).strip()
            and str(auth.get("password", ""))
        )
        self._set_account_configuration_state(has_credentials)

    def _set_account_configuration_state(self, configured: bool) -> None:
        self.has_configured_account = configured
        button_text = "Change Email/Password" if configured else "Create a New Account"
        self.update_auth_button.setText(button_text)
        if self.onboarding_active:
            self._sync_onboarding_step()

    def _sync_onboarding_step(self) -> None:
        if self.input_module.is_logged_in:
            step = 3
        elif self.has_configured_account:
            step = 2
        else:
            step = 1
        self._show_onboarding_step(step)

    def _show_onboarding_step(self, step: int) -> None:
        if not self.onboarding_active:
            return

        self.onboarding_step = max(1, min(step, 3))
        step_content = {
            1: (
                "第 1 步：创建账户",
                "点击 Create a New Account，并保存与 TigerNet 相同的邮箱和密码。",
                "Create Account",
            ),
            2: (
                "第 2 步：登录",
                "在下方输入同一个 TigerNet 邮箱和密码，然后点击 Login。",
                "Go to Login",
            ),
            3: (
                "第 3 步：获取最新数据",
                "登录成功。选择要获取的数据和天数，然后点击 Refresh 完成设置。",
                "Refresh Now",
            ),
        }
        title, body, action = step_content[self.onboarding_step]
        markers = []
        for index, label in enumerate(("创建账户", "登录", "刷新"), start=1):
            marker = "✓" if index < self.onboarding_step else "●" if index == self.onboarding_step else "○"
            markers.append(f"{marker} {label}")

        self.onboarding_title.setText(f"首次使用引导 · {title}")
        self.onboarding_progress.setText("   →   ".join(markers))
        self.onboarding_body.setText(body)
        self.onboarding_action_button.setText(action)
        self.onboarding_panel.show()
        self.help_hint.hide()
        self._update_onboarding_targets()

    def _run_onboarding_action(self) -> None:
        self.tabs.setCurrentIndex(0)
        if self.onboarding_step == 1:
            self.update_auth_button.click()
        elif self.onboarding_step == 2:
            self.student_id_input.setFocus()
        else:
            self.refresh_button.click()

    def _update_onboarding_targets(self) -> None:
        self._clear_onboarding_targets()
        if self.onboarding_step == 1:
            targets = (self.update_auth_button,)
        elif self.onboarding_step == 2:
            targets = (self.student_id_input, self.password_input, self.login_button)
        else:
            targets = (self.refresh_button,)

        for widget in targets:
            self._set_onboarding_target(widget, True)

    def _clear_onboarding_targets(self) -> None:
        targets = (
            self.update_auth_button,
            self.student_id_input,
            self.password_input,
            self.login_button,
            self.refresh_button,
        )
        for widget in targets:
            self._set_onboarding_target(widget, False)

    def _set_onboarding_target(self, widget: QWidget, enabled: bool) -> None:
        widget.setProperty("onboardingTarget", "true" if enabled else "false")
        widget.style().unpolish(widget)
        widget.style().polish(widget)
        widget.update()

    def _set_login_status(self, logged_in: bool) -> None:
        if logged_in:
            text = "● Logged In"
            background = "#e5f6eb"
            border = "#2e8b57"
            foreground = "#17623b"
        else:
            text = "● Not Logged In"
            background = "#fff3dc"
            border = "#d89020"
            foreground = "#7a4700"

        self.login_state_label.setText(text)
        self.login_state_label.setStyleSheet(
            "QLabel {"
            f"background: {background}; border: 2px solid {border}; "
            f"color: {foreground}; border-radius: 7px; "
            "font-weight: 700; padding: 7px 11px;"
            "}"
        )

    def _set_content_access(self, can_view_content: bool) -> None:
        self._set_login_status(can_view_content)
        self.tabs.setTabEnabled(1, can_view_content)
        self.tabs.setTabEnabled(2, can_view_content)
        self.logout_button.setEnabled(can_view_content)
        self.refresh_button.setEnabled(can_view_content)
        self.refresh_mode_selector.setEnabled(can_view_content)
        self.schedule_day_count_selector.setEnabled(can_view_content)
        self.auto_login_checkbox.setEnabled(can_view_content)
        self.delete_local_data_button.setEnabled(can_view_content)
        self.login_button.setEnabled(not can_view_content)

        if self.onboarding_active:
            self._sync_onboarding_step()

        if can_view_content:
            self.tabs.setCurrentIndex(1)
            self.set_error(None)
            return

        self.tabs.setCurrentIndex(0)

    def _render_profile(self, data: dict[str, Any]) -> None:
        fields = [
            ("Student", data.get("student_name", "Unknown")),
            ("Student ID", data.get("student_id", "Unknown")),
            ("Last Updated", data.get("last_updated", "Never")),
        ]
        for column, (label, value) in enumerate(fields):
            label_widget = QLabel(label)
            label_widget.setObjectName("mutedText")
            value_widget = QLabel(str(value))
            value_widget.setObjectName("sectionTitle")
            self.profile_layout.addWidget(label_widget, 0, column)
            self.profile_layout.addWidget(value_widget, 1, column)
            self.profile_layout.setColumnStretch(column, 1)

    def _render_courses(self, courses: list[dict[str, Any]]) -> None:
        self.current_courses = []
        if not courses:
            self.course_detail_layout.addWidget(QLabel("No course information available."))
            return

        self.current_courses = courses
        self.course_selector.blockSignals(True)
        for index, course in enumerate(courses):
            self.course_selector.addItem(str(course.get("name", f"Course {index + 1}")))
        self.course_selector.blockSignals(False)
        self.course_selector.setCurrentIndex(0)
        self._select_course(0)

    def _select_course(self, index: int) -> None:
        if index < 0 or index >= len(self.current_courses):
            return

        self._clear_layout(self.course_detail_layout)
        self.course_detail_layout.addWidget(self._course_detail_section(self.current_courses[index]))
        self.course_detail_layout.addStretch(1)

    def _course_detail_section(self, course: dict[str, Any]) -> QWidget:
        section = QWidget()
        layout = QVBoxLayout(section)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        name_group = QGroupBox("Name")
        name_layout = QVBoxLayout(name_group)
        name_label = QLabel(str(course.get("name", "Unnamed Course")))
        name_label.setObjectName("sectionTitle")
        name_layout.addWidget(name_label)

        description_group = QGroupBox("Description")
        description_layout = QVBoxLayout(description_group)
        description = QLabel(str(course.get("description", "No description available.")))
        description.setWordWrap(True)
        description_layout.addWidget(description)

        assignment_group = QGroupBox("Assignments")
        assignment_layout = QVBoxLayout(assignment_group)
        assignments = course.get("assignments", [])
        if assignments:
            filter_panel, filter_state, results_layout = self._assignment_filter_panel(assignments)
            assignment_layout.addWidget(filter_panel)
            assignment_layout.addLayout(results_layout)

            def refresh_assignments(*_: Any) -> None:
                self._render_filtered_assignments(assignments, results_layout, filter_state)

            filter_state["criterion"].currentIndexChanged.connect(refresh_assignments)
            filter_state["grade"].currentIndexChanged.connect(refresh_assignments)
            filter_state["status"].currentIndexChanged.connect(refresh_assignments)
            filter_state["keyword"].textChanged.connect(refresh_assignments)
            refresh_assignments()
        else:
            empty_message = QLabel("No assignments captured for this course. This course may not expose grade details yet.")
            empty_message.setWordWrap(True)
            assignment_layout.addWidget(empty_message)

        layout.addWidget(name_group)
        layout.addWidget(description_group)
        layout.addWidget(assignment_group)
        return section

    def _assignment_filter_panel(
        self,
        assignments: list[dict[str, Any]],
    ) -> tuple[QFrame, dict[str, Any], QVBoxLayout]:
        panel = QFrame()
        panel.setObjectName("filterPanel")
        layout = QGridLayout(panel)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setHorizontalSpacing(12)
        layout.setVerticalSpacing(8)

        criterion_filter = QComboBox()
        criterion_filter.addItem("All criteria", "")
        criterion_filter.setMinimumWidth(260)
        for criterion_type in self._assignment_filter_values(assignments, "type"):
            criterion_filter.addItem(criterion_type, criterion_type)

        grade_filter = QComboBox()
        grade_filter.addItem("All grades", "")
        grade_filter.setMinimumWidth(160)
        for grade in self._assignment_filter_values(assignments, "grade"):
            grade_filter.addItem(grade, grade)

        status_filter = QComboBox()
        status_filter.addItem("All status", "")
        status_filter.setMinimumWidth(180)
        status_filter.addItem("Graded", "graded")
        status_filter.addItem("Not graded", "not_graded")
        status_filter.addItem("Missing", "missing")
        status_filter.addItem("Excluded", "excluded")
        status_filter.addItem("Included", "included")

        keyword_filter = QLineEdit()
        keyword_filter.setPlaceholderText("Search name, type, grade, or comment")

        layout.addWidget(QLabel("Criteria / Type"), 0, 0)
        layout.addWidget(criterion_filter, 1, 0)
        layout.addWidget(QLabel("Grade"), 0, 1)
        layout.addWidget(grade_filter, 1, 1)
        layout.addWidget(QLabel("Status"), 0, 2)
        layout.addWidget(status_filter, 1, 2)
        layout.addWidget(QLabel("Keyword"), 0, 3)
        layout.addWidget(keyword_filter, 1, 3)
        layout.setColumnMinimumWidth(0, 280)
        layout.setColumnMinimumWidth(1, 170)
        layout.setColumnMinimumWidth(2, 190)
        layout.setColumnStretch(3, 1)

        results_layout = QVBoxLayout()
        results_layout.setContentsMargins(0, 0, 0, 0)
        results_layout.setSpacing(10)
        return panel, {
            "criterion": criterion_filter,
            "grade": grade_filter,
            "status": status_filter,
            "keyword": keyword_filter,
        }, results_layout

    def _render_filtered_assignments(
        self,
        assignments: list[dict[str, Any]],
        results_layout: QVBoxLayout,
        filter_state: dict[str, Any],
    ) -> None:
        self._clear_layout(results_layout)
        visible_assignments = [
            assignment
            for assignment in assignments
            if self._assignment_matches_filters(assignment, filter_state)
        ]

        if not visible_assignments:
            empty_message = QLabel("No assignments match the current filters.")
            empty_message.setWordWrap(True)
            results_layout.addWidget(empty_message)
            return

        for assignment in visible_assignments:
            results_layout.addWidget(self._assignment_card(assignment))

    def _assignment_matches_filters(
        self,
        assignment: dict[str, Any],
        filter_state: dict[str, Any],
    ) -> bool:
        criterion = filter_state["criterion"].currentData()
        grade = filter_state["grade"].currentData()
        status = filter_state["status"].currentData()
        keyword = filter_state["keyword"].text().strip().lower()

        assignment_criterion = str(assignment.get("type", "")).strip()
        assignment_grade = str(assignment.get("grade", "")).strip()
        assignment_status = self._assignment_status(assignment)
        is_excluded = bool(assignment.get("excluded_from_cumulative_grade", False))

        if criterion and assignment_criterion != criterion:
            return False
        if grade and assignment_grade != grade:
            return False
        if status == "excluded" and not is_excluded:
            return False
        if status == "included" and is_excluded:
            return False
        if status not in ("", None, "excluded", "included") and assignment_status != status:
            return False
        if keyword:
            searchable = " ".join(
                str(assignment.get(field, ""))
                for field in ("name", "type", "grade", "comment", "criterion", "grade_status")
            ).lower()
            if keyword not in searchable:
                return False

        return True

    def _assignment_filter_values(self, assignments: list[dict[str, Any]], field: str) -> list[str]:
        values = set()
        for assignment in assignments:
            value = str(assignment.get(field, "")).strip()
            if value:
                values.add(value)
        return sorted(values)

    def _assignment_status(self, assignment: dict[str, Any]) -> str:
        status = str(assignment.get("grade_status", "")).strip()
        if status:
            return status

        grade = str(assignment.get("grade", "")).strip()
        if not grade or grade == "N/A":
            return "missing"
        if grade.startswith("-"):
            return "not_graded"
        return "graded"

    def _assignment_card(self, assignment: dict[str, Any]) -> QFrame:
        frame = QFrame()
        frame.setObjectName("assignmentCard")
        layout = QGridLayout(frame)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setHorizontalSpacing(18)
        layout.setVerticalSpacing(6)

        name = QLabel(str(assignment.get("name", "Unnamed Assignment")))
        name.setObjectName("sectionTitle")
        name.setWordWrap(True)
        grade = QLabel(f"Grade: {assignment.get('grade', 'N/A')}")
        assignment_type = QLabel(f"Type: {assignment.get('type', 'N/A')}")
        assignment_type.setWordWrap(True)
        comment = QLabel(f"Comment: {assignment.get('comment', 'No comment')}")
        comment.setWordWrap(True)

        layout.addWidget(name, 0, 0)
        layout.addWidget(grade, 0, 1)
        layout.addWidget(assignment_type, 1, 1)
        layout.addWidget(comment, 2, 0, 1, 2)
        layout.setColumnStretch(0, 1)
        return frame

    def _render_schedule(self, schedule_days: list[dict[str, Any]]) -> None:
        self.current_schedule_days = []
        self.schedule_day_selector.blockSignals(True)
        self.schedule_day_selector.clear()
        self.schedule_day_selector.blockSignals(False)
        self.schedule_day_meta_label.clear()

        if not schedule_days:
            self.schedule_list_layout.addWidget(QLabel("No schedule information available."))
            return

        self.current_schedule_days = schedule_days
        self.schedule_day_selector.blockSignals(True)
        for index, day in enumerate(schedule_days):
            self.schedule_day_selector.addItem(self._schedule_day_label(day, index), index)
        self.schedule_day_selector.blockSignals(False)

        self.schedule_day_selector.setCurrentIndex(self._today_schedule_index(schedule_days))
        self._select_schedule_day(self.schedule_day_selector.currentIndex())

    def _select_schedule_day(self, index: int) -> None:
        self._clear_layout(self.schedule_list_layout)
        if index < 0 or index >= len(self.current_schedule_days):
            self.schedule_day_meta_label.clear()
            return

        day = self.current_schedule_days[index]
        self.schedule_day_meta_label.setText(str(day.get("day_type", "")))
        self.schedule_list_layout.addWidget(self._schedule_day_section(day))
        self.schedule_list_layout.addStretch(1)

    def _schedule_day_label(self, day: dict[str, Any], index: int) -> str:
        day_index = day.get("day_index", index + 1)
        date_text = str(day.get("date", "Date unavailable"))
        return f"Day {day_index} - {date_text}"

    def _today_schedule_index(self, schedule_days: list[dict[str, Any]]) -> int:
        today = date.today()
        for index, day in enumerate(schedule_days):
            parsed_date = self._parse_schedule_date(day.get("date", ""))
            if parsed_date == today:
                return index

        return 0

    def _parse_schedule_date(self, value: Any) -> date | None:
        text = str(value).strip()
        for date_format in ("%Y-%m-%d", "%A, %B %d, %Y", "%A, %b %d, %Y"):
            try:
                return datetime.strptime(text, date_format).date()
            except ValueError:
                continue

        return None

    def _schedule_day_section(self, day: dict[str, Any]) -> QFrame:
        frame = QFrame()
        frame.setObjectName("scheduleDaySection")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(14, 12, 14, 14)
        layout.setSpacing(10)

        day_banner = QFrame()
        day_banner.setObjectName("scheduleDayBanner")
        header = QHBoxLayout(day_banner)
        header.setContentsMargins(14, 10, 14, 10)
        date = QLabel(str(day.get("date", "Date unavailable")))
        date.setObjectName("scheduleDateTitle")
        day_type = QLabel(str(day.get("day_type", "Day type unavailable")))
        day_type.setObjectName("scheduleDayBadge")

        header.addWidget(date)
        header.addStretch(1)
        header.addWidget(day_type)
        layout.addWidget(day_banner)

        classes = day.get("classes", [])
        if not classes:
            layout.addWidget(QLabel("No classes listed for this day."))
            return frame

        schedule_date = self._display_schedule_date(day.get("date", ""))
        for index, item in enumerate(classes):
            card = self._schedule_card(item, schedule_date, alternate=bool(index % 2))
            layout.addWidget(card)
        return frame

    def _schedule_card(
        self,
        item: dict[str, Any],
        schedule_date: str = "",
        *,
        alternate: bool = False,
    ) -> QFrame:
        frame = QFrame()
        frame.setObjectName("scheduleCard")
        if alternate:
            frame.setProperty("cardVariant", "alternate")
        card_layout = QHBoxLayout(frame)
        card_layout.setContentsMargins(8, 10, 12, 10)
        card_layout.setSpacing(12)

        accent = QFrame()
        accent.setObjectName("scheduleAccent")
        accent.setFixedWidth(6)
        if alternate:
            accent.setProperty("accentVariant", "alternate")
        card_layout.addWidget(accent)

        content_layout = QVBoxLayout()
        content_layout.setSpacing(8)
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)

        time = QLabel(str(item.get("time", "Time unavailable")))
        time.setObjectName("scheduleTime")
        course_name = QLabel(str(item.get("course_name", item.get("title", "Course unavailable"))))
        course_name.setObjectName("scheduleCourseTitle")
        course_name.setWordWrap(True)
        block_value = self._field_text(item.get("block", "")) or "--"
        date_and_block = (
            f"{schedule_date}  •  Block {block_value}"
            if schedule_date
            else f"Block {block_value}"
        )
        block = QLabel(date_and_block)
        block.setObjectName("scheduleBlockBadge")
        teacher = QLabel(f"Teacher  ·  {item.get('teacher', 'Unavailable')}")
        teacher.setObjectName("scheduleTeacher")

        header_layout.addWidget(time)
        header_layout.addWidget(course_name, stretch=1)
        header_layout.addWidget(block)
        content_layout.addLayout(header_layout)
        content_layout.addWidget(teacher)
        detail_fields = self._schedule_detail_fields(item)
        if detail_fields:
            detail_panel = QFrame()
            detail_panel.setObjectName("scheduleDetails")
            detail_layout = QGridLayout(detail_panel)
            detail_layout.setContentsMargins(10, 8, 10, 8)
            detail_layout.setHorizontalSpacing(14)
            detail_layout.setVerticalSpacing(6)
            for row, (label, value) in enumerate(detail_fields):
                key_label = QLabel(label)
                key_label.setObjectName("scheduleDetailKey")
                value_label = QLabel(value)
                value_label.setWordWrap(True)
                detail_layout.addWidget(key_label, row, 0)
                detail_layout.addWidget(value_label, row, 1)
            detail_layout.setColumnStretch(1, 1)
            content_layout.addWidget(detail_panel)
        card_layout.addLayout(content_layout, stretch=1)
        return frame

    def _display_schedule_date(self, value: Any) -> str:
        parsed_date = self._parse_schedule_date(value)
        if parsed_date is None:
            return self._field_text(value)

        return parsed_date.strftime("%b %d, %Y").replace(" 0", " ")

    def _schedule_detail_fields(self, item: dict[str, Any]) -> list[tuple[str, str]]:
        fields = item.get("fields", {})
        details: list[tuple[str, str]] = []
        if isinstance(fields, dict):
            ignored_keys = {"time", "block", "course_name", "course", "activity", "acivity", "title", "teacher"}
            preferred_keys = ("attendance", "attandance", "contact", "details", "detail", "location", "room")
            used_keys = set()
            for key in preferred_keys:
                value = self._field_text(fields.get(key, ""))
                if value:
                    details.append((self._schedule_field_label(key), value))
                    used_keys.add(key)

            for key, value in fields.items():
                normalized_key = str(key)
                if normalized_key in ignored_keys or normalized_key in used_keys:
                    continue

                text = self._field_text(value)
                if text:
                    details.append((self._schedule_field_label(normalized_key), text))

        if details:
            return details

        detail_text = self._field_text(item.get("detail", ""))
        return self._parse_detail_text(detail_text) if detail_text else []

    def _parse_detail_text(self, detail_text: str) -> list[tuple[str, str]]:
        details = []
        for part in detail_text.split(";"):
            if ":" not in part:
                continue
            key, value = part.split(":", 1)
            key = key.strip()
            value = value.strip()
            if key and value:
                details.append((self._schedule_field_label(key), value))

        return details or [("Details", detail_text)]

    def _schedule_field_label(self, key: str) -> str:
        label_map = {
            "attandance": "Attendance",
            "attendance": "Attendance",
            "contact": "Contact",
            "details": "Details",
            "detail": "Details",
            "location": "Location",
            "room": "Room",
        }
        normalized_key = str(key).strip().lower()
        return label_map.get(normalized_key, normalized_key.replace("_", " ").title())

    def _field_text(self, value: Any) -> str:
        return "" if value is None else str(value).strip()

    def _clear_layout(self, layout: QVBoxLayout | QHBoxLayout | QGridLayout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            child = item.widget()
            if child is not None:
                child.deleteLater()


def run_app() -> int:
    app = QApplication(sys.argv)
    window = SmartLearningWindow()
    window.show()
    if hasattr(app, "exec"):
        return app.exec()
    return app.exec_()
