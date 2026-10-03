from selenium.common.exceptions import (NoSuchElementException,
                                        StaleElementReferenceException,
                                        TimeoutException,
                                        WebDriverException)
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from config import settings


class BasePage:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, settings.TIMEOUT,
                                  ignored_exceptions=[StaleElementReferenceException])

    def open(self, path=""):
        self.driver.get(f"{settings.BASE_URL}{path}")
        return self

    def find(self, locator):
        return self.wait.until(EC.visibility_of_element_located(locator))

    def click(self, locator):
        self.wait.until(EC.element_to_be_clickable(locator)).click()

    def type(self, locator, text):
        el = self.find(locator)
        el.clear()
        el.send_keys(text)

    def text(self, locator):
        return self.find(locator).text

    def is_present(self, locator, timeout=3):
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: len(d.find_elements(*locator)) > 0)
            return True
        except TimeoutException:
            return False
