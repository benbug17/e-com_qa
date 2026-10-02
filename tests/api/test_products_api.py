import pytest
from jsonschema import validate
from utils import schemas

pytestmark = pytest.mark.api


@pytest.mark.smoke
def test_health(api):
    assert api.get("/api/health").json() == {"status": "ok"}


@pytest.mark.smoke
def test_list_products_matches_schema(api):
    r = api.get("/api/products")
    assert r.status_code == 200
    validate(r.json(), schemas.PRODUCT_LIST)


@pytest.mark.regression
def test_get_product_by_id(api):
    r = api.get("/api/products/1")
    assert r.status_code == 200
    validate(r.json(), schemas.PRODUCT)
    assert r.json()["name"] == "Laptop"


@pytest.mark.regression
def test_api_products_match_database(api, db):
    api_ids = {p["id"]: p for p in api.get("/api/products").json()}
    for row in db.fetch_all("SELECT * FROM products"):
        assert api_ids[row["id"]]["price"] == float(row["price"])
        assert api_ids[row["id"]]["stock"] == row["stock"]


@pytest.mark.negative
@pytest.mark.parametrize("pid", [9999, 0, -1, "abc"])
def test_unknown_product_is_404(api, pid):
    assert api.get(f"/api/products/{pid}").status_code == 404
