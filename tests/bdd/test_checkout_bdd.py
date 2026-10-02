import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from pages.login_page import LoginPage
from pages.products_page import ProductsPage
from pages.cart_page import CartPage

scenarios("features/checkout.feature")
pytestmark = [pytest.mark.bdd, pytest.mark.ui]


@given("I am on the login page")
def on_login(driver):
    LoginPage(driver).load()


@given(parsers.parse('I am logged in as "{user}"'))
def logged(driver, user):
    pwd = {"qa_user": "Passw0rd!", "jane": "Secret123!"}[user]
    LoginPage(driver).load().login(user, pwd)


@when(parsers.parse('I login as "{user}" with password "{pwd}"'))
def login_with(driver, user, pwd):
    LoginPage(driver).login(user, pwd)


@when(parsers.parse("I add product {pid:d} to my cart"))
def add(driver, pid):
    ProductsPage(driver).add_to_cart(pid)


@when("I checkout")
def checkout(driver):
    CartPage(driver).load().checkout()


@then("I see an order confirmation")
def confirmation(driver, request):
    request.node.order_id = CartPage(driver).confirmation_order_id()
    assert request.node.order_id > 0


@then(parsers.parse("the order exists in the database with total {total:f}"))
def order_in_db(db, request, total):
    row = db.fetch_one("SELECT total FROM orders WHERE id=%s", (request.node.order_id,))
    assert float(row["total"]) == pytest.approx(total)


@then(parsers.parse('I see the error "{msg}"'))
def see_error(driver, msg):
    assert msg.lower() in CartPage(driver).error_message().lower()
