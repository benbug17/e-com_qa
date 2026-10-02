import csv, pathlib
import pytest
from jsonschema import validate
from config import settings
from utils import schemas

pytestmark = pytest.mark.api
CASES = list(csv.DictReader(open(pathlib.Path(__file__).parents[1] / "data/login_negative.csv")))


@pytest.mark.smoke
def test_login_success_returns_valid_token(api):
    r = api.login(**settings.VALID_USER)
    assert r.status_code == 200
    validate(r.json(), schemas.LOGIN)


@pytest.mark.negative
@pytest.mark.parametrize("case", CASES, ids=[c["case_id"] for c in CASES])
def test_login_negative_data_driven(api, case):
    r = api.login(case["username"], case["password"])
    assert r.status_code == int(case["expected_status"])
    assert "token" not in r.json()


@pytest.mark.negative
def test_protected_endpoint_without_token_is_401(api):
    assert api.post("/api/orders", json={"items": []}).status_code == 401


@pytest.mark.negative
def test_tampered_token_is_rejected(auth_api):
    auth_api.token = auth_api.token[:-3] + "abc"
    assert auth_api.get("/api/orders/1").status_code == 401


@pytest.mark.negative
def test_login_with_non_json_body(api):
    r = api.session.post(f"{api.base}/api/auth/login", data="not json")
    assert r.status_code == 400
