"""Tests for Step 6: date filter on GET /profile (spec 06-date-filter-profile-page)."""
import re
import sqlite3

import pytest
from werkzeug.security import generate_password_hash

import database.db as db_module
from app import app as flask_app

ERR_RANGE = "Start date must be on or before end date."
EMPTY_MSG = "No expenses in this period"

# (date, description, category, amount) for user A
A_EXPENSES = [
    ("2026-01-01", "A-jan01", "Food", 100.00),
    ("2026-01-15", "A-jan15", "Transport", 200.00),
    ("2026-01-31", "A-jan31", "Food", 300.00),
    ("2026-02-10", "A-feb10", "Bills", 400.00),
]
B_EXPENSES = [
    ("2026-01-15", "B-secret", "Shopping", 9999.00),
    ("2026-02-10", "B-secret2", "Shopping", 7777.00),
]
ALL_A = [e[1] for e in A_EXPENSES]


@pytest.fixture
def app(tmp_path, monkeypatch):
    db_file = str(tmp_path / "test_filter.db")
    monkeypatch.setattr(db_module, "DB_PATH", db_file)
    flask_app.config.update(TESTING=True, SECRET_KEY="test-secret")
    db_module.init_db()
    conn = sqlite3.connect(db_file)
    for uid, name, email in ((1, "Alice A", "a@example.com"), (2, "Bob B", "b@example.com")):
        conn.execute(
            "INSERT INTO users (id, name, email, password_hash) VALUES (?, ?, ?, ?)",
            (uid, name, email, generate_password_hash("pw12345")),
        )
    for d, desc, cat, amt in A_EXPENSES:
        conn.execute(
            "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (1, ?, ?, ?, ?)",
            (amt, cat, d, desc),
        )
    for d, desc, cat, amt in B_EXPENSES:
        conn.execute(
            "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (2, ?, ?, ?, ?)",
            (amt, cat, d, desc),
        )
    conn.commit()
    conn.close()
    yield flask_app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_client(client):
    with client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["name"] = "Alice A"
    return client


def _get(client, query=""):
    return client.get("/profile" + query)


def _text(resp):
    return resp.get_data(as_text=True)


def _present(html):
    return [d for d in ALL_A if d in html]


def _snapshot(db_file):
    conn = sqlite3.connect(db_file)
    rows = conn.execute("SELECT * FROM expenses ORDER BY id").fetchall()
    users = conn.execute("SELECT * FROM users ORDER BY id").fetchall()
    conn.close()
    return rows, users


# ------------------------------------------------------------------ #
# Auth guard
# ------------------------------------------------------------------ #
class TestAuthGuard:
    @pytest.mark.parametrize(
        "query",
        ["", "?date_from=2026-01-01", "?date_to=2026-02-01",
         "?date_from=2026-01-01&date_to=2026-02-01", "?date_from=garbage"],
    )
    def test_profile_logged_out_with_query_redirects_to_login(self, client, query):
        resp = _get(client, query)
        assert resp.status_code == 302, "Expected redirect when logged out"
        assert "/login" in resp.headers["Location"]


# ------------------------------------------------------------------ #
# Unfiltered behaviour unchanged
# ------------------------------------------------------------------ #
class TestUnfiltered:
    def test_no_query_shows_all_own_expenses(self, auth_client):
        resp = _get(auth_client)
        html = _text(resp)
        assert resp.status_code == 200
        assert _present(html) == ALL_A
        assert "₹1,000.00" in html, "Total should be sum of all A expenses"

    def test_no_query_title_is_recent_transactions(self, auth_client):
        html = _text(_get(auth_client))
        assert "Recent transactions" in html

    def test_no_query_shows_no_error_or_empty_message(self, auth_client):
        html = _text(_get(auth_client))
        assert ERR_RANGE not in html
        assert EMPTY_MSG not in html

    def test_no_query_does_not_show_other_users_data(self, auth_client):
        html = _text(_get(auth_client))
        assert "B-secret" not in html
        assert "₹9,999.00" not in html

    @pytest.mark.parametrize("query", ["?date_from=&date_to=", "?date_from=", "?date_to="])
    def test_blank_params_treated_as_not_provided(self, auth_client, query):
        resp = _get(auth_client, query)
        html = _text(resp)
        assert resp.status_code == 200
        assert _present(html) == ALL_A
        assert ERR_RANGE not in html
        assert "Recent transactions" in html, "Blank params should not activate filter"


