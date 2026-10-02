from selenium.webdriver.common.by import By
from .base_page import BasePage


class CartPage(BasePage):
    ROWS = (By.CSS_SELECTOR, ".cart-row")
    TOTAL = (By.ID, "cart-total")
    CHECKOUT = (By.ID, "checkout-button")
    EMPTY = (By.ID, "empty-cart")
    ERROR = (By.CSS_SELECTOR, "[data-test='error']")
    CONFIRMATION = (By.ID, "order-confirmation")
    ORDER_ID = (By.ID, "order-id")

    def load(self):
        return self.open("/cart")

    def row_count(self):
        return len(self.driver.find_elements(*self.ROWS))

    def total(self):
        return float(self.text(self.TOTAL))

    def remove(self, product_id):
        self.click((By.ID, f"remove-{product_id}"))

    def checkout(self):
        self.click(self.CHECKOUT)
        return self

    def is_empty(self):
        return self.is_present(self.EMPTY)

    def error_message(self):
        return self.text(self.ERROR)

    def confirmation_order_id(self):
        self.find(self.CONFIRMATION)
        return int(self.text(self.ORDER_ID))
