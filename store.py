import os
import sqlite3
from datetime import datetime
from pathlib import Path

from flask import render_template, request, session, url_for
from werkzeug.security import generate_password_hash

BASE_DIR = Path(__file__).parent
DATABASE = Path(os.environ.get("DATABASE_PATH", str(BASE_DIR / "shop.db"))).expanduser()
UPLOAD_DIR = BASE_DIR / "static" / "uploads"
PAGE_SIZE = 20
DEMO_ADMIN_EMAIL = "admin@morrow.test"
DEMO_ADMIN_PASSWORD = "admin123"
DEMO_STAFF_EMAIL = "staff@morrow.test"
DEMO_STAFF_PASSWORD = "staff123"

SEED_PRODUCT_CATALOG = {
    "Audio": [
        ("Apple AirPods Pro (2nd generation)", 249.99),
        ("Apple AirPods 4 with Active Noise Cancellation", 179.99),
        ("Sony WF-1000XM5", 299.99),
        ("Sony WH-1000XM5", 399.99),
        ("Sony WH-1000XM4", 349.99),
        ("Bose QuietComfort Ultra Headphones", 429.99),
        ("Bose QuietComfort Earbuds II", 279.99),
        ("JBL Charge 5", 179.95),
        ("JBL Flip 6", 129.95),
        ("JBL Xtreme 4", 379.95),
        ("Marshall Emberton II", 169.99),
        ("Sonos Era 100", 249.00),
        ("Sonos Move 2", 499.00),
        ("Beats Studio Pro", 349.99),
        ("Beats Fit Pro", 199.99),
        ("Sennheiser Momentum 4 Wireless", 379.95),
        ("Sennheiser Momentum True Wireless 4", 299.95),
        ("Soundcore Space Q45", 149.99),
        ("Soundcore Liberty 4 NC", 99.99),
        ("Audio-Technica ATH-M50xBT2", 199.00),
    ],
    "Wearables": [
        ("Apple Watch Series 10", 399.00),
        ("Apple Watch Ultra 2", 799.00),
        ("Apple Watch SE (2nd generation)", 249.00),
        ("Samsung Galaxy Watch7", 299.99),
        ("Samsung Galaxy Watch Ultra", 649.99),
        ("Google Pixel Watch 3", 349.99),
        ("Garmin Forerunner 265", 449.99),
        ("Garmin Venu 3", 449.99),
        ("Garmin fēnix 7 Pro", 799.99),
        ("Fitbit Charge 6", 159.95),
        ("Fitbit Versa 4", 199.95),
        ("Fitbit Inspire 3", 99.95),
        ("Oura Ring 4", 349.00),
        ("Garmin Instinct 2X Solar", 449.99),
        ("WHOOP 4.0", 239.00),
        ("Amazfit Balance", 229.99),
        ("Huawei Watch GT 5", 279.00),
        ("Xiaomi Smart Band 9", 59.99),
        ("Garmin Lily 2", 249.99),
        ("COROS PACE 3", 229.00),
    ],
    "Power": [
        ("Anker Prime Power Bank 20K 200W", 179.99),
        ("Anker 737 Power Bank", 149.99),
        ("Anker Nano Power Bank 10K", 49.99),
        ("Anker MagGo Power Bank", 89.99),
        ("UGREEN Nexode Power Bank 25K", 129.99),
        ("Baseus Blade HD Laptop Power Bank", 99.99),
        ("Belkin BoostCharge Pro 10K", 69.99),
        ("Belkin BoostCharge Power Bank 20K", 49.99),
        ("mophie powerstation pro XL", 199.95),
        ("Shargeek 100 Power Bank", 179.99),
        ("Zendure SuperTank Pro", 199.00),
        ("Nitecore NB10000 Gen 3", 64.95),
        ("EcoFlow RIVER 2", 239.00),
        ("EcoFlow RIVER 2 Max", 469.00),
        ("Jackery Explorer 300 Plus", 299.00),
        ("BLUETTI EB3A", 299.00),
        ("Anker 521 Portable Power Station", 249.99),
        ("Goal Zero Sherpa 100AC", 299.95),
        ("RAVPower PD Pioneer 20K", 59.99),
        ("Cuktech 20 Power Bank", 99.99),
    ],
    "Entertainment": [
        ("Apple TV 4K (3rd generation)", 129.00),
        ("Roku Ultra", 99.99),
        ("Roku Streaming Stick 4K", 49.99),
        ("Google TV Streamer 4K", 99.99),
        ("Amazon Fire TV Stick 4K Max", 59.99),
        ("NVIDIA SHIELD TV Pro", 199.99),
        ("PlayStation 5 Slim", 499.99),
        ("Xbox Series X", 499.99),
        ("Xbox Series S", 299.99),
        ("Nintendo Switch OLED Model", 349.99),
        ("Nintendo Switch Lite", 199.99),
        ("Samsung The Frame 55-inch 4K TV", 1499.99),
        ("LG OLED evo C4 55-inch TV", 1599.99),
        ("Sony BRAVIA XR A80L 55-inch TV", 1799.99),
        ("Epson Home Cinema 2350 Projector", 1299.99),
        ("BenQ HT2060 Projector", 999.99),
        ("XGIMI HORIZON Ultra Projector", 1699.00),
        ("Sonos Beam (Gen 2)", 499.00),
        ("Sonos Arc Ultra", 999.00),
        ("Meta Quest 3S", 299.99),
    ],
    "Workspace": [
        ("Logitech MX Master 3S", 99.99),
        ("Logitech MX Keys S", 109.99),
        ("Logitech MX Mechanical Mini", 149.99),
        ("Logitech MX Anywhere 3S", 79.99),
        ("Logitech G PRO X SUPERLIGHT 2", 159.99),
        ("Razer DeathAdder V3 Pro", 149.99),
        ("Razer BlackWidow V4 Pro", 229.99),
        ("Razer Huntsman Mini", 119.99),
        ("Keychron Q1 Max", 219.99),
        ("Keychron K8 Pro", 109.99),
        ("Keychron K2 Version 2", 89.99),
        ("NuPhy Air75 V2", 129.95),
        ("Ducky One 3 Mini", 99.00),
        ("SteelSeries Apex Pro TKL Wireless", 249.99),
        ("Elgato Stream Deck MK.2", 149.99),
        ("Dell UltraSharp U2723QE", 629.99),
        ("LG UltraFine 27UQ850-W", 649.99),
        ("ASUS ProArt Display PA278CV", 399.99),
        ("BenQ ScreenBar Halo", 179.00),
        ("CalDigit TS4 Thunderbolt Station", 399.99),
    ],
}
SEED_PRODUCT_DESCRIPTIONS = {
    "Audio": "Personal and portable audio gear for music, calls, and everyday listening.",
    "Wearables": "A connected wearable designed for daily routines, fitness, and notifications.",
    "Power": "Portable charging and power equipment for work, travel, and home.",
    "Entertainment": "Home entertainment hardware for streaming, gaming, and movie nights.",
    "Workspace": "Computer and desk accessories for a more capable everyday setup.",
}
SEED_PRODUCTS = [
    (
        name,
        SEED_PRODUCT_DESCRIPTIONS[category],
        category,
        price,
        "#ffffff",
        "".join(word[0] for word in name.split()[:2]).upper(),
    )
    for category, products in SEED_PRODUCT_CATALOG.items()
    for name, price in products
]
LEGACY_SEED_PRODUCT_PREFIXES = (
    "Pulse wireless earbuds",
    "Orbit smart watch",
    "Volt power bank",
    "Beam mini projector",
    "Key mechanical keyboard",
    "Loop portable speaker",
)
PRODUCT_IMAGE_URLS = {
    "Pulse wireless earbuds": "https://images.unsplash.com/photo-1606220945770-b5b6c2c55bf1?fm=png&w=800&q=80",
    "Orbit smart watch": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?fm=png&w=800&q=80",
    "Volt power bank": "https://images.unsplash.com/photo-1609091839311-d5365f9ff1c5?fm=png&w=800&q=80",
    "Beam mini projector": "https://images.unsplash.com/photo-1535016120720-40c646be5580?fm=png&w=800&q=80",
    "Key mechanical keyboard": "https://images.unsplash.com/photo-1587829741301-dc798b83add3?fm=png&w=800&q=80",
    "Loop portable speaker": "https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?fm=png&w=800&q=80",
}
PRODUCT_CATEGORY_IMAGE_URLS = {
    "Audio": (
        "https://images.unsplash.com/photo-1608156639585-b3a032ef9689?fm=png&w=800&q=80",
        "https://images.unsplash.com/photo-1557063673-0493e05da49f?fm=png&w=800&q=80",
    ),
    "Wearables": (
        "https://images.unsplash.com/photo-1546868871-7041f2a55e12?fm=png&w=800&q=80",
        "https://images.unsplash.com/photo-1660844817855-3ecc7ef21f12?fm=png&w=800&q=80",
    ),
    "Power": (
        "https://images.unsplash.com/photo-1592318348310-f31b61a931c8?fm=png&w=800&q=80",
        "https://images.unsplash.com/photo-1585995603413-eb35b5f4a50b?fm=png&w=800&q=80",
    ),
    "Entertainment": (
        "https://images.unsplash.com/photo-1623762736174-77dccc1e571f?fm=png&w=800&q=80",
        "https://images.unsplash.com/photo-1698273300841-d9aee5c58922?fm=png&w=800&q=80",
    ),
    "Workspace": (
        "https://images.unsplash.com/photo-1745006485274-1f62da7ea85a?fm=png&w=800&q=80",
        "https://images.unsplash.com/photo-1600610429853-81d08d9ae4b1?fm=png&w=800&q=80",
    ),
}
_category_image_counts = {}
SEED_PRODUCT_IMAGE_URLS = {}
for _product in SEED_PRODUCTS:
    _name, _category = _product[0], _product[2]
    _image_options = PRODUCT_CATEGORY_IMAGE_URLS[_category]
    _image_index = _category_image_counts.get(_category, 0)
    SEED_PRODUCT_IMAGE_URLS[_name] = _image_options[_image_index % len(_image_options)]
    _category_image_counts[_category] = _image_index + 1
