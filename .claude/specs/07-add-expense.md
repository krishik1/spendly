# Spec: Add Expense

## Overview
Add Expense replaces the `/expenses/add` placeholder (`"Add expense — coming
in Step 7"`) with a real form that lets a logged-in user record a new
expense against their own account. Until now the only expenses in the
database are the seeded demo rows — every user, including newly registered
ones, has had no way to add their own data, so Profile (Steps 4–6) always
displays either the seed data or an empty state. This step makes the
`expenses` table genuinely writable by end users for the first time, and
sets up the pattern (form → validate → insert → redirect to `/profile`)
that Edit Expense (Step 8) and Delete Expense (Step 9) will follow.

## Depends on
- Step 1 (database setup) — the `expenses` table and `get_db()`.
- Step 3 (login/logout) — `session["user_id"]` identifies whose expense is
  being created.
- Step 4–6 (profile page) — the page the user lands on after adding an
  expense, and the page a new "Add expense" entry point is placed on.

## Routes
- `GET /expenses/add` — render the add-expense form — logged-in (redirect
  to `/login` if not authenticated)
- `POST /expenses/add` — validate the submitted fields, insert a new row
  into `expenses` for `session["user_id"]`, flash a success message, and
  redirect to `/profile` — logged-in (redirect to `/login` if not
  authenticated)

## Database changes
No database changes. Uses the existing `expenses` table as defined in
`database/db.py` (`user_id`, `amount`, `category`, `date`, `description`,
`created_at`). `category` is not constrained by the schema, so validity is
enforced in the route against the fixed list already used elsewhere in the
app: Food, Transport, Bills, Health, Entertainment, Shopping, Other.

## Templates
- **Create:** `templates/add_expense.html` — form extending `base.html`
  with fields:
  - `amount` — `type="number"`, `step="0.01"`, `min="0.01"`, required
  - `category` — `<select>` populated from the fixed 7-category list,
    required
  - `date` — `type="date"`, required, defaults to today via the `value`
    attribute
  - `description` — optional free text
  - a submit button and a "Cancel" link back to `/profile`
  - an `{% if error %}` block to re-render the form with a validation
    message, matching the pattern in `register.html` / `login.html`
- **Modify:** `templates/profile.html` — add an "Add expense" link/button
  (e.g. near the "Recent transactions" section heading) pointing to
  `{{ url_for('add_expense') }}`, so the feature is reachable from the UI.

## Files to change
- `expense-tracker/app.py` — replace the `add_expense` stub with `GET`/
  `POST` handling: auth guard, form rendering, validation, parameterised
  `INSERT`, flash message, redirect.
- `expense-tracker/templates/profile.html` — add the "Add expense" entry
  point described above.
- `expense-tracker/static/css/style.css` — add layout/styling rules for
  the add-expense form (container, field spacing) reusing the existing
  `.form-group` / `.form-input` / `.btn-submit` / `.btn-ghost` classes and
  CSS variables already used by `register.html` and `profile.html`; add
  new classes only for layout not already covered (e.g. a form section
  wrapper), using CSS variables for any colour.

## Files to create
- `expense-tracker/templates/add_expense.html`

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs.
- Parameterised queries only.
- Passwords hashed with werkzeug (no auth changes in this step).
- Use CSS variables — never hardcode hex values.
- All templates extend `base.html`.
- No inline styles.
- Authentication guard: check `session.get("user_id")` on both `GET` and
  `POST`; if absent, `redirect(url_for("login"))`.
- `amount` must parse as a positive number (> 0); reject non-numeric or
  zero/negative values with an inline error, re-rendering the form with
  the values the user already entered (except do not require re-typing on
  error — repopulate the fields from `request.form`).
- `category` must be one of the fixed 7 values (Food, Transport, Bills,
  Health, Entertainment, Shopping, Other); reject anything else.
- `date` must parse with `date.fromisoformat`; reject unparseable values.
  Do not reject future dates (users may log planned or same-day expenses).
- `description` is optional; store `None`/empty as-is, do not require it.
- The inserted `user_id` must always come from `session["user_id"]`, never
  from form input, so a user can only create expenses for themselves.
- On successful insert, flash a success message (e.g. "Expense added.")
  and redirect to `/profile` — do not redirect back to the same filtered
  query string.

## Definition of done
- [ ] Visiting `/expenses/add` while logged out redirects to `/login`.
- [ ] Visiting `/expenses/add` while logged in returns HTTP 200 with a form
      containing amount, category, date, and description fields.
- [ ] Submitting a valid amount, category, date, and description creates a
      new row in `expenses` with the logged-in user's `user_id`, flashes a
      success message, and redirects to `/profile`.
- [ ] The newly added expense appears in the profile page's transaction
      list and is reflected in the summary stats and category breakdown.
- [ ] Submitting a blank amount, a non-numeric amount, or an amount ≤ 0
      re-renders the form with a validation error (no crash, no insert).
- [ ] Submitting a category outside the fixed 7-category list re-renders
      the form with a validation error (no crash, no insert).
- [ ] Submitting an unparseable date re-renders the form with a validation
      error (no crash, no insert).
- [ ] Submitting with description left blank succeeds (description is
      optional).
- [ ] The profile page has a visible "Add expense" link that navigates to
      `/expenses/add`.
- [ ] App starts and all existing routes still respond without errors.
