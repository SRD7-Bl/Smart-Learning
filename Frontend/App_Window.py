"""Rendering module for the Smart Learning desktop application.

Day 1 focuses on a usable PyQt window and display framework. Interactive
widgets are wired into the User Input Module, but no backend workflow is
connected.
"""

from __future__ import annotations

import sys
from typing import Any

from Backend.Data_Access import DataAccessModule
from Frontend.Input_Module import UserInputModule
from Frontend.Request_Module import RequestSendingModule
from Frontend.Status_Error_Display import StatusErrorDisplayModule
from Frontend.qt_compat import (
    QApplication,
    ECHO_PASSWORD,
    NO_FRAME,
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

        self.setWindowTitle("Smart Learning")
        self.setMinimumSize(980, 680)
        self.resize(1120, 760)

        self._build_ui()
        self._connect_signal_board()
        self.render_academic_info(self.academic_info)
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
        main_layout.addWidget(self._build_content_area(), stretch=1)
        main_layout.addWidget(self._build_status_bar())

        self.setStyleSheet(
            """
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
            QLineEdit {
                background: #ffffff;
                border: 1px solid #cbd3df;
                border-radius: 6px;
                padding: 8px 10px;
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
            QPushButton:hover {
                border-color: #2364c8;
            }
            QPushButton#courseSelectorButton {
                background: #edf0f4;
                color: #20242a;
                min-width: 150px;
                padding: 10px 16px;
            }
            QPushButton#selectedCourseButton {
                background: #2364c8;
                border-color: #2364c8;
                color: #ffffff;
                min-width: 150px;
                padding: 10px 16px;
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
            QFrame#scheduleCard {
                background: #ffffff;
                border: 1px solid #d7dce3;
                border-radius: 8px;
            }
            QFrame#scheduleDaySection {
                background: #f8fafc;
                border: 1px solid #d7dce3;
                border-radius: 8px;
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
        )

    def _build_header(self) -> QWidget:
        header = QWidget()
        layout = QHBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 0)

        title_area = QVBoxLayout()
        self.title_label = QLabel("Smart Learning")
        self.title_label.setObjectName("appTitle")
        self.subtitle_label = QLabel("Academic dashboard rendering skeleton")
        self.subtitle_label.setObjectName("mutedText")
        title_area.addWidget(self.title_label)
        title_area.addWidget(self.subtitle_label)

        self.settings_button = QPushButton("Settings")
        self.settings_button.hide()
        self.logout_button = QPushButton("Log out")

        layout.addLayout(title_area, stretch=1)
        layout.addWidget(self.settings_button)
        layout.addWidget(self.logout_button)
        return header

    def _build_input_panel(self) -> QGroupBox:
        panel = QGroupBox("User Input Module Placeholder")
        layout = QGridLayout(panel)
        layout.setHorizontalSpacing(12)
        layout.setVerticalSpacing(10)

        self.student_id_input = QLineEdit()
        self.student_id_input.setPlaceholderText("Student ID")

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(ECHO_PASSWORD)

        self.login_button = QPushButton("Login")
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setObjectName("primaryButton")
        self.test_data_access_button = QPushButton("Test Data Access")

        layout.addWidget(QLabel("Student ID"), 0, 0)
        layout.addWidget(self.student_id_input, 0, 1)
        layout.addWidget(QLabel("Password"), 0, 2)
        layout.addWidget(self.password_input, 0, 3)
        layout.addWidget(self.login_button, 0, 4)
        layout.addWidget(self.refresh_button, 0, 5)
        layout.addWidget(self.test_data_access_button, 1, 4, 1, 2)
        layout.setColumnStretch(1, 1)
        layout.setColumnStretch(3, 1)
        return panel

    def _build_content_area(self) -> QTabWidget:
        self.tabs = QTabWidget()

        self.basic_tab = self._build_basic_tab()
        self.schedule_tab = self._build_schedule_tab()
        self.course_tab = self._build_course_tab()

        self.tabs.addTab(self.basic_tab, "Basic Info")
        self.tabs.addTab(self.schedule_tab, "Schedule")
        self.tabs.addTab(self.course_tab, "Courses & Assignments")
        self.tabs.setCurrentIndex(1)
        return self.tabs

    def _build_basic_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(14)

        layout.addWidget(self._build_input_panel())
        self.profile_group = QGroupBox("Student Overview")
        self.profile_layout = QGridLayout(self.profile_group)

        layout.addWidget(self.profile_group)
        layout.addStretch(1)
        return tab

    def _build_schedule_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(14)

        self.schedule_group = QGroupBox("Schedule")
        schedule_group_layout = QVBoxLayout(self.schedule_group)
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
        self.course_selector_layout = QHBoxLayout(self.course_selector_group)
        self.course_selector_layout.setSpacing(10)

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
        self.refresh_button.clicked.connect(self.input_module.request_refresh)
        self.settings_button.clicked.connect(self.input_module.request_settings)
        self.logout_button.clicked.connect(self.input_module.request_logout)
        self.login_button.clicked.connect(self._send_login_input)
        self.test_data_access_button.clicked.connect(self.data_access_module.request_all_data)
        self.input_module.content_access_changed.connect(self._set_content_access)
        self.input_module.validation_failed.connect(self.status_error_display.display_error)
        self.input_module.status_changed.connect(self.status_error_display.display_status)
        self.request_module.request_queued.connect(self.status_error_display.display_status)
        self.request_module.request_failed.connect(self.status_error_display.display_error)
        self.request_module.login_succeeded.connect(self._handle_login_succeeded)
        self.request_module.refresh_succeeded.connect(self.render_academic_info)
        self.input_module.logout_requested.connect(self._clear_login_inputs)
        self.data_access_module.all_data_loaded.connect(self._show_data_access_result)
        self.data_access_module.academic_info_loaded.connect(self.render_academic_info)
        self.data_access_module.data_access_failed.connect(self.status_error_display.display_error)
        self.status_error_display.status_ready.connect(self.set_status)

    def _send_login_input(self) -> None:
        self.input_module.request_login(
            self.student_id_input.text().strip(),
            self.password_input.text(),
        )
        self._clear_login_inputs()

    def render_academic_info(self, data: dict[str, Any]) -> None:
        self._clear_layout(self.profile_layout)
        self._clear_layout(self.schedule_list_layout)
        self._clear_layout(self.course_selector_layout)
        self._clear_layout(self.course_detail_layout)

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
        self._render_profile(
            {
                "student_name": user_settings.get("student", {}).get("display_name", "Unknown"),
                "student_id": user_settings.get("student", {}).get("student_id", "Unknown"),
                "last_updated": user_settings.get("last_successful_refresh", "Never"),
            }
        )

    def _clear_login_inputs(self) -> None:
        self.student_id_input.clear()
        self.password_input.clear()

    def _set_content_access(self, can_view_content: bool) -> None:
        self.tabs.setTabEnabled(1, can_view_content)
        self.tabs.setTabEnabled(2, can_view_content)
        self.logout_button.setEnabled(can_view_content)
        self.refresh_button.setEnabled(can_view_content)
        self.login_button.setEnabled(not can_view_content)

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
        if not courses:
            self.course_detail_layout.addWidget(QLabel("No course information available."))
            return

        self.current_courses = courses
        self.course_buttons = []
        for index, course in enumerate(courses):
            button = QPushButton(str(course.get("name", f"Course {index + 1}")))
            button.setCheckable(True)
            button.setObjectName("courseSelectorButton")
            button.clicked.connect(lambda checked=False, course_index=index: self._select_course(course_index))
            self.course_buttons.append(button)
            self.course_selector_layout.addWidget(button)

        self.course_selector_layout.addStretch(1)
        self._select_course(0)

    def _select_course(self, index: int) -> None:
        if index < 0 or index >= len(self.current_courses):
            return

        for button_index, button in enumerate(self.course_buttons):
            is_selected = button_index == index
            button.setChecked(is_selected)
            button.setObjectName("selectedCourseButton" if is_selected else "courseSelectorButton")
            button.style().unpolish(button)
            button.style().polish(button)

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
            for assignment in assignments:
                assignment_layout.addWidget(self._assignment_card(assignment))
        else:
            assignment_layout.addWidget(QLabel("No assignments listed for this course."))

        layout.addWidget(name_group)
        layout.addWidget(description_group)
        layout.addWidget(assignment_group)
        return section

    def _assignment_card(self, assignment: dict[str, Any]) -> QFrame:
        frame = QFrame()
        frame.setObjectName("assignmentCard")
        layout = QGridLayout(frame)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setHorizontalSpacing(18)
        layout.setVerticalSpacing(6)

        name = QLabel(str(assignment.get("name", "Unnamed Assignment")))
        name.setObjectName("sectionTitle")
        grade = QLabel(f"Grade: {assignment.get('grade', 'N/A')}")
        assignment_type = QLabel(f"Type: {assignment.get('type', 'N/A')}")
        comment = QLabel(f"Comment: {assignment.get('comment', 'No comment')}")
        comment.setWordWrap(True)

        layout.addWidget(name, 0, 0)
        layout.addWidget(grade, 0, 1)
        layout.addWidget(assignment_type, 1, 1)
        layout.addWidget(comment, 2, 0, 1, 2)
        layout.setColumnStretch(0, 1)
        return frame

    def _render_schedule(self, schedule_days: list[dict[str, Any]]) -> None:
        if not schedule_days:
            self.schedule_list_layout.addWidget(QLabel("No schedule information available."))
            return

        for day in schedule_days:
            self.schedule_list_layout.addWidget(self._schedule_day_section(day))
        self.schedule_list_layout.addStretch(1)

    def _schedule_day_section(self, day: dict[str, Any]) -> QFrame:
        frame = QFrame()
        frame.setObjectName("scheduleDaySection")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(14, 12, 14, 14)
        layout.setSpacing(10)

        header = QHBoxLayout()
        date = QLabel(str(day.get("date", "Date unavailable")))
        date.setObjectName("sectionTitle")
        day_type = QLabel(str(day.get("day_type", "Day type unavailable")))
        day_type.setObjectName("mutedText")

        header.addWidget(date)
        header.addStretch(1)
        header.addWidget(day_type)
        layout.addLayout(header)

        classes = day.get("classes", [])
        if not classes:
            layout.addWidget(QLabel("No classes listed for this day."))
            return frame

        for item in classes:
            layout.addWidget(self._schedule_card(item))
        return frame

    def _schedule_card(self, item: dict[str, Any]) -> QFrame:
        frame = QFrame()
        frame.setObjectName("scheduleCard")
        layout = QGridLayout(frame)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setHorizontalSpacing(18)
        layout.setVerticalSpacing(6)

        time = QLabel(str(item.get("time", "Time unavailable")))
        time.setObjectName("sectionTitle")
        course_name = QLabel(str(item.get("course_name", item.get("title", "Course unavailable"))))
        course_name.setObjectName("sectionTitle")
        block = QLabel(f"Block: {item.get('block', 'N/A')}")
        teacher = QLabel(f"Teacher: {item.get('teacher', 'Unavailable')}")
        teacher.setObjectName("mutedText")
        detail = QLabel(str(item.get("detail", "No details available")))
        detail.setWordWrap(True)

        layout.addWidget(time, 0, 0)
        layout.addWidget(course_name, 0, 1)
        layout.addWidget(block, 0, 2)
        layout.addWidget(teacher, 1, 1)
        layout.addWidget(detail, 2, 1, 1, 2)
        layout.setColumnStretch(1, 1)
        return frame

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
