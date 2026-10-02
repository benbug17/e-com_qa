from selenium.webdriver.common.by import By
from .base_page import BasePage


class ProductsPage(BasePage):
    TITLE = (By.ID, "page-title")
    CARDS = (By.CSS_SELECTOR, ".product-card")
    CART_COUNT = (By.ID, "cart-count")
    CART_LINK = (By.ID, "cart-link")
    LOGOUT = (By.ID, "logout-link")

    def load(self):
        return self.open("/products")

    def title(self):
        return self.text(self.TITLE)

    def product_count(self):
        self.find(self.CARDS)
        return len(self.driver.find_elements(*self.CARDS))

    def add_to_cart(self, product_id):
        self.click((By.ID, f"add-{product_id}"))
        return self

    def cart_count(self):
        return int(self.text(self.CART_COUNT))

    def go_to_cart(self):
        self.click(self.CART_LINK)

    def logout(self):
        self.click(self.LOGOUT)