PRODUCT_IMAGE_MIGRATION = "product-name-png-images-v1"
PRODUCT_CATALOG_MIGRATION = "realistic-random-products-v1"
PRODUCT_IMAGE_LINK_MIGRATION = "category-product-image-links-v1"


def get_db():
    DATABASE.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    seed_setting = os.environ.get("SEED_DEMO_DATA")
    production = os.environ.get("APP_ENV", "development").strip().lower() == "production"
    if production and not os.environ.get("DATABASE_PATH"):
        raise RuntimeError("DATABASE_PATH must point to a persistent disk when APP_ENV=production.")
    if production and not DATABASE.is_absolute():
        raise RuntimeError("DATABASE_PATH must be an absolute path in production.")
    seed_value = seed_setting.strip().lower() if seed_setting is not None else None
    if seed_value is not None and seed_value not in {"1", "true", "yes", "0", "false", "no"}:
        raise RuntimeError("SEED_DEMO_DATA must be set to true or false.")
    if production and seed_value in {"1", "true", "yes"}:
        raise RuntimeError("Demo data cannot be enabled when APP_ENV=production.")
    seed_demo_data = not production and seed_value not in {"0", "false", "no"}

    connection = get_db()
    connection.executescript("""
        CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, description TEXT NOT NULL, category TEXT NOT NULL, price REAL NOT NULL, color TEXT NOT NULL, initials TEXT NOT NULL, created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY AUTOINCREMENT, customer_name TEXT NOT NULL, email TEXT NOT NULL, address TEXT NOT NULL, items TEXT NOT NULL, total REAL NOT NULL, status TEXT NOT NULL DEFAULT 'New', payment_method TEXT NOT NULL DEFAULT 'unrecorded', created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, email TEXT NOT NULL UNIQUE, password TEXT NOT NULL, created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS favorites (user_id INTEGER NOT NULL, product_id INTEGER NOT NULL, PRIMARY KEY (user_id, product_id));
        CREATE TABLE IF NOT EXISTS reviews (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, product_id INTEGER NOT NULL, rating INTEGER NOT NULL, comment TEXT NOT NULL, created_at TEXT NOT NULL);
    """)
    connection.execute("CREATE TABLE IF NOT EXISTS categories (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE, created_at TEXT NOT NULL, icon TEXT)")
    connection.execute("CREATE TABLE IF NOT EXISTS app_migrations (name TEXT PRIMARY KEY, applied_at TEXT NOT NULL)")
    category_columns = {row[1] for row in connection.execute("PRAGMA table_info(categories)").fetchall()}
    if "icon" not in category_columns:
        connection.execute("ALTER TABLE categories ADD COLUMN icon TEXT")
    order_columns = {row[1] for row in connection.execute("PRAGMA table_info(orders)").fetchall()}
    if "payment_method" not in order_columns:
        connection.execute("ALTER TABLE orders ADD COLUMN payment_method TEXT NOT NULL DEFAULT 'unrecorded'")
    product_columns = {row[1] for row in connection.execute("PRAGMA table_info(products)").fetchall()}
    for column in (
        "image1",
        "image2",
        "image3",
    ):
        if column not in product_columns:
            connection.execute(f"ALTER TABLE products ADD COLUMN {column} TEXT")
    user_columns = {row[1] for row in connection.execute("PRAGMA table_info(users)").fetchall()}
    for column, definition in {"role": "TEXT NOT NULL DEFAULT 'customer'", "avatar": "TEXT", "phone": "TEXT", "address": "TEXT", "card_name": "TEXT", "card_last4": "TEXT", "card_expiry": "TEXT"}.items():
        if column not in user_columns:
            connection.execute(f"ALTER TABLE users ADD COLUMN {column} {definition}")
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    count = connection.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    if count == 0 and seed_demo_data:
        if not connection.execute("SELECT 1 FROM users WHERE role = 'admin' LIMIT 1").fetchone():
            connection.execute("INSERT OR IGNORE INTO users (name, email, password, role, created_at) VALUES (?, ?, ?, ?, ?)", ("Morrow Admin", DEMO_ADMIN_EMAIL, generate_password_hash(DEMO_ADMIN_PASSWORD), "admin", datetime.now().isoformat(timespec="seconds")))
        if not connection.execute("SELECT 1 FROM users WHERE email = ?", (DEMO_STAFF_EMAIL,)).fetchone():
            connection.execute("INSERT INTO users (name, email, password, role, created_at) VALUES (?, ?, ?, ?, ?)", ("Morrow Staff", DEMO_STAFF_EMAIL, generate_password_hash(DEMO_STAFF_PASSWORD), "user", datetime.now().isoformat(timespec="seconds")))
        now = datetime.now().isoformat(timespec="seconds")
        connection.executemany(
            "INSERT INTO products (name, description, category, price, color, initials, created_at, image1) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            [
                product + (now, SEED_PRODUCT_IMAGE_URLS[product[0]])
                for product in SEED_PRODUCTS
            ],
        )
    catalog_migration_applied = connection.execute(
        "SELECT 1 FROM app_migrations WHERE name = ?", (PRODUCT_CATALOG_MIGRATION,)
    ).fetchone()
    if not catalog_migration_applied:
        legacy_patterns = tuple(
            f"{product_name} [0-9][0-9]" for product_name in LEGACY_SEED_PRODUCT_PREFIXES
        )
        legacy_name_filter = " OR ".join("name GLOB ?" for _ in legacy_patterns)
        legacy_product_ids = [
            row[0]
            for row in connection.execute(
                f"SELECT id FROM products WHERE {legacy_name_filter}", legacy_patterns
            )
        ]
        if legacy_product_ids:
            placeholders = ",".join("?" for _ in legacy_product_ids)
            connection.execute(
                f"DELETE FROM favorites WHERE product_id IN ({placeholders})",
                legacy_product_ids,
            )
            connection.execute(
                f"DELETE FROM reviews WHERE product_id IN ({placeholders})",
                legacy_product_ids,
            )
            connection.execute(
                f"DELETE FROM products WHERE id IN ({placeholders})", legacy_product_ids
            )
            now = datetime.now().isoformat(timespec="seconds")
            connection.executemany(
                "INSERT INTO products (name, description, category, price, color, initials, created_at, image1) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    product + (now, SEED_PRODUCT_IMAGE_URLS[product[0]])
                    for product in SEED_PRODUCTS
                ],
            )
        connection.execute(
            "INSERT INTO app_migrations (name, applied_at) VALUES (?, ?)",
            (PRODUCT_CATALOG_MIGRATION, datetime.now().isoformat(timespec="seconds")),
        )
    image_links_applied = connection.execute(
        "SELECT 1 FROM app_migrations WHERE name = ?", (PRODUCT_IMAGE_LINK_MIGRATION,)
    ).fetchone()
    if not image_links_applied:
        for product_name, image_url in SEED_PRODUCT_IMAGE_URLS.items():
            connection.execute(
                "UPDATE products SET image1 = ? WHERE name = ?",
                (image_url, product_name),
            )
        connection.execute(
            "INSERT INTO app_migrations (name, applied_at) VALUES (?, ?)",
            (PRODUCT_IMAGE_LINK_MIGRATION, datetime.now().isoformat(timespec="seconds")),
        )
    migration_applied = connection.execute(
        "SELECT 1 FROM app_migrations WHERE name = ?", (PRODUCT_IMAGE_MIGRATION,)
    ).fetchone()
    if not migration_applied:
        for product_name, image_url in PRODUCT_IMAGE_URLS.items():
            connection.execute(
                "UPDATE products SET image1 = ? WHERE name LIKE ?",
                (image_url, f"{product_name}%"),
            )
        connection.execute(
            "INSERT INTO app_migrations (name, applied_at) VALUES (?, ?)",
            (PRODUCT_IMAGE_MIGRATION, datetime.now().isoformat(timespec="seconds")),
        )
    connection.execute("INSERT OR IGNORE INTO categories (name, created_at) SELECT DISTINCT category, datetime('now') FROM products WHERE TRIM(category) != ''")
    connection.commit()
    connection.close()


