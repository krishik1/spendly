# Spec: Login and Logout

## Overview
Login and Logout give a registered Spendly user a way to authenticate and
end their session. Registration (Step 2) can create `users` rows, but
nothing yet turns a submitted email/password into a signed-in session —
`/login` only renders a form with no handler behind it, and `/logout` is a
placeholder string. This step wires both up using Flask's built-in
`session`, so the app has a real notion of "who is logged in" for the first
time. That notion is what Profile (Step 4) and every expense route after it
will depend on.

## Depends on
- Step 1 (database setup) — the `users` table and `get_db()`.
- Step 2 (registration) — `users` rows with hashed passwords to log into.

## Routes
- `GET /login` — render the sign-in form — public (already implemented,
  unchanged)
- `POST /login` — verify email/password against `users`, start a session,
  flash a "welcome back" success message, and redirect to `/` (landing) on
  success — public
- `GET /logout` — clear the session, redirect to `/login` — logged-in
  (safe to call when logged out too; simply redirects)

## Database changes
No database changes. Uses the existing `users` table
(`database/db.py:20-27`) as-is — `email` to look up the row,
`password_hash` to verify with `werkzeug.security.check_password_hash`.

## Templates
- **Create:** none.
- **Modify:**
  - `templates/login.html` — no structural change; already posts `email`/
    `password` to `/login` and has an `{% if error %}` block that the new
    handler will populate on failure.
  - `templates/base.html` — the nav (`nav-links`, lines ~21-24) currently
    always shows "Sign in" / "Get started" regardless of auth state. Add a
    session-aware branch: when `session.get('user_id')` is set, show a
    "Sign out" link (`{{ url_for('logout') }}`) instead, so logout is
    reachable from the UI after logging in. Also render Flask's
    `get_flashed_messages()` inside `<main>` so the login success message
    is visible on whichever page it's flashed to.

## Files to change
- `expense-tracker/app.py`:
  - Set `app.secret_key` (required for Flask sessions to work; read from
    an environment variable with a hardcoded dev fallback, since this is a
    learning project with no `.env` handling yet).
  - Add `POST` handling to the existing `/login` route.
  - Implement `/logout` to clear the session (`session.clear()`) and
    redirect to `/login`, replacing the placeholder string.
- `expense-tracker/templates/base.html` — conditional nav block and flashed
  message rendering described above.
- `expense-tracker/static/css/style.css` — `.flash-container`/`.flash-message`/
  `.flash-success` rules for the success banner, using existing CSS
  variables only.

## Files to create
None.

## New dependencies
No new dependencies. Uses Flask's built-in `session` and the existing
`werkzeug.security` (`check_password_hash`, already installed as a Flask
dependency; `generate_password_hash` is already imported in `app.py`).

## Rules for implementation
- No SQLAlchemy or ORMs.
- Parameterised queries only.
- Passwords hashed with werkzeug — verify with `check_password_hash`,
  never compare plaintext.
- Use CSS variables — never hardcode hex values.
- All templates extend `base.html`.
- On login failure (unknown email OR wrong password), show the **same**
  generic error message ("Invalid email or password.") for both cases —
  don't reveal whether the email exists.
- Store only `user_id` (and optionally `name`) in the session — never the
  password or password hash.

## Definition of done
- [ ] Submitting the login form with a valid email + correct password
      (e.g. the seeded `demo@spendly.com` / `demo123`) redirects to the
      landing page, starts a session, and shows a "Welcome back" success
      message.
- [ ] Submitting with a correct email but wrong password re-renders
      `login.html` with "Invalid email or password." (no crash).
- [ ] Submitting with an email that doesn't exist shows the same
      "Invalid email or password." message, not a different one.
- [ ] After a successful login, the nav in `base.html` shows "Sign out"
      instead of "Sign in" / "Get started" on subsequent page loads.
- [ ] Visiting `/logout` clears the session and redirects to `/login`;
      the nav reverts to the logged-out state afterward.
- [ ] Reloading any page after login keeps the user logged in (session
      persists across requests without resubmitting the form).
- [ ] App starts and all existing routes still respond without errors.
