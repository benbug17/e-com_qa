import pytest
import psycopg2

pytestmark = pytest.mark.db


@pytest.mark.smoke
def test_seed_data_present(db):
    assert db.fetch_one("SELECT COUNT(*) AS n FROM products")["n"] == 4
    assert db.fetch_one("SELECT COUNT(*) AS n FROM users")["n"] == 2


@pytest.mark.regression
def test_passwords_are_hashed_not_plaintext(db):
    for u in db.fetch_all("SELECT password_hash FROM users"):
        assert u["password_hash"] not in ("Passw0rd!", "Secret123!")
        assert "$" in u["password_hash"] or ":" in u["password_hash"]


@pytest.mark.regression
def test_no_orphan_order_items(db):
    orphans = db.fetch_one("SELECT COUNT(*) AS n FROM order_items oi LEFT JOIN orders o "
                           "ON o.id = oi.order_id WHERE o.id IS NULL")["n"]
    assert orphans == 0


@pytest.mark.negative
@pytest.mark.parametrize("sql", [
    "INSERT INTO products(name,price,stock) VALUES('Bad',-1,1)",
    "INSERT INTO products(name,price,stock) VALUES('Bad',1,-1)",
    "INSERT INTO products(name,price,stock) VALUES(NULL,1,1)",
    "INSERT INTO users(username,email,password_hash) VALUES('qa_user','x@y.z','h')",
    "INSERT INTO orders(user_id,total) VALUES(9999,10)",
    "INSERT INTO cart_items(user_id,product_id,quantity) VALUES(1,1,0)",
], ids=["neg-price", "neg-stock", "null-name", "dup-username", "bad-fk", "zero-qty"])
def test_database_constraints_enforced(db, sql):
    with pytest.raises(psycopg2.Error):
        db.execute(sql)
    db.conn.rollback()
