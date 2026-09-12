# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

**Spendly** — a Flask expense tracker built as a step-by-step learning project.

Most backend functionality is intentionally unimplemented: routes and `database/db.py`
contain placeholder comments like `# Students will write this file in Step 1` and
`"Add expense — coming in Step 7"`. When asked to build a feature, check whether it
corresponds to one of these placeholders and implement it in place rather than
restructuring the app.

> The actual project root is `expense-tracker/`. The repo root also contains an
> unrelated `venv/` and `__MACOSX/` — ignore both.

---

## Commands

Run all commands from the `expense-tracker/` directory.

| Command | Purpose |
|---|---|
| `pip install -r requirements.txt` | Install deps (flask, werkzeug, pytest, pytest-flask) |
| `python app.py` | Run the dev server — http://localhost:5001 (debug=True) |
| `pytest` | Run tests (none exist yet — add under `expense-tracker/tests/`) |
| `pytest path/to/test_file.py::test_name` | Run a single test |

No build step, bundler, or linter is configured.

---

## Architecture

### `app.py`
Single Flask app; all routes defined directly on `app` (no blueprints, no app
factory). Routes render Jinja templates from `templates/` via `render_template`.

### `database/db.py`
Intended to hold:

| Function | Responsibility |
|---|---|
| `get_db()` | SQLite connection, row_factory + foreign keys enabled |
| `init_db()` | `CREATE TABLE IF NOT EXISTS` statements |
| `seed_db()` | Sample data |

Currently a stub; build it out as this functionality is needed. The SQLite
file (`expense_tracker.db`) is gitignored and created at runtime.

### `templates/base.html`
Shared layout (nav, footer, font/CSS links) with `{% block title %}`,
`{% block head %}`, `{% block content %}`, `{% block scripts %}`. Every page
template extends this base.

### `static/css/style.css`
Single global stylesheet, no CSS framework.

### `static/js/main.js`
Vanilla JS only, no JS framework/bundler. Add page behavior here or inline
via `{% block scripts %}` in individual templates.

---

## Conventions

- Keep the frontend framework-free (plain Jinja templates, vanilla CSS/JS) —
  don't introduce React/Vue/build tooling.
- Follow the existing route style in `app.py`: flat `@app.route` functions,
  not blueprints.
