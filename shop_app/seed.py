"""Create schema + seed data. Used by the app (init) and by tests (reset between tests)."""
import os
from werkzeug.security import generate_password_hash

SCHEMA = os.path.join(os.path.dirname(__file__), "schema.sql")
USERS = [("qa_user", "qa_user@example.com", "Passw0rd!"),
         ("jane", "jane@example.com", "Secret123!")]
PRODUCTS = [("Laptop", 999.99, 100), ("Headphones", 59.50, 100),
            ("Keyboard", 25.00, 100), ("Limited Edition Mug", 12.00, 2)]


def reset(conn):
    with conn.cursor() as cur:
        cur.execute(open(SCHEMA).read())
        for u, e, p in USERS:
            cur.execute("INSERT INTO users(username,email,password_hash) VALUES(%s,%s,%s)",
                        (u, e, generate_password_hash(p)))
        for n, pr, st in PRODUCTS:
            cur.execute("INSERT INTO products(name,price,stock) VALUES(%s,%s,%s)", (n, pr, st))
    conn.commit()


if __name__ == "__main__":
    import psycopg2
    reset(psycopg2.connect(os.getenv("DATABASE_URL", "postgresql://qa:qa@localhost:5432/shop")))
    print("Database initialised")
