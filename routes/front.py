import ast
import json
import math
import re
import sqlite3
from pathlib import Path, PurePosixPath
from uuid import uuid4
from flask import Blueprint, abort, jsonify, redirect, render_template, request, session, url_for
from urllib.parse import urlsplit
from store import PAGE_SIZE, UPLOAD_DIR, get_db

front_bp = Blueprint("front", __name__)


def remove_old_avatar(avatar_url, connection, user_id):
    """Delete a replaced profile photo if it is this user's upload and nothing else uses it."""
    if not avatar_url:
        return
    parsed_url = urlsplit(avatar_url)
    image_path = PurePosixPath(parsed_url.path)
    filename = image_path.name
    if (
        parsed_url.scheme
        or parsed_url.netloc
        or image_path.parent != PurePosixPath("/static/uploads")
        or not (filename.startswith(f"user-{user_id}-profile.") or filename.startswith(f"user-{user_id}-profile-"))
    ):
        return
    if connection.execute(
        "SELECT 1 FROM users WHERE avatar = ? UNION ALL "
        "SELECT 1 FROM products WHERE image1 = ? OR image2 = ? OR image3 = ? LIMIT 1",
        (avatar_url, avatar_url, avatar_url, avatar_url),
    ).fetchone():
        return
    upload_directory = UPLOAD_DIR.resolve()
    file_path = (upload_directory / filename).resolve()
    if file_path.parent == upload_directory:
        file_path.unlink(missing_ok=True)


def render_profile(error=None, status=200):
    connection = get_db()
    account = connection.execute("SELECT * FROM users WHERE id = ?", (session["user"]["id"],)).fetchone()
    orders = connection.execute("SELECT * FROM orders WHERE email = ? ORDER BY id DESC", (session["user"]["email"],)).fetchall()
    favorites = connection.execute("SELECT products.* FROM favorites JOIN products ON products.id = favorites.product_id WHERE favorites.user_id = ?", (session["user"]["id"],)).fetchall()
    connection.close()
    return render_template("profile.html", account=account, orders=orders, favorites=favorites, error=error), status

@front_bp.route("/")
def storefront():
    connection = get_db()
    query = request.args.get("q", "").strip()
    page = max(request.args.get("page", 1, type=int), 1)
    offset = (page - 1) * PAGE_SIZE
    if query:
        values = tuple(f"%{query}%" for _ in range(3))
        total = connection.execute("SELECT COUNT(*) FROM products WHERE name LIKE ? OR description LIKE ? OR category LIKE ?", values).fetchone()[0]
        products = connection.execute("SELECT * FROM products WHERE name LIKE ? OR description LIKE ? OR category LIKE ? ORDER BY id DESC LIMIT ? OFFSET ?", values + (PAGE_SIZE, offset)).fetchall()
    else:
        total = connection.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        products = connection.execute("SELECT * FROM products ORDER BY id DESC LIMIT ? OFFSET ?", (PAGE_SIZE, offset)).fetchall()
    categories = connection.execute("SELECT name AS category, icon FROM categories ORDER BY name").fetchall()
    connection.close()
    return render_template("index.html", products=products, categories=categories, page=page, total_pages=(total + PAGE_SIZE - 1) // PAGE_SIZE, query=query)

@front_bp.route("/about")
def about_page():
    return render_template("about.html")

@front_bp.route("/category/<category_name>")
@front_bp.route("/category")
def category(category_name=None):
    price_filters = {}
    for key in ("min_price", "max_price"):
        value = request.args.get(key, "").strip()
        if value:
            try:
                price = float(value)
            except ValueError:
                abort(400, description=f"{key.replace('_', ' ').capitalize()} must be a number.")
            if not math.isfinite(price) or price < 0:
                abort(400, description=f"{key.replace('_', ' ').capitalize()} must be a non-negative number.")
            price_filters[key] = price

    sort = request.args.get("sort", "latest")
    sort_orders = {
        "latest": "id DESC",
        "price_asc": "price ASC, id DESC",
        "price_desc": "price DESC, id DESC",
        "name_asc": "name COLLATE NOCASE ASC, id DESC",
    }
    if sort not in sort_orders:
        sort = "latest"

    conditions = []
    values = []
    if category_name is not None:
        conditions.append("category = ?")
        values.append(category_name)
    if "min_price" in price_filters:
        conditions.append("price >= ?")
        values.append(price_filters["min_price"])
    if "max_price" in price_filters:
        conditions.append("price <= ?")
        values.append(price_filters["max_price"])
    where_clause = " AND ".join(conditions) or "1 = 1"

    connection = get_db()
    page = max(request.args.get("page", 1, type=int), 1)
    offset = (page - 1) * PAGE_SIZE
    total = connection.execute(f"SELECT COUNT(*) FROM products WHERE {where_clause}", values).fetchone()[0]
    products = connection.execute(
        f"SELECT * FROM products WHERE {where_clause} ORDER BY {sort_orders[sort]} LIMIT ? OFFSET ?",
        tuple(values) + (PAGE_SIZE, offset),
    ).fetchall()
    categories = connection.execute("SELECT name AS category, icon FROM categories ORDER BY name").fetchall()
    connection.close()
    return render_template(
        "category.html",
        products=products,
        categories=categories,
        category_name=category_name,
        is_all=category_name is None,
        page_title=category_name or "All products",
        page=page,
        total=total,
        total_pages=max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE),
        min_price=price_filters.get("min_price"),
        max_price=price_filters.get("max_price"),
        sort=sort,
    )

