import subprocess
import sys
import time
from urllib.parse import urlparse, urlunparse

import psycopg2
import requests
import os
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.options import Options as FirefoxOptions

from config import settings
from utils.api_client import ApiClient
from utils.db import Database


def _dsn_for(db_name):
    u = urlparse(settings.DATABASE_URL)
    return urlunparse(u._replace(path=f"/{db_name}"))


@pytest.fixture(scope="session")
def isolated_environment():
    """Under pytest-xdist, give each worker its own database AND its own app server,
    so parallel tests never share (or wipe) each other's data. Serial runs are unchanged."""
    worker = os.getenv("PYTEST_XDIST_WORKER")
    if worker is None:
        yield
        return
    n = int(worker.replace("gw", ""))
    db_name, port = f"shop_{worker}", 5100 + n
    original = (settings.DATABASE_URL, settings.BASE_URL)

    admin = psycopg2.connect(_dsn_for("postgres"))
    admin.autocommit = True
    with admin.cursor() as cur:
        cur.execute(f"DROP DATABASE IF EXISTS {db_name} WITH (FORCE)")
        cur.execute(f"CREATE DATABASE {db_name}")

    settings.DATABASE_URL = _dsn_for(db_name)
    settings.BASE_URL = f"http://127.0.0.1:{port}"
    proc = subprocess.Popen([sys.executable, "-m", "shop_app.app"],
                            env={**os.environ, "DATABASE_URL": settings.DATABASE_URL, "PORT": str(port)},
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(40):
        try:
            if requests.get(f"{settings.BASE_URL}/api/health", timeout=1).ok:
                break
        except requests.RequestException:
            time.sleep(0.5)
    else:
        proc.terminate()
        raise RuntimeError(f"worker app on port {port} did not start")
    yield
    proc.terminate()
    with admin.cursor() as cur:
        cur.execute(f"DROP DATABASE IF EXISTS {db_name} WITH (FORCE)")
    admin.close()
    settings.DATABASE_URL, settings.BASE_URL = original


@pytest.fixture(scope="session")
def db_session(isolated_environment):
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
        if os.getenv("CHROME_BIN"):
            opts.binary_location = os.environ["CHROME_BIN"]
        service = ChromeService(os.environ["CHROMEDRIVER"]) if os.getenv("CHROMEDRIVER") else ChromeService()
        drv = webdriver.Chrome(service=service, options=opts)
    request.node.driver = drv
    yield drv
    drv.quit()


@pytest.fixture
def logged_in(driver):
    from pages.login_page import LoginPage
    from pages.products_page import ProductsPage
    LoginPage(driver).load().login(**settings.VALID_USER)
    page = ProductsPage(driver)
    page.title()                      # wait until login has completed
    return page


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Screenshot on UI test failure (setup or call phase)."""
    outcome = yield
    rep = outcome.get_result()
    drv = getattr(item, "driver", None)
    if rep.when in ("setup", "call") and rep.failed and drv:
        os.makedirs("reports/screenshots", exist_ok=True)
        drv.save_screenshot(f"reports/screenshots/{item.name}.png")
        print(f"\nFAILED AT URL: {drv.current_url}")