# ------------------------------------------------------------------ #
# Filtering behaviour
# ------------------------------------------------------------------ #
class TestFiltering:
    def test_only_from_shows_on_or_after(self, auth_client):
        html = _text(_get(auth_client, "?date_from=2026-01-15"))
        assert _present(html) == ["A-jan15", "A-jan31", "A-feb10"]

    def test_only_to_shows_on_or_before(self, auth_client):
        html = _text(_get(auth_client, "?date_to=2026-01-15"))
        assert _present(html) == ["A-jan01", "A-jan15"]

    def test_both_dates_show_only_inside_range(self, auth_client):
        html = _text(_get(auth_client, "?date_from=2026-01-02&date_to=2026-01-30"))
        assert _present(html) == ["A-jan15"]

    def test_range_boundaries_are_inclusive(self, auth_client):
        html = _text(_get(auth_client, "?date_from=2026-01-01&date_to=2026-01-31"))
        assert _present(html) == ["A-jan01", "A-jan15", "A-jan31"]

    def test_single_day_range_returns_that_day(self, auth_client):
        html = _text(_get(auth_client, "?date_from=2026-01-15&date_to=2026-01-15"))
        assert _present(html) == ["A-jan15"]

    def test_filter_active_title_reads_transactions(self, auth_client):
        html = _text(_get(auth_client, "?date_from=2026-01-01"))
        assert "Recent transactions" not in html
        assert "Transactions" in html

    def test_stats_reflect_filtered_set(self, auth_client):
        # Jan only: 100 + 200 + 300 = 600, 3 transactions, top category Food (400)
        html = _text(_get(auth_client, "?date_from=2026-01-01&date_to=2026-01-31"))
        assert "₹600.00" in html
        assert "₹1,000.00" not in html
        assert re.search(r"profile-stat-label\">Transactions</div>\s*<div[^>]*>3<", html), \
            "Transaction count should be 3"
        assert re.search(r"Top category</div>\s*<div[^>]*>Food<", html)

    def test_top_category_changes_with_filter(self, auth_client):
        # Only Feb: Bills is the only category
        html = _text(_get(auth_client, "?date_from=2026-02-01"))
        assert re.search(r"Top category</div>\s*<div[^>]*>Bills<", html)
        assert "₹400.00" in html

    def test_category_breakdown_reflects_filter(self, auth_client):
        html = _text(_get(auth_client, "?date_from=2026-02-01"))
        breakdown = html.split("Category breakdown")[1]
        assert "Bills" in breakdown
        assert "Food" not in breakdown
        assert "Transport" not in breakdown

    @pytest.mark.parametrize(
        "query",
        ["?date_from=2026-01-01&date_to=2026-01-31", "?date_from=2026-01-01", "?date_to=2026-02-28", ""],
    )
    def test_category_percentages_sum_to_100(self, auth_client, query):
        html = _text(_get(auth_client, query))
        breakdown = html.split("Category breakdown")[1]
        pcts = [float(p) for p in re.findall(r"([\d.]+)%", breakdown)]
        assert pcts, "Expected at least one percentage"
        assert abs(sum(pcts) - 100) <= 1.0, f"Percentages sum to {sum(pcts)}"

    def test_amounts_use_rupee_symbol(self, auth_client):
        html = _text(_get(auth_client, "?date_from=2026-01-01&date_to=2026-01-31"))
        assert "₹" in html
        assert "$" not in html.split("profile-stats")[1].split("Category breakdown")[0]


# ------------------------------------------------------------------ #
# Pre-filled form / Clear link
# ------------------------------------------------------------------ #
class TestForm:
    def test_form_has_date_inputs_apply_and_clear(self, auth_client):
        html = _text(_get(auth_client))
        assert 'type="date"' in html
        assert 'name="date_from"' in html
        assert 'name="date_to"' in html
        assert "Apply" in html
        assert "Clear" in html
        assert re.search(r"<form[^>]*method=\"get\"", html, re.I), "Filter form must use GET"

    def test_inputs_prefilled_with_applied_range(self, auth_client):
        html = _text(_get(auth_client, "?date_from=2026-01-01&date_to=2026-01-31"))
        assert 'value="2026-01-01"' in html
        assert 'value="2026-01-31"' in html

    def test_inputs_not_prefilled_without_filter(self, auth_client):
        html = _text(_get(auth_client))
        assert not re.search(r'value="\d{4}-\d{2}-\d{2}"', html)

    def test_clear_link_points_to_unfiltered_profile(self, auth_client):
        html = _text(_get(auth_client, "?date_from=2026-01-01"))
        assert re.search(r'<a[^>]*href="/profile"[^>]*>\s*Clear', html), "Clear must link to /profile"

    def test_following_clear_returns_unfiltered(self, auth_client):
        resp = auth_client.get("/profile")
        assert _present(_text(resp)) == ALL_A


