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
    grade_details_selector: str = 'div:nth-of-type(4) a[data-analysis]'
    grade_details_fallback_selector: str = "div:nth-of-type(4) a"

    # Grade Detail Part
    criteria_container_selector: str = 'div.sky-repeater[role="grid"]'
    criteria_container_fallback_selector: str = 'div[aria-label="List of items"]'
    criteria_container_xpath: str = '//div[contains(@class, "sky-repeater") and @role="grid"]'
    iframe_selector: str = "iframe"
    criteria_item_selector: str = "sky-repeater-item"
    criteria_button_selector: str = "button"
    assignment_grid_selector: str = "div.ag-center-cols-container"
    assignment_row_selector: str = "div[row-index]"
    assignment_name_cell_selector: str = 'div[col-id="AssignmentShortDescription"]'
    assignment_points_cell_selector: str = 'div[col-id="Points"]'
    assignment_comment_cell_selector: str = 'div[col-id="Comment"]'
    modal_close_button_selector: str = "div.sky-modal-footer-container button"


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

            courses = []
            for index in range(1, len(course_rows) + 1):
                driver.switch_to.default_content()
                rows = driver.find_elements(By.CSS_SELECTOR, self.locators.course_row_selector)
                course = self._extract_course_info(rows[index - 1], index)
                course["assignments"] = self._acquire_grade_details(driver, wait, rows[index - 1])
                courses.append(course)
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

    def _acquire_grade_details(
        self,
        driver: WebDriver,
        wait: WebDriverWait,
        row: WebElement,
    ) -> list[dict[str, str]]:
        grade_details = self._find_grade_details_link(row)
        if grade_details is None:
            self.acquisition_status.emit("Course has no grade details link; skipping assignments.")
            return []

        self.acquisition_status.emit("Opening grade details.")
        print("InformationAcquisitionModule: clicking grade details link")
        self._click_element(driver, grade_details)
        criteria_container = self._wait_for_criteria_container(wait)

        assignments: list[dict[str, str]] = []
        criteria_count = len(criteria_container.find_elements(By.CSS_SELECTOR, self.locators.criteria_item_selector))
        self.acquisition_status.emit(f"Found {criteria_count} criteria groups.")
        print(f"InformationAcquisitionModule: criteria count = {criteria_count}")
        for criteria_index in range(criteria_count):
            criteria_container = self._find_criteria_container(driver)
            criteria_items = criteria_container.find_elements(By.CSS_SELECTOR, self.locators.criteria_item_selector)
            if criteria_index >= len(criteria_items):
                break

            criteria_button = self._find_criteria_button(criteria_items[criteria_index], criteria_index + 1)
            if criteria_button is None:
                continue

            assignment_type = (criteria_button.text or criteria_button.get_attribute("textContent") or "").strip()
            if not assignment_type:
                assignment_type = f"Criteria {criteria_index + 1}"
            self.acquisition_status.emit(f"Opening grade criteria {criteria_index + 1}: {assignment_type}.")
            print(f"InformationAcquisitionModule: clicking criteria {criteria_index + 1}: {assignment_type}")
            self._click_element(driver, criteria_button)
            grid = self._wait_for_css(wait, self.locators.assignment_grid_selector, f"assignment grid for {assignment_type}")
            criteria_assignments = self._extract_assignments_from_grid(grid, assignment_type)
            print(
                "InformationAcquisitionModule:",
                f"criteria {criteria_index + 1} assignment rows = {len(criteria_assignments)}",
            )
            assignments.extend(criteria_assignments)

        self.acquisition_status.emit("Closing grade details.")
        self._close_grade_details(driver, wait)
        driver.switch_to.default_content()
        return assignments

    def _extract_assignments_from_grid(
        self,
        grid: WebElement,
        assignment_type: str,
    ) -> list[dict[str, str]]:
        assignments = []
        rows = grid.find_elements(By.CSS_SELECTOR, self.locators.assignment_row_selector)
        for row in rows:
            assignments.append(
                {
                    "name": self._visible_text_from_selector(row, self.locators.assignment_name_cell_selector),
                    "grade": self._visible_text_from_selector(row, self.locators.assignment_points_cell_selector),
                    "type": assignment_type,
                    "comment": self._visible_text_from_selector(row, self.locators.assignment_comment_cell_selector),
                }
            )

        return assignments

    def _close_grade_details(self, driver: WebDriver, wait: WebDriverWait) -> None:
        close_button = wait.until(
            lambda active_driver: self._find_close_button(active_driver.find_elements(By.CSS_SELECTOR, self.locators.modal_close_button_selector))
        )
        self._click_element(driver, close_button)
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, self.locators.criteria_container_selector)))
        print("InformationAcquisitionModule: closed grade details")

    def _wait_for_criteria_container(self, wait: WebDriverWait) -> WebElement:
        print("InformationAcquisitionModule: waiting for criteria container")

        def condition(driver: WebDriver) -> WebElement | bool:
            container = self._find_criteria_container_in_current_context(driver)
            if container is not None:
                return container

            container = self._switch_to_frame_with_criteria_container(driver)
            return container if container is not None else False

        return wait.until(condition, message="Timed out waiting for criteria container.")

    def _find_criteria_container_in_current_context(self, driver: WebDriver) -> WebElement | None:
        selectors = [
            self.locators.criteria_container_selector,
            self.locators.criteria_container_fallback_selector,
        ]
        for selector in selectors:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if elements:
                print(f"InformationAcquisitionModule: criteria container matched CSS: {selector}")
                return elements[0]

        elements = driver.find_elements(By.XPATH, self.locators.criteria_container_xpath)
        if elements:
            print(f"InformationAcquisitionModule: criteria container matched XPath: {self.locators.criteria_container_xpath}")
            return elements[0]

        return None

    def _find_criteria_container(self, driver: WebDriver) -> WebElement | None:
        container = self._find_criteria_container_in_current_context(driver)
        if container is not None:
            return container

        return self._switch_to_frame_with_criteria_container(driver)

    def _switch_to_frame_with_criteria_container(self, driver: WebDriver) -> WebElement | None:
        driver.switch_to.default_content()
        frames = driver.find_elements(By.CSS_SELECTOR, self.locators.iframe_selector)
        print(f"InformationAcquisitionModule: scanning {len(frames)} iframe(s) for criteria container")
        for index, frame in enumerate(frames, start=1):
            driver.switch_to.default_content()
            driver.switch_to.frame(frame)
            container = self._find_criteria_container_in_current_context(driver)
            if container is not None:
                print(f"InformationAcquisitionModule: criteria container found in iframe {index}")
                return container

        driver.switch_to.default_content()
        return None

    def _wait_for_css(self, wait: WebDriverWait, selector: str, label: str) -> WebElement:
        print(f"InformationAcquisitionModule: waiting for {label}: {selector}")
        return wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, selector)),
            message=f"Timed out waiting for {label}: {selector}",
        )

    def _find_close_button(self, buttons: list[WebElement]) -> WebElement | bool:
        for button in buttons:
            button_text = (button.text or button.get_attribute("textContent") or "").strip().lower()
            if button_text == "close":
                return button
        return False

    def _find_criteria_button(self, criteria_item: WebElement, criteria_number: int) -> WebElement | None:
        buttons = criteria_item.find_elements(By.CSS_SELECTOR, self.locators.criteria_button_selector)
        if buttons:
            print(f"InformationAcquisitionModule: criteria {criteria_number} button count = {len(buttons)}")
            return buttons[0]

        outer_html = criteria_item.get_attribute("outerHTML") or ""
        print(
            f"InformationAcquisitionModule: criteria {criteria_number} has no button. "
            f"outerHTML starts with: {outer_html[:300]}"
        )
        return None

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
        grade_details = self._find_grade_details_link(row)
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

    def _visible_text_from_selector(self, row: WebElement, selector: str) -> str:
        element = self._find_optional(row, selector)
        if element is None:
            return ""

        return (element.text or element.get_attribute("textContent") or "").strip()

    def _find_optional(self, row: WebElement, selector: str) -> WebElement | None:
        elements = row.find_elements(By.CSS_SELECTOR, selector)
        return elements[0] if elements else None

    def _find_grade_details_link(self, row: WebElement) -> WebElement | None:
        grade_links = row.find_elements(By.CSS_SELECTOR, self.locators.grade_details_selector)
        for link in grade_links:
            if self._is_grade_details_link(link):
                return link

        fallback_links = row.find_elements(By.CSS_SELECTOR, self.locators.grade_details_fallback_selector)
        for link in fallback_links:
            if self._is_grade_details_link(link):
                return link

        return None

    def _is_grade_details_link(self, link: WebElement) -> bool:
        text = (link.text or link.get_attribute("textContent") or "").strip().lower()
        analysis_id = (link.get_attribute("data-analysis") or "").strip()
        return text == "see grade details" or bool(analysis_id)

    def _click_element(self, driver: WebDriver, element: WebElement) -> None:
        try:
            element.click()
        except WebDriverException:
            driver.execute_script("arguments[0].click();", element)
