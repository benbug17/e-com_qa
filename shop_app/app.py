import os
from functools import wraps
import psycopg2, psycopg2.extras
from flask import (Flask, request, session, redirect, url_for, jsonify, g,
                   render_template_string)
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from werkzeug.security import check_password_hash

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret")
tokens = URLSafeTimedSerializer(app.secret_key)
DSN = os.getenv("DATABASE_URL", "postgresql://qa:qa@localhost:5432/shop")


# ---------- DB helpers ----------
def conn():
    if "db" not in g:
        g.db = psycopg2.connect(DSN, cursor_factory=psycopg2.extras.RealDictCursor)
    return g.db


@app.teardown_appcontext
def _close(_):
    c = g.pop("db", None)
    if c:
        c.close()


def query(sql, args=(), one=False, commit=False):
    with conn().cursor() as cur:
        cur.execute(sql, args)
        rows = cur.fetchall() if cur.description else []
    if commit:
        conn().commit()
    return (rows[0] if rows else None) if one else rows


def product_dict(p):
    return {"id": p["id"], "name": p["name"], "price": float(p["price"]), "stock": p["stock"]}


class OrderError(Exception):
    def __init__(self, msg, status):
        super().__init__(msg)
        self.status = status


def place_order(user_id, items):
    """Atomic: validate, lock rows, decrement stock, insert order + lines."""
    if not isinstance(items, list) or not items:
        raise OrderError("items must be a non-empty list", 400)
    c = conn()
    try:
        with c.cursor() as cur:
            total, lines = 0, []
            for it in items:
                pid, qty = it.get("product_id"), it.get("quantity")
                if not isinstance(pid, int) or not isinstance(qty, int) or qty <= 0:
                    raise OrderError("invalid product_id or quantity", 400)
                cur.execute("SELECT id, price, stock FROM products WHERE id=%s FOR UPDATE", (pid,))
                p = cur.fetchone()
                if not p:
                    raise OrderError(f"product {pid} not found", 404)
                if p["stock"] < qty:
                    raise OrderError(f"insufficient stock for product {pid}", 409)
                cur.execute("UPDATE products SET stock=stock-%s WHERE id=%s", (qty, pid))
                total += p["price"] * qty
                lines.append((pid, qty, p["price"]))
            cur.execute("INSERT INTO orders(user_id,total) VALUES(%s,%s) RETURNING id", (user_id, total))
            oid = cur.fetchone()["id"]
            for pid, qty, price in lines:
                cur.execute("INSERT INTO order_items(order_id,product_id,quantity,unit_price) "
                            "VALUES(%s,%s,%s,%s)", (oid, pid, qty, price))
        c.commit()
        return oid, float(total)
    except Exception:
        c.rollback()
        raise


# ---------- API ----------
def api_auth(f):
    @wraps(f)
    def w(*a, **kw):
        h = request.headers.get("Authorization", "")
        if not h.startswith("Bearer "):
            return jsonify(error="missing token"), 401
        try:
            g.user_id = tokens.loads(h[7:], max_age=3600)["uid"]
        except (BadSignature, SignatureExpired):
            return jsonify(error="invalid or expired token"), 401
        return f(*a, **kw)
    return w


@app.get("/api/health")
def health():
    return jsonify(status="ok")


@app.post("/api/auth/login")
def api_login():
    d = request.get_json(silent=True) or {}
    if not d.get("username") or not d.get("password"):
        return jsonify(error="username and password required"), 400
    u = query("SELECT * FROM users WHERE username=%s", (d["username"],), one=True)
    if not u or not check_password_hash(u["password_hash"], d["password"]):
        return jsonify(error="invalid credentials"), 401
    return jsonify(token=tokens.dumps({"uid": u["id"]}), user_id=u["id"], username=u["username"])


@app.get("/api/products")
def api_products():
    return jsonify([product_dict(p) for p in query("SELECT * FROM products ORDER BY id")])


@app.get("/api/products/<int:pid>")
def api_product(pid):
    p = query("SELECT * FROM products WHERE id=%s", (pid,), one=True)
    return (jsonify(product_dict(p)), 200) if p else (jsonify(error="not found"), 404)


@app.post("/api/orders")
@api_auth
def api_create_order():
    d = request.get_json(silent=True) or {}
    try:
        oid, total = place_order(g.user_id, d.get("items"))
    except OrderError as e:
        return jsonify(error=str(e)), e.status
    return jsonify(order_id=oid, total=total, status="PLACED"), 201


@app.get("/api/orders/<int:oid>")
@api_auth
def api_get_order(oid):
    o = query("SELECT * FROM orders WHERE id=%s AND user_id=%s", (oid, g.user_id), one=True)
    if not o:
        return jsonify(error="not found"), 404
    items = query("SELECT product_id, quantity, unit_price FROM order_items WHERE order_id=%s ORDER BY id", (oid,))
    return jsonify(order_id=o["id"], total=float(o["total"]), status=o["status"],
                   items=[{"product_id": i["product_id"], "quantity": i["quantity"],
                           "unit_price": float(i["unit_price"])} for i in items])


