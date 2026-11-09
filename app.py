import os
import sqlite3
from datetime import datetime

import click
from flask import Flask
from werkzeug.security import generate_password_hash

from routes.admin import admin_bp, add_product, create_customer, dashboard, delete_product, edit_product, products, update_order_status
from routes.auth import auth_bp, login, logout, register
from routes.front import about_page, add_review, category, checkout, create_order, front_bp, notifications_page, product_detail, profile, storefront, toggle_favorite, update_profile
from store import current_user_context, currency, get_db, init_db

production = os.environ.get("APP_ENV", "development").strip().lower() == "production"
secret_key = os.environ.get("SECRET_KEY")
if production and not secret_key:
    raise RuntimeError("SECRET_KEY must be configured when APP_ENV=production.")

app = Flask(__name__)
application = app
app.config.update(
    SECRET_KEY=secret_key or "morrow-development-key",
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=production,
)

app.register_blueprint(front_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)

# Keep existing templates and links compatible with the pre-blueprint endpoint names.
compatibility_rules = [
    ("storefront", "/", storefront, ["GET"]),
    ("about", "/about", about_page, ["GET"]),
    ("category", "/category/<category_name>", category, ["GET"]),
    ("product_detail", "/product/<int:product_id>", product_detail, ["GET"]),
    ("checkout", "/checkout", checkout, ["GET"]),
    ("profile", "/profile", profile, ["GET"]),
    ("notifications_page", "/notifications", notifications_page, ["GET"]),
    ("update_profile", "/profile/update", update_profile, ["POST"]),
    ("toggle_favorite", "/product/<int:product_id>/favorite", toggle_favorite, ["POST"]),
    ("add_review", "/product/<int:product_id>/review", add_review, ["POST"]),
    ("create_order", "/api/orders", create_order, ["POST"]),
    ("register", "/register", register, ["GET", "POST"]),
    ("login", "/login", login, ["GET", "POST"]),
    ("logout", "/logout", logout, ["GET"]),
    ("admin", "/admin", dashboard, ["GET"]),
    ("manage_products", "/admin/products", products, ["GET"]),
    ("add_product", "/admin/products", add_product, ["POST"]),
    ("edit_product", "/admin/products/<int:product_id>/edit", edit_product, ["POST"]),
    ("delete_product", "/admin/products/<int:product_id>/delete", delete_product, ["POST"]),
    ("update_order_status", "/admin/orders/<int:order_id>/status", update_order_status, ["POST"]),
    ("create_customer", "/admin/customers", create_customer, ["POST"]),
]
for endpoint, path, view, methods in compatibility_rules:
    app.add_url_rule(path, endpoint=endpoint, view_func=view, methods=methods)

app.template_filter("currency")(currency)
app.context_processor(current_user_context)

init_db()


@app.cli.command("create-admin")
@click.option("--name", prompt=True)
@click.option("--email", prompt=True)
@click.password_option()
def create_admin(name, email, password):
    """Create an administrator account using interactive prompts."""
    name = name.strip()
    email = email.strip().lower()
    if not name or not email:
        raise click.ClickException("Name and email are required.")
    if len(password) < 12:
        raise click.ClickException("Use an administrator password with at least 12 characters.")

    connection = get_db()
    try:
        connection.execute(
            "INSERT INTO users (name, email, password, role, created_at) VALUES (?, ?, ?, ?, ?)",
            (name, email, generate_password_hash(password), "admin", datetime.now().isoformat(timespec="seconds")),
        )
        connection.commit()
    except sqlite3.IntegrityError as error:
        connection.rollback()
        raise click.ClickException("An account with that email already exists.") from error
    finally:
        connection.close()
    click.echo(f"Administrator account created for {email}.")

if __name__ == "__main__":
    app.run(
        host=os.environ.get("HOST", "127.0.0.1"),
        port=int(os.environ.get("PORT", "8555")),
        debug=(
            not production
            and os.environ.get("FLASK_DEBUG", "").strip().lower() in {"1", "true", "yes"}
        ),
    )
