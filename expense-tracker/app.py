import os
import sqlite3

from flask import Flask, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from database.db import get_db, init_db, seed_db

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")

with app.app_context():
    init_db()
    seed_db()


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user_id"):
        return redirect(url_for("profile"))

    if request.method == "GET":
        return render_template("register.html")

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    if not name or not email or not password:
        return render_template("register.html", error="All fields are required."), 400

    if len(password) < 8:
        return render_template("register.html", error="Password must be at least 8 characters."), 400

    db = get_db()
    try:
        db.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email, generate_password_hash(password)),
        )
        db.commit()
    except sqlite3.IntegrityError:
        return render_template("register.html", error="An account with that email already exists."), 400
    finally:
        db.close()

    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("profile"))

    if request.method == "GET":
        return render_template("login.html")

    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    db = get_db()
    user = db.execute(
        "SELECT id, name, password_hash FROM users WHERE email = ?",
        (email,),
    ).fetchone()
    db.close()

    if user is None or not check_password_hash(user["password_hash"], password):
        return render_template("login.html", error="Invalid email or password."), 400

    session["user_id"] = user["id"]
    session["name"] = user["name"]
    flash(f"Welcome back, {user['name']}! You're logged in.", "success")
    return redirect(url_for("profile"))


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/profile")
def profile():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    user = {
        "name": "Demo User",
        "email": "demo@spendly.com",
        "initials": "DU",
        "member_since": "Member since March 2025",
    }

    stats = {
        "total_spent_display": "₹20,000.00",
        "transaction_count": 6,
        "top_category": "Food",
    }

    transactions = [
        {"date": "12 Sep 2026", "description": "Grocery shopping at BigBasket", "category": "Food", "amount_display": "₹1,240.00"},
        {"date": "10 Sep 2026", "description": "Electricity bill - BESCOM", "category": "Bills", "amount_display": "₹2,150.50"},
        {"date": "08 Sep 2026", "description": "Uber rides to office", "category": "Transport", "amount_display": "₹680.00"},
        {"date": "06 Sep 2026", "description": "Movie night with friends", "category": "Entertainment", "amount_display": "₹950.00"},
        {"date": "03 Sep 2026", "description": "New running shoes", "category": "Shopping", "amount_display": "₹3,499.00"},
        {"date": "01 Sep 2026", "description": "Pharmacy - vitamins & supplements", "category": "Health", "amount_display": "₹610.25"},
    ]

    categories = [
        {"name": "Food", "amount_display": "₹6,000.00", "percentage": 30, "bar_step": 30},
        {"name": "Shopping", "amount_display": "₹4,000.00", "percentage": 20, "bar_step": 20},
        {"name": "Bills", "amount_display": "₹4,000.00", "percentage": 20, "bar_step": 20},
        {"name": "Transport", "amount_display": "₹2,000.00", "percentage": 10, "bar_step": 10},
        {"name": "Entertainment", "amount_display": "₹2,000.00", "percentage": 10, "bar_step": 10},
        {"name": "Health", "amount_display": "₹2,000.00", "percentage": 10, "bar_step": 10},
    ]

    return render_template(
        "profile.html",
        user=user,
        stats=stats,
        transactions=transactions,
        categories=categories,
    )


@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    app.run(debug=True, port=5001)