# ------------------------------------------------------------------ #
# Empty result
# ------------------------------------------------------------------ #
class TestEmptyRange:
    def test_range_with_no_matches_shows_empty_state(self, auth_client):
        resp = _get(auth_client, "?date_from=2025-01-01&date_to=2025-12-31")
        html = _text(resp)
        assert resp.status_code == 200
        assert EMPTY_MSG in html
        assert "₹0.00" in html
        assert re.search(r"Transactions</div>\s*<div[^>]*>0<", html), "Count should be 0"
        assert _present(html) == []
        assert ERR_RANGE not in html
        assert "profile-filter-error" not in html

    def test_empty_range_has_empty_breakdown(self, auth_client):
        html = _text(_get(auth_client, "?date_from=2025-01-01&date_to=2025-12-31"))
        breakdown = html.split("Category breakdown")[1]
        assert EMPTY_MSG in breakdown
        assert "%" not in breakdown

    def test_empty_range_does_not_show_other_users_matches(self, auth_client):
        # user B has expenses in this range, A does not
        html = _text(_get(auth_client, "?date_from=2026-03-01"))
        assert "B-secret" not in html
        assert EMPTY_MSG in html


# ------------------------------------------------------------------ #
# Validation errors
# ------------------------------------------------------------------ #
class TestValidation:
    def test_from_after_to_shows_error_and_unfiltered_data(self, auth_client):
        resp = _get(auth_client, "?date_from=2026-02-01&date_to=2026-01-01")
        html = _text(resp)
        assert resp.status_code == 200
        assert ERR_RANGE in html
        assert _present(html) == ALL_A, "Should fall back to unfiltered data"
        assert "₹1,000.00" in html

    @pytest.mark.parametrize(
        "query",
        [
            "?date_from=not-a-date",
            "?date_to=not-a-date",
            "?date_from=2026-13-45",
            "?date_from=2026-02-30",
            "?date_from=01/02/2026",
            "?date_from=abc&date_to=2026-01-01",
            "?date_from=2026-01-01&date_to=xyz",
        ],
    )
    def test_invalid_date_no_crash_and_shows_error(self, auth_client, query):
        resp = _get(auth_client, query)
        html = _text(resp)
        assert resp.status_code == 200, f"Got {resp.status_code} for {query}"
        assert "profile-filter-error" in html, "Expected an inline error message"
        assert "B-secret" not in html

    def test_invalid_date_falls_back_to_unfiltered(self, auth_client):
        html = _text(_get(auth_client, "?date_from=not-a-date"))
        assert _present(html) == ALL_A

    @pytest.mark.parametrize(
        "payload",
        [
            "2026-01-01' OR '1'='1",
            "2026-01-01'; DROP TABLE expenses;--",
            "' OR 1=1 --",
        ],
    )
    @pytest.mark.parametrize("param", ["date_from", "date_to"])
    def test_sql_injection_returns_normally_and_leaks_nothing(self, auth_client, app, param, payload):
        resp = auth_client.get("/profile", query_string={param: payload})
        html = _text(resp)
        assert resp.status_code == 200
        assert "B-secret" not in html
        assert "₹9,999.00" not in html
        conn = sqlite3.connect(db_module.DB_PATH)
        count = conn.execute("SELECT COUNT(*) FROM expenses").fetchone()[0]
        conn.close()
        assert count == len(A_EXPENSES) + len(B_EXPENSES), "Expenses table must be intact"

    def test_very_long_param_does_not_crash(self, auth_client):
        resp = _get(auth_client, "?date_from=" + "9" * 5000)
        assert resp.status_code == 200


# ------------------------------------------------------------------ #
# User scoping and data integrity
# ------------------------------------------------------------------ #
class TestIsolationAndIntegrity:
    @pytest.mark.parametrize(
        "query",
        ["?date_from=2026-01-15&date_to=2026-01-15", "?date_from=2026-01-01",
         "?date_to=2026-12-31", "?date_from=2026-02-10&date_to=2026-02-10"],
    )
    def test_filter_never_exposes_other_users_expenses(self, auth_client, query):
        html = _text(_get(auth_client, query))
        assert "B-secret" not in html
        assert "₹9,999.00" not in html
        assert "₹7,777.00" not in html

    def test_other_user_sees_only_own_filtered_data(self, client):
        with client.session_transaction() as sess:
            sess["user_id"] = 2
        html = _text(_get(client, "?date_from=2026-01-01&date_to=2026-01-31"))
        assert "B-secret" in html
        assert "B-secret2" not in html
        assert not _present(html), "User B must not see user A expenses"
        assert "₹9,999.00" in html

    def test_filtering_does_not_modify_database(self, auth_client):
        before = _snapshot(db_module.DB_PATH)
        for q in ("?date_from=2026-01-01&date_to=2026-01-31", "?date_from=bad",
                  "?date_from=2026-05-01&date_to=2026-01-01", "?date_to=2025-01-01"):
            _get(auth_client, q)
        after = _snapshot(db_module.DB_PATH)
        assert before == after, "Filtering must be read-only"

    def test_filter_is_repeatable_same_result(self, auth_client):
        q = "?date_from=2026-01-01&date_to=2026-01-31"
        assert _present(_text(_get(auth_client, q))) == _present(_text(_get(auth_client, q)))
