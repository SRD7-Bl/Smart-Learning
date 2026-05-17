"""Information acquisition module for Smart Learning."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from Frontend.qt_compat import QObject, pyqtSignal


@dataclass(frozen=True)
class CourseAcquisitionLocators:
    """Editable locators for the Progress course cards."""

    progress_tab_by: str = By.ID
    progress_tab_value: str = "progress-btn"
    welcome_close_selector: str = "a.close.fa.fa-times"
    courses_container_by: str = By.ID
    courses_container_value: str = "coursesContainer"
    course_row_selector: str = "#coursesContainer > div.row"
    course_name_selector: str = "div:nth-of-type(1) a h3"
    course_description_selector: str = "div:nth-of-type(1) div.collapse p"
    teacher_selector: str = "div:nth-of-type(5) h4.group-owner-name"
    grade_details_selector: str = "div:nth-of-type(4) a"


class InformationAcquisitionModule(QObject):
    """Acquire raw course information from TigerNet after authentication."""

    course_info_acquired = pyqtSignal(list)
    acquisition_failed = pyqtSignal(str)
    acquisition_status = pyqtSignal(str)

    def __init__(
        self,
        parent: QObject | None = None,
        locators: CourseAcquisitionLocators | None = None,
        timeout_seconds: int = 15,
    ) -> None:
        super().__init__(parent)
        self.locators = locators or CourseAcquisitionLocators()
        self.timeout_seconds = timeout_seconds

    def acquire_course_info(self, driver: WebDriver) -> None:
        try:
            wait = WebDriverWait(driver, self.timeout_seconds)
            self._dismiss_welcome_if_present(driver)
            self.acquisition_status.emit("Opening Progress tab.")
            progress_tab = wait.until(
                EC.element_to_be_clickable((self.locators.progress_tab_by, self.locators.progress_tab_value))
            )
            progress_tab.click()

            self.acquisition_status.emit("Waiting for course cards.")
            wait.until(
                EC.presence_of_element_located(
                    (self.locators.courses_container_by, self.locators.courses_container_value)
                )
            )
            course_rows = driver.find_elements(By.CSS_SELECTOR, self.locators.course_row_selector)
            if not course_rows:
                self.acquisition_failed.emit("No course cards were found in the Progress tab.")
                return

            courses = [self._extract_course_info(row, index) for index, row in enumerate(course_rows, start=1)]
        except TimeoutException as error:
            self.acquisition_failed.emit(f"Course acquisition timed out: {error.msg}")
            return
        except WebDriverException as error:
            self.acquisition_failed.emit(f"Selenium acquisition error: {error.msg}")
            return

        print("InformationAcquisitionModule course info:")
        for course in courses:
            print(course)

        self.course_info_acquired.emit(courses)

    def _dismiss_welcome_if_present(self, driver: WebDriver) -> None:
        close_buttons = driver.find_elements(By.CSS_SELECTOR, self.locators.welcome_close_selector)
        if not close_buttons:
            return

        try:
            close_buttons[0].click()
            self.acquisition_status.emit("Closed welcome popup.")
        except WebDriverException:
            self.acquisition_status.emit("Welcome popup close button was present but could not be clicked.")

    def _extract_course_info(self, row: WebElement, index: int) -> dict[str, Any]:
        grade_details = self._find_optional(row, self.locators.grade_details_selector)
        return {
            "index": index,
            "name": self._text_from_selector(row, self.locators.course_name_selector),
            "description": self._text_from_selector(row, self.locators.course_description_selector),
            "teacher": self._text_from_selector(row, self.locators.teacher_selector),
            "grade_details_href": grade_details.get_attribute("href") if grade_details else "",
            "grade_details_analysis_id": grade_details.get_attribute("data-analysis") if grade_details else "",
        }

    def _text_from_selector(self, row: WebElement, selector: str) -> str:
        element = self._find_optional(row, selector)
        if element is None:
            return ""

        return (element.get_attribute("textContent") or element.text).strip()

    def _find_optional(self, row: WebElement, selector: str) -> WebElement | None:
        elements = row.find_elements(By.CSS_SELECTOR, selector)
        return elements[0] if elements else None