# ---------- UI ----------
LOGIN = """<!doctype html><html><head><title>QA Shop - Login</title></head><body><h1>Login</h1>
{% if error %}<div class="error" data-test="error">{{ error }}</div>{% endif %}
<form method="post" action="/"><input id="username" name="username" placeholder="Username">
<input id="password" name="password" type="password" placeholder="Password">
<button id="login-button" type="submit">Login</button></form></body></html>"""
HEAD = """<!doctype html><html><head><title>QA Shop</title></head><body>
<nav><a id="cart-link" href="/cart">Cart (<span id="cart-count">{{ cart_count }}</span>)</a>
<a id="logout-link" href="/logout">Logout</a></nav>
{% if error %}<div class="error" data-test="error">{{ error }}</div>{% endif %}"""
PRODUCTS = HEAD + """<h1 id="page-title">Products</h1>
{% for p in products %}<div class="product-card" data-test="product-{{p.id}}">
<span class="product-name">{{ p.name }}</span> <span class="product-price">{{ '%.2f' % p.price }}</span>
<span class="product-stock">{{ p.stock }}</span>
<form method="post" action="/cart/add/{{p.id}}"><button id="add-{{p.id}}" type="submit">Add to cart</button></form>
</div>{% endfor %}</body></html>"""
CART = HEAD + """<h1 id="page-title">Your Cart</h1>
{% if not rows %}<p id="empty-cart">Your cart is empty</p>{% endif %}
{% for r in rows %}<div class="cart-row" data-test="cart-{{r.product_id}}">
<span class="cart-name">{{ r.name }}</span> x<span class="cart-qty">{{ r.quantity }}</span>
<span class="cart-line-total">{{ '%.2f' % (r.price * r.quantity) }}</span>
<form method="post" action="/cart/remove/{{r.product_id}}"><button id="remove-{{r.product_id}}">Remove</button></form>
</div>{% endfor %}
<p>Total: <span id="cart-total">{{ '%.2f' % total }}</span></p>
<form method="post" action="/checkout"><button id="checkout-button">Checkout</button></form>
<a id="continue-link" href="/products">Continue shopping</a></body></html>"""
CONFIRM = HEAD + """<h1 id="page-title">Thank you</h1>
<p id="order-confirmation">Order #<span id="order-id">{{ order_id }}</span> placed</p></body></html>"""


def ui_auth(f):
    @wraps(f)
    def w(*a, **kw):
        return f(*a, **kw) if session.get("uid") else redirect("/")
    return w


def cart_ctx():
    n = query("SELECT COALESCE(SUM(quantity),0) AS n FROM cart_items WHERE user_id=%s",
              (session["uid"],), one=True)["n"]
    return {"cart_count": n}


@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template_string(LOGIN)
    u, p = request.form.get("username", "").strip(), request.form.get("password", "")
    if not u or not p:
        return render_template_string(LOGIN, error="Username and password are required"), 400
    row = query("SELECT * FROM users WHERE username=%s", (u,), one=True)
    if not row or not check_password_hash(row["password_hash"], p):
        return render_template_string(LOGIN, error="Invalid username or password"), 401
    session["uid"] = row["id"]
    return redirect("/products")


@app.get("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.get("/products")
@ui_auth
def products():
    ps = [product_dict(p) for p in query("SELECT * FROM products ORDER BY id")]
    return render_template_string(PRODUCTS, products=ps, **cart_ctx())


@app.post("/cart/add/<int:pid>")
@ui_auth
def cart_add(pid):
    query("INSERT INTO cart_items(user_id,product_id,quantity) VALUES(%s,%s,1) "
          "ON CONFLICT (user_id,product_id) DO UPDATE SET quantity=cart_items.quantity+1",
          (session["uid"], pid), commit=True)
    return redirect("/products")


@app.post("/cart/remove/<int:pid>")
@ui_auth
def cart_remove(pid):
    query("DELETE FROM cart_items WHERE user_id=%s AND product_id=%s", (session["uid"], pid), commit=True)
    return redirect("/cart")


def cart_rows():
    return query("SELECT c.product_id, c.quantity, p.name, p.price FROM cart_items c "
                 "JOIN products p ON p.id=c.product_id WHERE c.user_id=%s ORDER BY c.product_id",
                 (session["uid"],))


@app.get("/cart")
@ui_auth
def cart():
    rows = cart_rows()
    total = sum(r["price"] * r["quantity"] for r in rows)
    return render_template_string(CART, rows=rows, total=float(total), **cart_ctx(),
                                  error=request.args.get("error"))


@app.post("/checkout")
@ui_auth
def checkout():
    rows = cart_rows()
    if not rows:
        return redirect("/cart?error=Cart is empty")
    try:
        oid, _ = place_order(session["uid"], [{"product_id": r["product_id"], "quantity": r["quantity"]} for r in rows])
    except OrderError as e:
        return redirect(f"/cart?error={e}")
    query("DELETE FROM cart_items WHERE user_id=%s", (session["uid"],), commit=True)
    return render_template_string(CONFIRM, order_id=oid, **cart_ctx())


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