@front_bp.route("/product/<int:product_id>")
def product_detail(product_id):
    connection = get_db()
    product = connection.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    reviews = connection.execute("SELECT reviews.*, users.name FROM reviews JOIN users ON users.id = reviews.user_id WHERE product_id = ? ORDER BY reviews.id DESC", (product_id,)).fetchall()
    recommendations = connection.execute("SELECT * FROM products WHERE category = ? AND id != ? ORDER BY id DESC LIMIT 4", (product["category"], product_id)).fetchall() if product else []
    is_favorite = bool(session.get("user") and connection.execute("SELECT 1 FROM favorites WHERE user_id = ? AND product_id = ?", (session["user"]["id"], product_id)).fetchone())
    connection.close()
    if not product:
        return redirect(url_for("front.storefront"))
    average = round(sum(review["rating"] for review in reviews) / len(reviews), 1) if reviews else 0
    return render_template("product.html", product=product, reviews=reviews, recommendations=recommendations, average=average, is_favorite=is_favorite)

@front_bp.route("/checkout")
def checkout():
    if not session.get("user"):
        next_url = request.full_path if request.query_string else request.path
        return redirect(url_for("auth.login", next=next_url))
    buy_now_product = None
    connection = get_db()
    account = connection.execute(
        "SELECT address, card_name, card_last4, card_expiry FROM users WHERE id = ?",
        (session["user"]["id"],),
    ).fetchone()
    saved_address = account["address"] if account and account["address"] else ""
    saved_card = dict(account) if account and account["card_last4"] else None
    if "buy_now" in request.args:
        product_id = request.args.get("buy_now", type=int)
        if not product_id:
            connection.close()
            return redirect(url_for("front.storefront"))
        product = connection.execute(
            "SELECT id, name, price, image1, color, initials FROM products WHERE id = ?",
            (product_id,),
        ).fetchone()
        if not product:
            connection.close()
            return redirect(url_for("front.storefront"))
        buy_now_product = dict(product)
    connection.close()
    return render_template(
        "checkout.html",
        buy_now_product=buy_now_product,
        saved_address=saved_address,
        saved_card=saved_card,
    )

@front_bp.route("/profile")
def profile():
    if not session.get("user"):
        return redirect(url_for("auth.login"))
    return render_profile()

@front_bp.route("/notifications")
def notifications_page():
    if not session.get("user"):
        return redirect(url_for("auth.login"))
    connection = get_db()
    orders = connection.execute("SELECT * FROM orders WHERE email = ? ORDER BY id DESC", (session["user"]["email"],)).fetchall()
    connection.close()
    return render_template("notifications.html", orders=orders)

@front_bp.get("/api/orders/<int:order_id>")
def order_invoice(order_id):
    user = session.get("user")
    if not user:
        return jsonify({"error": "Please log in to view this invoice."}), 401
    connection = get_db()
    order = connection.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    connection.close()
    if not order or (user.get("role") not in {"admin", "user"} and order["email"] != user["email"]):
        return jsonify({"error": "Invoice not found."}), 404
    try:
        items = ast.literal_eval(order["items"])
    except (ValueError, SyntaxError):
        try:
            items = json.loads(order["items"])
        except (TypeError, ValueError):
            items = []
    if not isinstance(items, list):
        items = []
    invoice_items = []
    for item in items:
        if not isinstance(item, dict):
            continue
        try:
            quantity = int(item.get("quantity", 1))
            price = float(item.get("price", 0))
        except (TypeError, ValueError):
            continue
        if quantity < 1:
            continue
        invoice_items.append({"name": str(item.get("name", "Item")), "quantity": quantity, "price": price})
    return jsonify({
        "id": order["id"],
        "customer_name": order["customer_name"],
        "email": order["email"],
        "address": order["address"],
        "created_at": order["created_at"],
        "status": order["status"],
        "payment_method": order["payment_method"],
        "total": order["total"],
        "items": invoice_items,
    })

