import sqlite3

import pytest
from werkzeug.security import generate_password_hash

import app as app_module
from database import db as db_module


@pytest.fixture
def client(tmp_path, monkeypatch):
    db_path = str(tmp_path / "test.db")
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    db_module.init_db()

    conn = sqlite3.connect(db_path)
    for name, email in (("Alice Test", "alice@test.com"), ("Bob Other", "bob@test.com")):
        conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email, generate_password_hash("password123")),
        )
    rows = [
        (1, 10.0, "Food", "2026-01-05", "Jan food"),
        (1, 20.0, "Bills", "2026-02-10", "Feb bills"),
        (1, 30.0, "Food", "2026-03-15", "Mar food"),
        (2, 999.0, "Shopping", "2026-02-10", "Bob secret"),
    ]
    conn.executemany(
        "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
        rows,
    )
    conn.commit()
    conn.close()

    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as c:
        with c.session_transaction() as s:
            s["user_id"] = 1
            s["name"] = "Alice Test"
        yield c


def get(client, query=""):
    resp = client.get("/profile" + query)
    return resp, resp.get_data(as_text=True)


def test_no_params_shows_everything(client):
    resp, html = get(client)
    assert resp.status_code == 200
    assert "₹60.00" in html
    assert "Recent transactions" in html
    assert "Jan food" in html and "Mar food" in html


def test_from_only(client):
    _, html = get(client, "?date_from=2026-02-10")
    assert "Feb bills" in html and "Mar food" in html
    assert "Jan food" not in html
    assert "₹50.00" in html


def test_to_only(client):
    _, html = get(client, "?date_to=2026-02-10")
    assert "Jan food" in html and "Feb bills" in html
    assert "Mar food" not in html
    assert "₹30.00" in html


def test_range_is_inclusive(client):
    _, html = get(client, "?date_from=2026-02-10&date_to=2026-02-10")
    assert "Feb bills" in html
    assert "Jan food" not in html and "Mar food" not in html
    assert "₹20.00" in html
    assert "100%" in html


def test_inputs_prefilled_and_title_changes(client):
    _, html = get(client, "?date_from=2026-01-01&date_to=2026-12-31")
    assert 'value="2026-01-01"' in html
    assert 'value="2026-12-31"' in html
    assert "Transactions</h2>" in html


def test_empty_range(client):
    resp, html = get(client, "?date_from=2030-01-01")
    assert resp.status_code == 200
    assert "₹0.00" in html
    assert "No expenses in this period" in html


def test_start_after_end_shows_error_and_unfiltered(client):
    resp, html = get(client, "?date_from=2026-03-01&date_to=2026-01-01")
    assert resp.status_code == 200
    assert "Start date must be on or before end date." in html
    assert "₹60.00" in html


def test_invalid_date_does_not_crash(client):
    resp, html = get(client, "?date_from=not-a-date")
    assert resp.status_code == 200
    assert "Enter valid dates." in html
    assert "₹60.00" in html


def test_blank_params_treated_as_missing(client):
    resp, html = get(client, "?date_from=&date_to=")
    assert resp.status_code == 200
    assert "Enter valid dates." not in html
    assert "₹60.00" in html


def test_sql_injection_string_is_harmless(client):
    resp, html = get(client, "?date_from=2026-01-01' OR '1'='1")
    assert resp.status_code == 200
    assert "Bob secret" not in html
    assert "₹999.00" not in html


def test_other_users_data_never_shown(client):
    _, html = get(client, "?date_from=2026-02-10&date_to=2026-02-10")
    assert "Bob secret" not in html


def test_logged_out_redirects_to_login():
    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as c:
        resp = c.get("/profile?date_from=2026-01-01")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]
