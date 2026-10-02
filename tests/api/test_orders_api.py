import pytest
from jsonschema import validate
from utils import schemas

pytestmark = pytest.mark.api


@pytest.mark.smoke
def test_create_order_returns_201_and_schema(auth_api):
    r = auth_api.post("/api/orders", json={"items": [{"product_id": 1, "quantity": 1}]})
    assert r.status_code == 201
    validate(r.json(), schemas.ORDER_CREATED)


@pytest.mark.regression
def test_order_total_is_calculated_server_side(auth_api):
    r = auth_api.post("/api/orders", json={"items": [{"product_id": 1, "quantity": 2},
                                                     {"product_id": 3, "quantity": 4}]})
    assert r.json()["total"] == pytest.approx(2 * 999.99 + 4 * 25.00)


@pytest.mark.regression
def test_get_order_roundtrip(auth_api):
    oid = auth_api.post("/api/orders", json={"items": [{"product_id": 2, "quantity": 3}]}).json()["order_id"]
    r = auth_api.get(f"/api/orders/{oid}")
    assert r.status_code == 200
    validate(r.json(), schemas.ORDER)
    assert r.json()["items"][0]["quantity"] == 3


@pytest.mark.negative
@pytest.mark.parametrize("payload,status", [
    ({}, 400),
    ({"items": []}, 400),
    ({"items": [{"product_id": 1, "quantity": 0}]}, 400),
    ({"items": [{"product_id": 1, "quantity": -5}]}, 400),
    ({"items": [{"product_id": "1", "quantity": 1}]}, 400),
    ({"items": [{"product_id": 9999, "quantity": 1}]}, 404),
    ({"items": [{"product_id": 4, "quantity": 3}]}, 409),
], ids=["no-items", "empty", "qty-zero", "qty-negative", "pid-string", "unknown-product", "out-of-stock"])
def test_invalid_orders_rejected(auth_api, payload, status):
    assert auth_api.post("/api/orders", json=payload).status_code == status


@pytest.mark.negative
def test_cannot_read_another_users_order(auth_api, api):
    oid = auth_api.post("/api/orders", json={"items": [{"product_id": 1, "quantity": 1}]}).json()["order_id"]
    other = type(api)()
    other.login("jane", "Secret123!")
    assert other.get(f"/api/orders/{oid}").status_code == 404
