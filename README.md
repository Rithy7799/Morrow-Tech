# MorrowTech

MorrowTech is an online store for everyday tech, built with Flask and SQLite. Shoppers can browse and search the catalog, keep a bag, check out, and track their orders. Store staff run the catalog, categories, orders, and accounts from an admin desk.

**Live site:** _add the hosted URL here_

> Checkout is a demo. Orders are recorded, but no payment is ever charged.

## Features

### Storefront
- **Catalog and search.** The home page lists products 20 per page and searches by name, description, or category. Each category also has its own page.
- **Product pages.** Up to three images per product, an average star rating, customer reviews, and related items from the same category.
- **Bag.** The bag is kept in the browser's `localStorage`, so it stays across visits without an account. It opens as a drawer from any page.
- **Checkout.** Buy everything in the bag, or use **Buy now** to buy one product straight from its page. Choose a saved card or KHQR as the payment method. You have to be signed in to check out, and the server reprices every item from the database instead of trusting the browser.
- **Accounts.** Register, sign in, and sign out. The profile page holds your contact details, delivery address, profile photo, and a saved card (only the last four digits are stored), plus your order history and favorites.
- **Favorites and reviews.** Save products to a favorites list, and rate products from 1 to 5 stars with a comment.
- **Notifications and invoices.** Each order shows up as a notification with its status (New, Packed, Shipped, or Cancelled), and its invoice opens in a pop-up.
- **Responsive layout.** On phones and tablets the header sticks to the top and a bottom navigation bar appears.

### Admin desk (`/admin`)
- **Dashboard.** An overview of the catalog, recent orders, and users.
- **Products.** Add, edit, and delete products. Each of the three image slots takes either an uploaded PNG, JPEG, or WebP file or an HTTP(S) link. Uploaded images that nothing uses any more are deleted.
- **Categories.** Create, rename, and delete categories.
- **Orders.** Change an order's status.
- **Users.** Create customer or staff accounts (admins only).

### Roles

| Role       | Stored as  | Access                                               |
|------------|------------|------------------------------------------------------|
| Customer   | `customer` | Storefront, profile, checkout                        |
| Staff      | `user`     | Everything above, plus the admin desk, except creating accounts |
| Admin      | `admin`    | Everything, including creating accounts              |

## Tech stack

- **Backend:** Python, Flask 3, SQLite (through the standard `sqlite3` module)
- **Frontend:** Jinja2 templates, plain CSS, plain JavaScript, Bootstrap Icons, and Google Fonts
- **Security:** Werkzeug password hashing, HTTP-only `SameSite=Lax` session cookies (marked secure in production), and checks that only allow redirects within the site after sign-in
- **Serving:** Gunicorn, through the `Procfile`

## Running it locally

You need Python 3.9 or newer.

