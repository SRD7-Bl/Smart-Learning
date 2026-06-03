"""Selenium authentication module for Smart Learning."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from Backend.Data_Access import DataAccessModule
from Frontend.qt_compat import QObject, pyqtSignal


class AuthenticationConfigurationError(ValueError):
    """Raised when required Selenium locators are not configured."""

"""集中存储所有标签/id名等可能会影响脚本结果的‘脆弱’参数"""
@dataclass(frozen=True)
class LocatorConfig:
    """Editable Selenium locators for the TigerNet login flow."""

    login_url: str = "https://ridleycollege.myschoolapp.com/app?svcid=edu#login"
    username_by: str = By.ID
    username_value: str = "Username"
    username_next_by: str = By.ID
    username_next_value: str = "nextBtn"
    password_by: str = By.ID
    password_value: str = "i0118"
    password_next_by: str = By.ID
    password_next_value: str = "idSIButton9"
    success_by: str = By.CLASS_NAME
    success_value: str = "bb-tile-header"


class AuthenticationModule(QObject):
    """Authenticate against TigerNet using credentials from local data access."""

    authentication_succeeded = pyqtSignal(object)
    authentication_failed = pyqtSignal(str)
    authentication_status = pyqtSignal(str)

    def __init__(
        self,
        parent: QObject | None = None,
        data_access_module: DataAccessModule | None = None,
        locator_config: LocatorConfig | None = None,
        headless: bool = False,
        timeout_seconds: int = 15,
    ) -> None:
        super().__init__(parent)
        self.data_access_module = data_access_module or DataAccessModule(self)
        self.locators = locator_config or LocatorConfig()
        self.headless = headless
        self.timeout_seconds = timeout_seconds
        self.driver: WebDriver | None = None
        self._connect_data_access()

    def _connect_data_access(self) -> None:
        self.data_access_module.auth_credentials_loaded.connect(self._run_login_flow)
        self.data_access_module.data_access_failed.connect(self.authentication_failed.emit)

    def request_authentication(self) -> None:
        self.authentication_status.emit("Authentication requested. Loading local credentials.")
        self.data_access_module.request_auth_credentials()

    def close_driver(self) -> None:
        if self.driver is None:
            return

        try:
            self.driver.quit()
        except WebDriverException:
            pass
        self.driver = None

    """主要脚本"""
    def _run_login_flow(self, username: str, password: str) -> None:
        try:
            self._validate_locator_config()
            """重新开一个driver"""
            self.close_driver()
            driver = self._create_driver()
            wait = WebDriverWait(driver, self.timeout_seconds)

            self.authentication_status.emit("Opening TigerNet login page.")
            driver.get(self.locators.login_url)

            """<1>输入Username"""
            username_input = self._wait_visible(
                wait,
                self.locators.username_by,
                self.locators.username_value,
                "username input",
            )
            username_input.clear()
            username_input.send_keys(username)

            """<2>点击确定button"""
            username_next = self._wait_clickable(
                wait,
                self.locators.username_next_by,
                self.locators.username_next_value,
                "username next button",
            )
            username_next.click()

            """<3>输入Password"""
            password_input = self._wait_visible(
                wait,
                self.locators.password_by,
                self.locators.password_value,
                "password input",
            )
            password_input.clear()
            password_input.send_keys(password)

            """<4>点击确定button"""
            password_next = self._wait_clickable(
                wait,
                self.locators.password_next_by,
                self.locators.password_next_value,
                "password next button",
            )
            password_next.click()

            self._wait_visible(
                wait,
                self.locators.success_by,
                self.locators.success_value,
                "successful login marker",
            )
        except TimeoutException as error:
            self.authentication_failed.emit(f"TigerNet login timed out: {error.msg}")
            return
        except AuthenticationConfigurationError as error:
            self.authentication_failed.emit(str(error))
            return
        except WebDriverException as error:
            self.authentication_failed.emit(f"Selenium browser error: {error.msg}")
            return
        except OSError as error:
            self.authentication_failed.emit(f"Selenium browser could not start: {error}")
            return

        self.authentication_status.emit("TigerNet login succeeded.")
        self.authentication_succeeded.emit(driver)

    def _create_driver(self) -> WebDriver:
        if self.driver is not None:
            return self.driver

        options = webdriver.ChromeOptions()
        options.add_argument("--window-size=1280,900")
        if self.headless:
            options.add_argument("--headless=new")

        self.driver = webdriver.Chrome(options=options)
        return self.driver

    def _wait_visible(
        self,
        wait: WebDriverWait,
        by: str,
        value: str,
        label: str,
    ) -> Any:
        self._check_locator(value, label)
        return wait.until(EC.visibility_of_element_located((by, value)))

    def _wait_clickable(
        self,
        wait: WebDriverWait,
        by: str,
        value: str,
        label: str,
    ) -> Any:
        self._check_locator(value, label)
        return wait.until(EC.element_to_be_clickable((by, value)))

    def _check_locator(self, value: str, label: str) -> None:
        if value.startswith("TODO_"):
            raise AuthenticationConfigurationError(f"Authentication locator is not configured: {label}")

    def _validate_locator_config(self) -> None:
        locator_values = [
            (self.locators.username_value, "username input"),
            (self.locators.username_next_value, "username next button"),
            (self.locators.password_value, "password input"),
            (self.locators.password_next_value, "password next button"),
            (self.locators.success_value, "successful login marker"),
        ]
        for value, label in locator_values:
            self._check_locator(value, label)
