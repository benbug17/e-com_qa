import pytest
from config import settings
from pages.login_page import LoginPage
from pages.products_page import ProductsPage

pytestmark = pytest.mark.ui


@pytest.mark.smoke
def test_valid_login_shows_products(driver):
    LoginPage(driver).load().login(**settings.VALID_USER)
    page = ProductsPage(driver)
    assert page.title() == "Products"
    assert page.product_count() == 4


@pytest.mark.regression
def test_logout_returns_to_login(driver, logged_in):
    logged_in.logout()
    assert LoginPage(driver).is_present(LoginPage.SUBMIT)


@pytest.mark.regression
def test_protected_page_redirects_when_logged_out(driver):
    ProductsPage(driver).load()
    assert LoginPage(driver).is_present(LoginPage.SUBMIT)


@pytest.mark.negative
@pytest.mark.parametrize("user,pwd,msg", [
    ("qa_user", "wrong", "Invalid username or password"),
    ("nobody", "Passw0rd!", "Invalid username or password"),
    ("", "", "required"),
    ("qa_user", "", "required"),
    ("' OR '1'='1", "x", "Invalid username or password"),
])
def test_invalid_login_shows_error(driver, user, pwd, msg):
    page = LoginPage(driver).load().login(user, pwd)
    assert msg in page.error_message()