@front_bp.get("/api/products/images")
def product_images():
    try:
        product_ids = list(dict.fromkeys(
            int(product_id) for product_id in request.args.get("ids", "").split(",")
        ))
    except ValueError:
        return jsonify({"error": "Invalid product IDs."}), 400
    if not product_ids or len(product_ids) > 100 or any(product_id < 1 for product_id in product_ids):
        return jsonify({"error": "Invalid product IDs."}), 400
    placeholders = ",".join("?" for _ in product_ids)
    connection = get_db()
    products = connection.execute(
        f"SELECT id, image1 FROM products WHERE id IN ({placeholders})", product_ids
    ).fetchall()
    connection.close()
    return jsonify({str(product["id"]): product["image1"] for product in products if product["image1"]})

@front_bp.post("/profile/update")
def update_profile():
    if not session.get("user"):
        return redirect(url_for("auth.login"))
    user_id = session["user"]["id"]
    connection = get_db()
    existing = connection.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if not existing:
        connection.close()
        session.pop("user", None)
        return redirect(url_for("auth.login"))
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    if not name or not email or "@" not in email:
        connection.close()
        return render_profile("Enter your name and a valid email address.", 400)
    if connection.execute("SELECT 1 FROM users WHERE email = ? AND id != ?", (email, user_id)).fetchone():
        connection.close()
        return render_profile("Another account already uses that email address.", 400)
    avatar = request.form.get("avatar", existing["avatar"] or "").strip()
    card_last4 = existing["card_last4"]
    card_number = request.form.get("card_number", "").strip()
    if card_number:
        card_digits = re.sub(r"[^0-9]", "", card_number)
        if not 13 <= len(card_digits) <= 19:
            connection.close()
            return render_profile("Enter a valid card number.", 400)
        card_last4 = card_digits[-4:]
    new_image_path = None
    profile_image = request.files.get("profile_image")
    if profile_image and profile_image.filename:
        extension = Path(profile_image.filename).suffix.lower()
        if extension not in {".png", ".jpg", ".jpeg", ".webp"}:
            connection.close()
            return render_profile("Profile photos must be PNG, JPEG, or WebP files.", 400)
        # A new name for every upload, so browsers don't keep showing the cached old photo.
        filename = f"user-{user_id}-profile-{uuid4().hex}{extension}"
        new_image_path = UPLOAD_DIR / filename
        profile_image.save(new_image_path)
        avatar = url_for("static", filename=f"uploads/{filename}")
    try:
        connection.execute("UPDATE users SET name = ?, email = ?, phone = ?, address = ?, avatar = ?, card_name = ?, card_last4 = ?, card_expiry = ? WHERE id = ?", (name, email, request.form.get("phone", existing["phone"] or "").strip(), request.form.get("address", existing["address"] or "").strip(), avatar, request.form.get("card_name", existing["card_name"] or "").strip(), card_last4, request.form.get("card_expiry", existing["card_expiry"] or "").strip(), user_id))
        connection.commit()
    except sqlite3.IntegrityError:
        connection.rollback()
        connection.close()
        if new_image_path:
            new_image_path.unlink(missing_ok=True)
        return render_profile("Another account already uses that email address.", 400)
    if existing["avatar"] != avatar:
        remove_old_avatar(existing["avatar"], connection, user_id)
    connection.close()
    session["user"] = {**session["user"], "name": name, "email": email}
    return redirect(url_for("front.profile"))

@front_bp.post("/product/<int:product_id>/favorite")
def toggle_favorite(product_id):
    if not session.get("user"):
        return redirect(url_for("auth.login"))
    connection = get_db()
    existing = connection.execute("SELECT 1 FROM favorites WHERE user_id = ? AND product_id = ?", (session["user"]["id"], product_id)).fetchone()
    connection.execute("DELETE FROM favorites WHERE user_id = ? AND product_id = ?", (session["user"]["id"], product_id)) if existing else connection.execute("INSERT INTO favorites (user_id, product_id) VALUES (?, ?)", (session["user"]["id"], product_id))
    connection.commit()
    connection.close()
    return redirect(request.referrer or url_for("front.product_detail", product_id=product_id))

