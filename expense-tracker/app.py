import os
import sqlite3
from datetime import date

from flask import Flask, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from database.db import get_db, init_db, seed_db

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")

with app.app_context():
    init_db()
    seed_db()


# ------------------------------------------------------------------ #
# Profile helpers                                                    #
# ------------------------------------------------------------------ #

def _format_currency(amount):
    return f"₹{amount:,.2f}"


def _format_transaction_date(date_str):
    return date.fromisoformat(date_str).strftime("%d %b %Y")


def _get_profile_transactions(db, user_id):
    rows = db.execute(
        "SELECT date, description, category, amount FROM expenses "
        "WHERE user_id = ? ORDER BY date DESC, id DESC",
        (user_id,),
    ).fetchall()
    return [
        {
            "date": _format_transaction_date(r["date"]),
            "description": r["description"],
            "category": r["category"],
            "amount_display": _format_currency(r["amount"]),
        }
        for r in rows
    ]


def _get_profile_stats(db, user_id):
    total, count = db.execute(
        "SELECT COALESCE(SUM(amount), 0), COUNT(*) FROM expenses WHERE user_id = ?",
        (user_id,),
    ).fetchone()
    top = db.execute(
        "SELECT category FROM expenses WHERE user_id = ? "
        "GROUP BY category ORDER BY SUM(amount) DESC LIMIT 1",
        (user_id,),
    ).fetchone()
    return {
        "total_spent_display": _format_currency(total),
        "transaction_count": count,
        "top_category": top["category"] if top else "—",
    }


def _get_profile_categories(db, user_id):
    rows = db.execute(
        "SELECT category, SUM(amount) AS total FROM expenses "
        "WHERE user_id = ? GROUP BY category ORDER BY total DESC",
        (user_id,),
    ).fetchall()
    grand_total = sum(r["total"] for r in rows)
    categories = []
    for r in rows:
        pct = round(r["total"] / grand_total * 100) if grand_total else 0
        bar_step = min(100, max(10, round(pct / 10) * 10))
        categories.append({
            "name": r["category"],
            "amount_display": _format_currency(r["total"]),
            "percentage": pct,
            "bar_step": bar_step,
        })
    return categories


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

    db = get_db()
    row = db.execute(
        "SELECT name, email, created_at FROM users WHERE id = ?",
        (session["user_id"],),
    ).fetchone()

    parts = row["name"].split()
    initials = "".join(p[0] for p in parts[:2]).upper()
    member_since = date.fromisoformat(row["created_at"][:10]).strftime("Member since %B %Y")

    user = {
        "name": row["name"],
        "email": row["email"],
        "initials": initials,
        "member_since": member_since,
    }
    stats = _get_profile_stats(db, session["user_id"])
    transactions = _get_profile_transactions(db, session["user_id"])
    categories = _get_profile_categories(db, session["user_id"])
    db.close()

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
