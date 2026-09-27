from __future__ import annotations

import os
from unittest.mock import patch

from cryptography.fernet import Fernet

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from Backend.Application_Controller import ApplicationController
from Backend.Data_Access import DataAccessModule
from Frontend.App_Window import SmartLearningWindow
from Frontend.Input_Module import UserInputModule
from Frontend.Request_Module import RequestSendingModule
from Frontend.qt_compat import QApplication, QLabel, QDate


def test_account_button_and_password_prompt_follow_configuration_state(tmp_path) -> None:
    app = QApplication.instance() or QApplication([])
    key = Fernet.generate_key().decode("ascii")

    with patch("Backend.Encryption.keyring.get_password", return_value=key):
        data_access = DataAccessModule(storage_dir=tmp_path)
        controller = ApplicationController(data_access_module=data_access)
        assert controller.authentication_module.data_access_module is data_access
        assert controller.processor_module.data_access_module is data_access
        request_module = RequestSendingModule(application_controller=controller)
        input_module = UserInputModule(
            settings_path=data_access.user_settings_path,
            request_module=request_module,
        )
        window = SmartLearningWindow(
            input_module=input_module,
            request_module=request_module,
            data_access_module=data_access,
        )
        assert window.data_access_module is controller.data_access_module

        assert window.update_auth_button.text() == "Create a New Account"
        assert window.update_auth_button.objectName() == "accountButton"
        basic_layout = window.basic_content.layout()
        assert basic_layout.itemAt(0).widget() is window.account_management_group
        assert basic_layout.itemAt(1).widget() is window.account_controls_group
        assert window.basic_scroll.widgetResizable() is True
        assert window.login_notice.text() == "请使用与 TigerNet 登录相同的邮箱和密码"
        assert window.login_state_label.text() == "● Not Logged In"
        assert window.onboarding_active is True
        assert window.onboarding_step == 1
        assert window.onboarding_panel.isHidden() is False
        assert window.first_use_checkbox.isEnabled() is True
        assert window.tabs.count() == 4
        assert window.tabs.tabText(3) == "Assignment Calendar"
        assert window.tabs.isTabEnabled(3) is False

        window.theme_toggle.setChecked(True)
        assert input_module.dark_mode_enabled is True
        assert window.theme_toggle.text() == "☀ Light"
        assert window.basic_tab.styleSheet()
        assert data_access._read_user_settings()["dark_mode"] is True

        window.theme_toggle.setChecked(False)
        assert input_module.dark_mode_enabled is False
        assert window.theme_toggle.text() == "☾ Dark"
        assert window.basic_tab.styleSheet() == ""
        assert data_access._read_user_settings()["dark_mode"] is False

        window.first_use_checkbox.setChecked(False)
        assert input_module.is_first_use is False
        assert window.onboarding_panel.isHidden() is True
        assert data_access._read_user_settings()["is_first_use"] is False

        window.first_use_checkbox.setChecked(True)
        assert input_module.is_first_use is True
        assert window.onboarding_step == 1
        assert window.onboarding_panel.isHidden() is False
        assert data_access._read_user_settings()["is_first_use"] is True

        window._set_content_access(True)
        assert window.login_state_label.text() == "● Logged In"
        assert window.tabs.isTabEnabled(3) is True

        window._set_content_access(False)
        assert window.login_state_label.text() == "● Not Logged In"

        with (
            patch(
                "Frontend.App_Window.QInputDialog.getText",
                side_effect=[("student@example.com", True), ("new-password", True)],
            ) as create_prompts,
            patch("Frontend.App_Window.QMessageBox.information"),
        ):
            window._update_auth_credentials()

        assert create_prompts.call_count == 2
        assert window.update_auth_button.text() == "Change Email/Password"
        assert window.onboarding_step == 2

        with (
            patch(
                "Frontend.App_Window.QInputDialog.getText",
                side_effect=[
                    ("new-password", True),
                    ("updated@example.com", True),
                    ("updated-password", True),
                ],
            ) as change_prompts,
            patch("Frontend.App_Window.QMessageBox.information"),
        ):
            window._update_auth_credentials()

        assert change_prompts.call_count == 3
        assert data_access._read_user_settings()["auth"] == {
            "student_id": "updated@example.com",
            "password": "updated-password",
        }

        with patch("Frontend.App_Window.QMessageBox.information"):
            request_module.login_succeeded.emit(
                {"student": {"display_name": "Test Student", "student_id": "000000"}}
            )
        assert input_module.is_first_use is True
        assert window.onboarding_step == 3

        request_module.refresh_succeeded.emit({})
        assert input_module.is_first_use is False
        assert window.onboarding_active is False
        assert window.onboarding_panel.isHidden() is True
        assert data_access._read_user_settings()["is_first_use"] is False

        window._render_schedule(
            [
                {
                    "date": "2026-09-25",
                    "day_type": "A Day",
                    "classes": [
                        {
                            "time": "9:10 AM - 9:50 AM",
                            "course_name": "Economics",
                            "block": "5",
                            "teacher": "Test Teacher",
                            "fields": {"location": "Room 101"},
                        },
                        {
                            "time": "9:55 AM - 10:35 AM",
                            "course_name": "Chemistry",
                            "block": "6",
                            "teacher": "Test Teacher",
                        },
                    ],
                }
            ]
        )
        day_section = window.schedule_list_layout.itemAt(0).widget()
        labels = day_section.findChildren(QLabel)
        block_badges = [
            label.text() for label in labels if label.objectName() == "scheduleBlockBadge"
        ]
        assert block_badges == [
            "Sep 25, 2026  •  Block 5",
            "Sep 25, 2026  •  Block 6",
        ]

        window._load_assignment_calendar(
            [
                {
                    "name": "Chemistry",
                    "assignments": [
                        {
                            "name": "Lab Report",
                            "type": "Criteria B",
                            "grade": "--/8",
                            "due_date": "09/28/2026",
                        },
                        {
                            "name": "Reflection",
                            "type": "Criteria D",
                            "grade": "7/8",
                            "due_date": "",
                        },
                    ],
                }
            ]
        )
        assert window.assignment_calendar_summary.text() == (
            "2 assignment(s)  •  1 dated  •  1 without date"
        )
        assert window._parse_assignment_date("Sep 28, 2026").isoformat() == "2026-09-28"
        window.assignment_calendar.setSelectedDate(QDate(2026, 9, 28))
        window._render_calendar_agenda()
        agenda_labels = [label.text() for label in window.assignment_agenda.findChildren(QLabel)]
        assert "Lab Report" in agenda_labels
        assert "Reflection" in agenda_labels
        assert "Date not available  ·  1" in agenda_labels

        window.close()
        app.processEvents()