@front_bp.post("/product/<int:product_id>/review")
def add_review(product_id):
    if not session.get("user"):
        return redirect(url_for("auth.login"))
    try:
        rating = int(request.form.get("rating", 5))
    except (TypeError, ValueError):
        return "Choose a rating from 1 to 5.", 400
    connection = get_db()
    if not connection.execute("SELECT 1 FROM products WHERE id = ?", (product_id,)).fetchone():
        connection.close()
        return redirect(url_for("front.storefront"))
    connection.execute("INSERT INTO reviews (user_id, product_id, rating, comment, created_at) VALUES (?, ?, ?, ?, datetime('now'))", (session["user"]["id"], product_id, max(1, min(5, rating)), request.form.get("comment", "").strip()))
    connection.commit()
    connection.close()
    return redirect(url_for("front.product_detail", product_id=product_id))

@front_bp.post("/api/orders")
@front_bp.post("/api/purchases")
def create_order():
    if not session.get("user"):
        referring_page = urlsplit(request.referrer or "")
        next_url = referring_page.path if referring_page.path.startswith("/") and not referring_page.path.startswith("//") else url_for("front.checkout")
        if referring_page.query:
            next_url += f"?{referring_page.query}"
        return jsonify({"error": "Please log in before buying.", "login_url": url_for("auth.login", next=next_url)}), 401
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "Please provide valid purchase details."}), 400
    customer, items = payload.get("customer"), payload.get("items")
    if not isinstance(customer, dict) or not isinstance(items, list) or not items or len(items) > 100:
        return jsonify({"error": "Please provide contact details and a valid bag."}), 400
    payment_method = payload.get("payment_method")
    if not isinstance(payment_method, str) or payment_method not in {"saved_card", "khqr"}:
        return jsonify({"error": "Choose a valid payment method."}), 400
    customer = {field: customer.get(field, "").strip() if isinstance(customer.get(field), str) else "" for field in ("name", "email", "address")}
    if not all(customer.values()) or "@" not in customer["email"]:
        return jsonify({"error": "Please provide a name, valid email, and delivery address."}), 400

    quantities = {}
    for item in items:
        if not isinstance(item, dict):
            return jsonify({"error": "Your bag contains an invalid item."}), 400
        product_id, quantity = item.get("id"), item.get("quantity")
        if (not isinstance(product_id, int) or isinstance(product_id, bool) or product_id < 1
                or not isinstance(quantity, int) or isinstance(quantity, bool) or not 1 <= quantity <= 99):
            return jsonify({"error": "Your bag contains an invalid item quantity."}), 400
        quantities[product_id] = quantities.get(product_id, 0) + quantity
        if quantities[product_id] > 99:
            return jsonify({"error": "Your bag contains an invalid item quantity."}), 400

    connection = get_db()
    if payment_method == "saved_card":
        saved_card = connection.execute(
            "SELECT card_last4 FROM users WHERE id = ?", (session["user"]["id"],)
        ).fetchone()
        if not saved_card or not saved_card["card_last4"]:
            connection.close()
            return jsonify({"error": "Save a card in your profile or choose KHQR."}), 400
    product_ids = list(quantities)
    placeholders = ",".join("?" for _ in product_ids)
    products = connection.execute(f"SELECT id, name, price FROM products WHERE id IN ({placeholders})", product_ids).fetchall()
    products_by_id = {product["id"]: product for product in products}
    if len(products_by_id) != len(product_ids):
        connection.close()
        return jsonify({"error": "A product in your bag is no longer available."}), 400
    purchase_items = [{"id": product_id, "name": products_by_id[product_id]["name"], "quantity": quantity, "price": products_by_id[product_id]["price"]} for product_id, quantity in quantities.items()]
    total = round(sum(item["price"] * item["quantity"] for item in purchase_items), 2)
    cursor = connection.execute("INSERT INTO orders (customer_name, email, address, items, total, payment_method, created_at) VALUES (?, ?, ?, ?, ?, ?, datetime('now'))", (customer["name"], customer["email"], customer["address"], str(purchase_items), total, payment_method))
    connection.commit()
    purchase_id = cursor.lastrowid
    connection.close()
    payment_label = "saved card" if payment_method == "saved_card" else "KHQR"
    return jsonify({
        "purchase_id": purchase_id,
        "total": total,
        "message": (
            f"Order #{purchase_id} recorded for ${total:,.2f} with {payment_label}. "
            "Demo only; no payment was charged."
        ),
    })