def admin_access_required():
    user = session.get("user")
    if not user:
        return render_template("auth.html", mode="login", error="Please log in to access the admin desk."), 302
    if user.get("role") not in {"admin", "user"}:
        return render_template("access_denied.html"), 403
    return None


def owner_admin_required():
    access_error = admin_access_required()
    if access_error:
        return access_error
    if session["user"].get("role") != "admin":
        return render_template("access_denied.html"), 403
    return None


def currency(value):
    return f"${value:,.2f}"


def current_user_context():
    user = session.get("user")
    notifications = []
    favorite_product_ids = []
    if user:
        connection = get_db()
        account = connection.execute("SELECT id, name, email, role, avatar, card_name, card_last4, card_expiry FROM users WHERE id = ?", (user["id"],)).fetchone()
        if account:
            user = dict(account)
            favorite_product_ids = [
                favorite["product_id"]
                for favorite in connection.execute(
                    "SELECT product_id FROM favorites WHERE user_id = ?", (user["id"],)
                ).fetchall()
            ]
        notifications = connection.execute("SELECT id, total, status, created_at FROM orders WHERE email = ? ORDER BY id DESC LIMIT 5", (user["email"],)).fetchall()
        connection.close()
    return {
        "current_user": user,
        "notifications": notifications,
        "favorite_product_ids": favorite_product_ids,
    }
