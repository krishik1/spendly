# Spec: Registration

## Overview
Registration lets a new visitor create a Spendly account by submitting their
name, email, and password on the existing `/register` page. It is the first
authentication step in the roadmap — it turns the `users` table from Step 1
into a table people can actually populate, and it unblocks Login (Step 3),
Profile (Step 4), and every expense-tracking feature that requires a
logged-in `user_id`. This spec is written retroactively: the feature was
implemented directly on `master` (commit `bc881e8`) during this session,
ahead of the spec-first branch workflow, and is documented here for the
project record.

## Depends on
- Step 1 (database setup) — requires the `users` table, `get_db()`, and
  `init_db()` from `database/db.py`.

## Routes
- `GET /register` — render the signup form — public
- `POST /register` — validate input, hash the password, insert the new
  user, redirect to `/login` on success — public

## Database changes
No database changes. Uses the existing `users` table as defined in
`database/db.py` (`id`, `name`, `email` UNIQUE, `password_hash`,
`created_at`). The `UNIQUE` constraint on `email` is relied on directly
(caught as `sqlite3.IntegrityError`) instead of a pre-check query.

## Templates
- **Create:** none — `templates/register.html` already existed with the
  form (`name`, `email`, `password` fields posting to `/register`) and an
  `{% if error %}` block for inline error display.
- **Modify:** none required. `register.html` is reused as-is for both the
  initial GET render and for re-rendering with `error` set on validation
  failures.

## Files to change
- `expense-tracker/app.py` — add `POST` handling to the `/register` route.

## Files to create
None.

## New dependencies
No new dependencies. Uses `werkzeug.security.generate_password_hash`,
already a Flask dependency, and the standard library `sqlite3`.

## Rules for implementation
- No SQLAlchemy or ORMs.
- Parameterised queries only.
- Passwords hashed with werkzeug (`generate_password_hash`).
- Use CSS variables — never hardcode hex values.
- All templates extend `base.html`.

## Definition of done
- [x] Visiting `/register` renders the signup form.
- [x] Submitting valid name/email/password creates a row in `users` with a
      hashed password and redirects to `/login`.
- [x] Submitting with any field blank re-renders the form with
      "All fields are required."
- [x] Submitting a password under 8 characters re-renders the form with
      "Password must be at least 8 characters."
- [x] Submitting an email that already exists re-renders the form with
      "An account with that email already exists." instead of crashing.
- [x] App starts and serves all routes without errors.
