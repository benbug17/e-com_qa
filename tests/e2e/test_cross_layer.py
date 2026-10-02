"""Cross-layer: an action in one layer must be reflected consistently in the others."""
import pytest
from pages.cart_page import CartPage

pytestmark = pytest.mark.e2e


@pytest.mark.regression
def test_api_order_persists_correctly_in_db(auth_api, db):
    stock_before = db.fetch_one("SELECT stock FROM products WHERE id=1")["stock"]
    r = auth_api.post("/api/orders", json={"items": [{"product_id": 1, "quantity": 2},
                                                     {"product_id": 3, "quantity": 1}]})
    oid = r.json()["order_id"]

    order = db.fetch_one("SELECT * FROM orders WHERE id=%s", (oid,))
    items = db.fetch_all("SELECT * FROM order_items WHERE order_id=%s ORDER BY product_id", (oid,))
    assert order["status"] == "PLACED" and float(order["total"]) == r.json()["total"]
    assert [(i["product_id"], i["quantity"]) for i in items] == [(1, 2), (3, 1)]
    assert db.fetch_one("SELECT stock FROM products WHERE id=1")["stock"] == stock_before - 2
    assert float(order["total"]) == pytest.approx(sum(float(i["unit_price"]) * i["quantity"] for i in items))


@pytest.mark.regression
def test_failed_order_rolls_back_everything(auth_api, db):
    """Second line is out of stock -> first line's stock decrement must be rolled back."""
    r = auth_api.post("/api/orders", json={"items": [{"product_id": 1, "quantity": 1},
                                                     {"product_id": 4, "quantity": 99}]})
    assert r.status_code == 409
    assert db.fetch_one("SELECT stock FROM products WHERE id=1")["stock"] == 100
    assert db.fetch_one("SELECT COUNT(*) AS n FROM orders")["n"] == 0
    assert db.fetch_one("SELECT COUNT(*) AS n FROM order_items")["n"] == 0


@pytest.mark.smoke
def test_ui_checkout_visible_in_db_and_api(driver, logged_in, db, api):
    logged_in.add_to_cart(2).add_to_cart(3)
    logged_in.go_to_cart()
    oid = CartPage(driver).checkout().confirmation_order_id()

    order = db.fetch_one("SELECT * FROM orders WHERE id=%s", (oid,))
    assert float(order["total"]) == pytest.approx(84.50)
    assert db.fetch_one("SELECT COUNT(*) AS n FROM cart_items")["n"] == 0

    api.login("qa_user", "Passw0rd!")
    assert api.get(f"/api/orders/{oid}").json()["total"] == pytest.approx(84.50)


@pytest.mark.regression
def test_ui_add_to_cart_persists_in_db(logged_in, db):
    logged_in.add_to_cart(1).add_to_cart(1)
    assert db.fetch_one("SELECT quantity FROM cart_items WHERE product_id=1")["quantity"] == 2