```bash
git clone https://github.com/Rithy7799/Marrow-Tech.git
cd Marrow-Tech
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Then open <http://127.0.0.1:8555>.

The database (`shop.db`) and its tables are created on first run, and existing databases get any new columns added automatically. In development, an empty catalog is filled with 100 sample products and two demo accounts:

The seeded catalog uses example electronics listings. Its image links are representative, category-relevant Unsplash photos, not photos of each exact model. Descriptions and prices are illustrative; verify product details, pricing, availability, and image suitability before offering items for sale.

| Account | Email               | Password   |
|---------|---------------------|------------|
| Admin   | `admin@morrow.test` | `admin123` |
| Staff   | `staff@morrow.test` | `staff123` |

These passwords are public. Never use them on a live store.

### Environment variables

| Variable         | Default                  | Purpose |
|------------------|--------------------------|---------|
| `APP_ENV`        | `development`            | Set to `production` on the live host. |
| `SECRET_KEY`     | a development-only key   | Signs session cookies. **Required** in production. |
| `DATABASE_PATH`  | `./shop.db`              | Where the SQLite file lives. In production it is **required** and must be an absolute path. |
| `SEED_DEMO_DATA` | on in development        | Set to `false` to start with an empty catalog. It cannot be turned on in production. |
| `HOST` / `PORT`  | `127.0.0.1` / `8555`     | Address used by `python app.py`. |
| `FLASK_DEBUG`    | off                      | Set to `true` to turn on the debugger locally. It is always off in production. |

## Deployment

The app is deployed with the included `Procfile`:

```
web: APP_ENV=production gunicorn --workers 2 --preload --bind 0.0.0.0:${PORT:-8000} app:application
```

`app:application` is the WSGI entry point, so any WSGI host can run it. To deploy it yourself:

1. Set these environment variables on the host:
   - `SECRET_KEY`: a long random value, which you can generate with
     `python -c "import secrets; print(secrets.token_hex(32))"`
   - `DATABASE_PATH`: an absolute path on a persistent disk, for example `/data/shop.db`
   - `PORT`: usually set by the host for you
2. Keep `static/uploads/` on persistent storage too, because product images and profile photos are saved there. Back up the database and the uploads together.
3. For a new database, create the first administrator with a one-off command:
   ```bash
   flask --app app create-admin
   ```
   It asks for a name, an email, and a password of at least 12 characters. Then sign in and add categories and products from the admin desk.
4. When moving an existing store, copy its database and `static/uploads/` to the persistent storage before starting the app, and remove or change any demo accounts first.
5. Serve the site over HTTPS. Production session cookies are only sent over secure connections.

The app refuses to start in production if `SECRET_KEY` or `DATABASE_PATH` is missing, or if demo data is turned on.

## Routes

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Storefront (`?q=` to search, `?page=` to change pages) |
| GET | `/about` | About page |
| GET | `/category/<name>` | Products in one category |
| GET | `/product/<id>` | Product page |
| POST | `/product/<id>/favorite` | Add or remove a favorite |
| POST | `/product/<id>/review` | Post a review |
| GET | `/checkout` | Checkout (`?buy_now=<id>` buys a single product) |
| GET | `/profile`, POST `/profile/update` | View and update your profile |
| GET | `/notifications` | Order updates |
| GET, POST | `/register`, `/login`; GET `/logout` | Account sign-up, sign-in, and sign-out |
| POST | `/api/purchases` (also `/api/orders`) | Place an order (JSON) |
| GET | `/api/orders/<id>` | Order invoice (JSON) |
| GET | `/api/products/images?ids=1,2` | First image of each listed product (JSON) |
| GET | `/admin`, `/admin/products` | Admin dashboard and product manager |
| POST | `/admin/products`, `/admin/products/<id>/edit`, `/admin/products/<id>/delete` | Add, edit, and delete products |
| POST | `/admin/categories`, `/admin/categories/<id>/edit`, `/admin/categories/<id>/delete` | Add, rename, and delete categories |
| POST | `/admin/orders/<id>/status` | Change an order's status |
| POST | `/admin/customers` | Create an account (admins only) |

## Project structure

```
Marrow-Tech/
├── app.py               # App setup, blueprints, the create-admin command, WSGI entry point
├── store.py             # Database connection, schema and migrations, demo data, access checks
├── routes/
│   ├── front.py         # Storefront, product pages, profile, checkout, JSON API
│   ├── auth.py          # Register, sign-in, sign-out
│   └── admin.py         # Admin desk: products, categories, orders, users
├── templates/           # Jinja2 pages (base layout, store, checkout, profile, admin)
├── static/
│   ├── styles.css       # All styling, including the mobile and tablet layouts
│   ├── app.js           # Bag, checkout, invoice pop-up, admin tabs, notifications
│   └── uploads/         # Uploaded product images and profile photos
├── requirements.txt     # Flask and Gunicorn
└── Procfile             # Gunicorn start command for the host
```

## Database

SQLite with six tables:

- **products**: name, description, category, price, a fallback color and initials, and up to three images
- **categories**: the category names
- **users**: name, email, password hash, role, profile photo, phone, address, and saved card details (cardholder name, last four digits, expiry date)
- **orders**: customer details, a list of the items bought, the total, the status, and the payment method
- **favorites**: which users saved which products
- **reviews**: a 1–5 star rating and a comment, linked to a user and a product

## License

This project is available for personal testing and learning only. Business or
other commercial use requires prior written approval from the copyright
holder. See [LICENSE](./LICENSE) for the full terms.
