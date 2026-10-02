import os
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions

from config import settings
from utils.api_client import ApiClient
from utils.db import Database


@pytest.fixture(scope="session")
def db_session():
    d = Database()
    yield d
    d.close()


@pytest.fixture(autouse=True)
def clean_state(db_session):
    """Every test starts from identical, known data."""
    db_session.reset()
    yield


@pytest.fixture
def db(db_session):
    return db_session


@pytest.fixture
def api():
    return ApiClient()


@pytest.fixture
def auth_api(api):
    r = api.login(**settings.VALID_USER)
    assert r.status_code == 200, f"login failed: {r.text}"
    return api


@pytest.fixture
def driver(request):
    if settings.BROWSER == "firefox":
        opts = FirefoxOptions()
        if settings.HEADLESS:
            opts.add_argument("-headless")
        drv = webdriver.Firefox(options=opts)
    else:
        opts = ChromeOptions()
        if settings.HEADLESS:
            opts.add_argument("--headless=new")
        for a in ("--no-sandbox", "--disable-dev-shm-usage", "--window-size=1366,900"):
            opts.add_argument(a)
        drv = webdriver.Chrome(options=opts)
    request.node.driver = drv
    yield drv
    drv.quit()


@pytest.fixture
def logged_in(driver):
    from pages.login_page import LoginPage
    from pages.products_page import ProductsPage
    LoginPage(driver).load().login(**settings.VALID_USER)
    return ProductsPage(driver)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Screenshot on UI test failure."""
    outcome = yield
    rep = outcome.get_result()
    drv = getattr(item, "driver", None)
    if rep.when == "call" and rep.failed and drv:
        os.makedirs("reports/screenshots", exist_ok=True)
        drv.save_screenshot(f"reports/screenshots/{item.name}.png")
