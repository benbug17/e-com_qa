import pytest
from pages.cart_page import CartPage

pytestmark = pytest.mark.ui


@pytest.mark.smoke
def test_add_product_updates_cart_badge(logged_in):
    logged_in.add_to_cart(1)
    assert logged_in.cart_count() == 1


@pytest.mark.regression
def test_cart_total_is_sum_of_lines(driver, logged_in):
    logged_in.add_to_cart(1).add_to_cart(2).add_to_cart(2)   # 999.99 + 2*59.50
    logged_in.go_to_cart()
    cart = CartPage(driver)
    assert cart.row_count() == 2
    assert cart.total() == pytest.approx(1118.99)


@pytest.mark.regression
def test_remove_item_from_cart(driver, logged_in):
    logged_in.add_to_cart(3)
    logged_in.go_to_cart()
    cart = CartPage(driver)
    cart.remove(3)
    assert cart.is_empty()


@pytest.mark.smoke
def test_checkout_shows_confirmation(driver, logged_in):
    logged_in.add_to_cart(3)
    logged_in.go_to_cart()
    assert CartPage(driver).checkout().confirmation_order_id() > 0


@pytest.mark.negative
def test_checkout_with_empty_cart_shows_error(driver, logged_in):
    logged_in.go_to_cart()
    cart = CartPage(driver).checkout()
    assert "empty" in cart.error_message().lower()


@pytest.mark.negative
def test_checkout_fails_when_stock_insufficient(driver, logged_in, db):
    logged_in.add_to_cart(4).add_to_cart(4).add_to_cart(4)    # 3 mugs, only 2 in stock
    logged_in.go_to_cart()
    cart = CartPage(driver).checkout()
    assert "insufficient stock" in cart.error_message().lower()
    assert db.fetch_one("SELECT COUNT(*) AS n FROM orders")["n"] == 0
