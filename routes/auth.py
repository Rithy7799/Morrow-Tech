from datetime import datetime
import sqlite3
from flask import Blueprint, redirect, render_template, request, session, url_for
from urllib.parse import urlsplit
from werkzeug.security import check_password_hash, generate_password_hash
from store import get_db

auth_bp = Blueprint("auth", __name__)

def safe_next_url(target):
    if not target or not target.startswith("/") or target.startswith("//") or "\\" in target:
        return None
    parsed = urlsplit(target)
    if parsed.scheme or parsed.netloc:
        return None
    return target

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    next_url = safe_next_url(request.values.get("next", ""))
    if request.method == "POST":
        name, email, password = (request.form.get(field, "").strip() for field in ("name", "email", "password"))
        if not name or not email or len(password) < 6:
            return render_template("auth.html", mode="register", error="Enter your name, email, and a password of at least 6 characters.", next_url=next_url)
        if password != request.form.get("confirm_password", ""):
            return render_template("auth.html", mode="register", error="Passwords do not match.", next_url=next_url)
        connection = get_db()
        try:
            cursor = connection.execute("INSERT INTO users (name, email, password, role, created_at) VALUES (?, ?, ?, ?, ?)", (name, email.lower(), generate_password_hash(password), "customer", datetime.now().isoformat(timespec="seconds")))
            connection.commit()
        except sqlite3.IntegrityError:
            connection.close()
            return render_template("auth.html", mode="register", error="An account with that email already exists.", next_url=next_url)
        connection.close()
        session["user"] = {"id": cursor.lastrowid, "name": name, "email": email.lower(), "role": "customer"}
        return redirect(next_url or url_for("front.profile"))
    return render_template("auth.html", mode="register", next_url=next_url)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    next_url = safe_next_url(request.values.get("next", ""))
    if request.method == "POST":
        email, password = request.form.get("email", "").strip().lower(), request.form.get("password", "")
        connection = get_db()
        user = connection.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        connection.close()
        if not user or not check_password_hash(user["password"], password):
            return render_template("auth.html", mode="login", error="That email and password combination was not found.", next_url=next_url)
        session["user"] = {"id": user["id"], "name": user["name"], "email": user["email"], "role": user["role"]}
        return redirect(next_url or url_for("front.profile"))
    return render_template("auth.html", mode="login", next_url=next_url)

@auth_bp.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("front.storefront"))
