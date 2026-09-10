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

"""存储所有的标签和id名的class"""
@dataclass(frozen=True)
class CourseAcquisitionLocators:
    """Editable locators for the Progress course cards."""

    schedule_main_selector: str = "#col-main"
    schedule_header_selector: str = "#col-main #schedule-header"
    schedule_date_selector: str = "#col-main #schedule-header h2"
    schedule_day_type_selector: str = "div"
    schedule_rows_selector: str = "#col-main div.ch.schedule-list table tbody#accordionSchedules tr"
    schedule_cell_selector: str = "td[data-heading]"
    schedule_next_day_button_selector: str = "span.chCal-button-content"
    schedule_next_day_button_xpath: str = (
        "//*[@id='col-main']//span[contains(concat(' ', normalize-space(@class), ' '), ' chCal-button-content ') "
        "and contains(translate(normalize-space(.), '\u00a0', ' '), '►')]"
    )
    schedule_next_day_text: str = "►"
    schedule_rows_wait_seconds: int = 3

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
    schedule_info_acquired = pyqtSignal(dict)
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

    """两个接口函数: authentication succeed -> send signal to AC -> AC triggles this function"""
    def acquire_schedule_info(self, driver: WebDriver, day_count: int = 1) -> None:
        try:
            driver.switch_to.default_content()
            wait = WebDriverWait(driver, self.timeout_seconds)
            self._dismiss_welcome_if_present(driver)
            schedule = self._acquire_schedule_days(driver, wait, day_count)
        except TimeoutException as error:
            self.acquisition_failed.emit(f"Schedule acquisition timed out: {error.msg}")
            return
        except WebDriverException as error:
            self.acquisition_failed.emit(f"Selenium schedule acquisition error: {error.msg}")
            return

        self.schedule_info_acquired.emit(schedule)

    def acquire_course_info(
        self,
        driver: WebDriver,
        include_schedule: bool = False,
        schedule_day_count: int = 1,
    ) -> None:
        try:
            wait = WebDriverWait(driver, self.timeout_seconds)
            self._dismiss_welcome_if_present(driver)
            if include_schedule:
                schedule = self._acquire_schedule_days(driver, wait, schedule_day_count)
                self.schedule_info_acquired.emit(schedule)

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

        # Assignment acquisition debug prints are intentionally disabled for now.

        self.course_info_acquired.emit(courses)

    """Schedule部分的脚本"""
    def _acquire_schedule_days(
        self,
        driver: WebDriver,
        wait: WebDriverWait,
        day_count: int,
    ) -> dict[str, Any]:
        schedules = []
        """先获取需要获取的schedule的天数"""
        try:
            normalized_day_count = max(1, int(day_count))
        except (TypeError, ValueError):
            normalized_day_count = 1
        
        for day_index in range(normalized_day_count):
            """对于每一天获取daily schedule"""
            schedule = self._acquire_daily_schedule(driver, wait, day_index + 1) 
            if schedule:
                schedules.append(schedule) #追加到结果list

            if day_index >= normalized_day_count - 1:
                break
            
            current_date = schedule.get("date", "") if schedule else ""
            """找下一天的按钮"""
            if not self._go_to_next_schedule_day(driver, wait, current_date):
                self.acquisition_status.emit("Could not find the next schedule day button; stopping schedule acquisition.")
                break

        return {"schedule_days": schedules}

    def _acquire_daily_schedule(
        self,
        driver: WebDriver,
        wait: WebDriverWait,
        day_number: int = 1,
    ) -> dict[str, Any]:
        self.acquisition_status.emit(f"Acquiring schedule day {day_number}.")
        try:
            wait.until(lambda active_driver: self._switch_to_context_with_schedule(active_driver))
        except TimeoutException:
            self.acquisition_status.emit("Schedule container was not found; continuing to assignment acquisition.")
            return {}
        """有些天可能是blank，没有任何schedule"""
        self._wait_for_schedule_rows_or_empty_day(driver)
        """获取daily schedule"""
        schedule = self._extract_daily_schedule(driver)
        schedule["day_index"] = day_number
        return schedule

    """查找next day button"""
    def _go_to_next_schedule_day(self, driver: WebDriver, wait: WebDriverWait, current_date: str) -> bool:
        next_button = self._find_next_schedule_day_button(driver)
        if next_button is not None:
            self.acquisition_status.emit("Opening next schedule day.")
            self._click_element(driver, next_button)
        elif self._click_next_schedule_day_with_js(driver):
            self.acquisition_status.emit("Opening next schedule day.")
        else:
            return False

        if not current_date:
            wait.until(lambda active_driver: self._switch_to_context_with_schedule(active_driver))
            return True

        wait.until(lambda active_driver: self._current_schedule_date(active_driver) != current_date)
        self._wait_for_schedule_rows_or_empty_day(driver)
        return True

    def _find_next_schedule_day_button(self, driver: WebDriver) -> WebElement | None:
        button = self._find_next_schedule_day_button_in_current_context(driver)
        if button is not None:
            return button

        driver.switch_to.default_content()
        button = self._find_next_schedule_day_button_in_current_context(driver)
        if button is not None:
            return button

        frames = driver.find_elements(By.CSS_SELECTOR, self.locators.iframe_selector)
        for frame in frames:
            driver.switch_to.default_content()
            driver.switch_to.frame(frame)
            button = self._find_next_schedule_day_button_in_current_context(driver)
            if button is not None:
                return button

        driver.switch_to.default_content()
        return None

    def _find_next_schedule_day_button_in_current_context(self, driver: WebDriver) -> WebElement | None:
        elements = driver.find_elements(By.XPATH, self.locators.schedule_next_day_button_xpath)
        for element in elements:
            clickable_element = self._clickable_schedule_ancestor(element)
            if clickable_element is not None:
                return clickable_element

        for element in self._schedule_next_button_candidates(driver):
            text = self._normalized_visible_text(element)
            if text == self.locators.schedule_next_day_text:
                clickable_element = self._clickable_schedule_ancestor(element)
                if clickable_element is not None:
                    return clickable_element

        return None

    def _clickable_schedule_ancestor(self, element: WebElement) -> WebElement | None:
        clickable_ancestors = element.find_elements(By.XPATH, "./ancestor::*[self::button or self::a][1]")
        return clickable_ancestors[0] if clickable_ancestors else element

    def _click_next_schedule_day_with_js(self, driver: WebDriver) -> bool:
        if self._click_next_schedule_day_with_js_in_current_context(driver):
            return True

        driver.switch_to.default_content()
        if self._click_next_schedule_day_with_js_in_current_context(driver):
            return True

        frames = driver.find_elements(By.CSS_SELECTOR, self.locators.iframe_selector)
        for frame in frames:
            driver.switch_to.default_content()
            driver.switch_to.frame(frame)
            if self._click_next_schedule_day_with_js_in_current_context(driver):
                return True

        driver.switch_to.default_content()
        return False

    def _click_next_schedule_day_with_js_in_current_context(self, driver: WebDriver) -> bool:
        return bool(
            driver.execute_script(
                """
                const root = document.querySelector(arguments[2]) || document;
                const spans = Array.from(root.querySelectorAll(arguments[0]));
                const target = spans.find((span) => (
                    (span.textContent || '').replace(/\\u00a0/g, ' ').trim() === arguments[1]
                ));
                if (!target) {
                    return false;
                }
                const clickable = target.closest('button, a') || target;
                clickable.click();
                return true;
                """,
                self.locators.schedule_next_day_button_selector,
                self.locators.schedule_next_day_text,
                self.locators.schedule_main_selector,
            )
        )

    def _schedule_next_button_candidates(self, driver: WebDriver) -> list[WebElement]:
        root = self._find_first(driver, self.locators.schedule_main_selector)
        if root is None:
            return []

        return root.find_elements(By.CSS_SELECTOR, self.locators.schedule_next_day_button_selector)
    
    def _extract_daily_schedule(self, driver: WebDriver) -> dict[str, Any]:
        self._switch_to_context_with_schedule(driver)
        header = self._find_first(driver, self.locators.schedule_header_selector)
        date = self._text_from_optional_element(
            self._find_first(driver, self.locators.schedule_date_selector)
        )
        day_type = self._first_non_date_header_text(header, date)

        rows = self._extract_schedule_rows_with_js(driver)
        if not rows:
            rows = []
            for row in driver.find_elements(By.CSS_SELECTOR, self.locators.schedule_rows_selector):
                row_data = self._extract_schedule_row(row)
                if row_data:
                    rows.append(row_data)

        return {
            "date": date,
            "day_type": day_type,
            "rows": rows,
        }

    """有些天可能是blank，没有任何schedule"""
    def _wait_for_schedule_rows_or_empty_day(self, driver: WebDriver) -> None:
        short_wait = WebDriverWait(driver, self.locators.schedule_rows_wait_seconds)
        try:
            short_wait.until(lambda active_driver: bool(self._extract_schedule_rows_with_js(active_driver)))
        except TimeoutException:
            self.acquisition_status.emit("No schedule rows appeared in the wait window; treating this day as empty.")

    def _switch_to_context_with_schedule(self, driver: WebDriver) -> bool:
        if self._context_has_schedule_rows(driver):
            return True

        driver.switch_to.default_content()
        if self._context_has_schedule_rows(driver):
            return True

        frames = driver.find_elements(By.CSS_SELECTOR, self.locators.iframe_selector)
        for frame in frames:
            driver.switch_to.default_content()
            driver.switch_to.frame(frame)
            if self._context_has_schedule_rows(driver):
                return True

        driver.switch_to.default_content()
        if self._context_has_schedule_header(driver):
            return True

        frames = driver.find_elements(By.CSS_SELECTOR, self.locators.iframe_selector)
        for frame in frames:
            driver.switch_to.default_content()
            driver.switch_to.frame(frame)
            if self._context_has_schedule_header(driver):
                return True

        driver.switch_to.default_content()
        return False

    def _context_has_schedule_rows(self, driver: WebDriver) -> bool:
        return bool(self._extract_schedule_rows_with_js(driver))

    def _context_has_schedule_header(self, driver: WebDriver) -> bool:
        return bool(driver.find_elements(By.CSS_SELECTOR, self.locators.schedule_date_selector))

    def _current_schedule_date(self, driver: WebDriver) -> str:
        self._switch_to_context_with_schedule(driver)
        return self._text_from_optional_element(
            self._find_first(driver, self.locators.schedule_date_selector)
        )

    def _extract_schedule_row(self, row: WebElement) -> dict[str, str]:
        row_data: dict[str, str] = {}
        for cell in row.find_elements(By.CSS_SELECTOR, self.locators.schedule_cell_selector):
            heading = (cell.get_attribute("data-heading") or "").strip()
            if not heading:
                continue
            row_data[heading] = (cell.text or cell.get_attribute("textContent") or "").strip()

        return row_data

    def _extract_schedule_rows_with_js(self, driver: WebDriver) -> list[dict[str, str]]:
        rows = driver.execute_script(
            """
            const root = document.querySelector(arguments[0]) || document;
            return Array.from(root.querySelectorAll('tr'))
                .map((row) => {
                    const cells = Array.from(row.querySelectorAll(arguments[1]));
                    const data = {};
                    for (const cell of cells) {
                        const heading = (cell.getAttribute('data-heading') || '').trim();
                        if (heading) {
                            data[heading] = (cell.textContent || '').replace(/\\u00a0/g, ' ').trim();
                        }
                    }
                    return data;
                })
                .filter((row) => Object.keys(row).length > 0);
            """,
            self.locators.schedule_main_selector,
            self.locators.schedule_cell_selector,
        )
        return rows if isinstance(rows, list) else []

    def _first_non_date_header_text(self, header: WebElement | None, date: str) -> str:
        if header is None:
            return ""

        for element in header.find_elements(By.CSS_SELECTOR, self.locators.schedule_day_type_selector):
            text = (element.text or element.get_attribute("textContent") or "").strip()
            for line in [item.strip() for item in text.splitlines() if item.strip()]:
                if line and line != date:
                    return line

        return ""

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
        self._click_element(driver, grade_details)
        criteria_container = self._wait_for_criteria_container(wait)

        assignments: list[dict[str, str]] = []
        criteria_count = len(criteria_container.find_elements(By.CSS_SELECTOR, self.locators.criteria_item_selector))
        self.acquisition_status.emit(f"Found {criteria_count} criteria groups.")
        for criteria_index in range(criteria_count):
            criteria_container = self._find_criteria_container(driver)
            criteria_items = criteria_container.find_elements(By.CSS_SELECTOR, self.locators.criteria_item_selector)
            if criteria_index >= len(criteria_items):
                break

            criteria_button = self._find_criteria_button(criteria_items[criteria_index])
            if criteria_button is None:
                continue

            assignment_type = (criteria_button.text or criteria_button.get_attribute("textContent") or "").strip()
            if not assignment_type:
                assignment_type = f"Criteria {criteria_index + 1}"
            self.acquisition_status.emit(f"Opening grade criteria {criteria_index + 1}: {assignment_type}.")
            self._click_element(driver, criteria_button)
            grid = self._wait_for_css(wait, self.locators.assignment_grid_selector, f"assignment grid for {assignment_type}")
            criteria_assignments = self._extract_assignments_from_grid(grid, assignment_type)
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

    def _wait_for_criteria_container(self, wait: WebDriverWait) -> WebElement:
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
                return elements[0]

        elements = driver.find_elements(By.XPATH, self.locators.criteria_container_xpath)
        if elements:
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
        for frame in frames:
            driver.switch_to.default_content()
            driver.switch_to.frame(frame)
            container = self._find_criteria_container_in_current_context(driver)
            if container is not None:
                return container

        driver.switch_to.default_content()
        return None

    def _wait_for_css(self, wait: WebDriverWait, selector: str, label: str) -> WebElement:
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

    def _find_criteria_button(self, criteria_item: WebElement) -> WebElement | None:
        buttons = criteria_item.find_elements(By.CSS_SELECTOR, self.locators.criteria_button_selector)
        if buttons:
            return buttons[0]
        return None

    """登陆后可能会弹出welcome窗口，先点掉"""
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

    def _text_from_optional_element(self, element: WebElement | None) -> str:
        if element is None:
            return ""

        return (element.text or element.get_attribute("textContent") or "").strip()

    def _normalized_visible_text(self, element: WebElement) -> str:
        text = element.text or element.get_attribute("textContent") or ""
        return " ".join(text.replace("\xa0", " ").split())

    def _find_optional(self, row: WebElement, selector: str) -> WebElement | None:
        elements = row.find_elements(By.CSS_SELECTOR, selector)
        return elements[0] if elements else None

    def _find_first(self, root: WebDriver | WebElement | None, selector: str) -> WebElement | None:
        if root is None:
            return None

        elements = root.find_elements(By.CSS_SELECTOR, selector)
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
