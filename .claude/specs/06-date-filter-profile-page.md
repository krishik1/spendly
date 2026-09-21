# Spec: Date Filter for Profile Page

## Overview
Step 6 adds a date-range filter to the `/profile` page. Today the summary
stats, transaction list and category breakdown always cover every expense the
user has ever recorded. This step lets a logged-in user narrow all three
sections to a chosen period using a "From" and "To" date, submitted as query
parameters, plus a "Clear" link to reset. Because the filter is applied in one
place and shared by all three sections, the numbers on the page always agree
with each other.

## Depends on
- Step 1: Database setup (`expenses.date` stored as ISO `YYYY-MM-DD` text)
- Step 3: Login / Logout (`session["user_id"]`)
- Step 4: Profile page static UI
- Step 5: Profile page backend routes (`_get_profile_stats`,
  `_get_profile_transactions`, `_get_profile_categories` in `app.py`)

## Routes
No new routes. The existing `GET /profile` route accepts two optional query
parameters:
- `GET /profile?date_from=YYYY-MM-DD&date_to=YYYY-MM-DD` — profile page
  filtered to expenses whose `date` is between the two dates, inclusive —
  logged-in

Either parameter may be omitted (open-ended range). With neither, behaviour is
unchanged from Step 5.

## Database changes
No database changes. `expenses.date` is already `TEXT` in ISO format, so
`date >= ?` / `date <= ?` comparisons work correctly as string comparisons.

## Templates
- **Create:** none
- **Modify:** `templates/profile.html`
  - Add a `GET` filter form (no JS required) above the stats row with two
    `<input type="date">` fields (`date_from`, `date_to`), an "Apply" button and
    a "Clear" link to `url_for('profile')`.
  - Pre-fill the inputs with the currently applied values.
  - Show an inline error message when the submitted range is invalid.
  - Show an "No expenses in this period" row/message when a filter matches
    nothing.
  - Section title "Recent transactions" should read "Transactions" when a
    filter is active.

## Files to change
- `app.py` — read/validate `date_from` / `date_to` in `profile()`; pass the
  range into the three `_get_profile_*` helpers, which append the date
  conditions to their `WHERE` clause
- `templates/profile.html` — filter form, error and empty states
- `static/css/style.css` — styles for the filter form using existing CSS
  variables

## Files to create
- `tests/test_date_filter.py` — pytest tests for the filter

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs — raw `sqlite3` only via `get_db()`
- Parameterised queries only — build the optional `AND date >= ?` /
  `AND date <= ?` fragments from fixed strings and pass values as parameters;
  never format user input into SQL
- Passwords hashed with werkzeug (no auth changes in this step)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- No inline styles
- Currency must always display as ₹
- Validate both parameters with `date.fromisoformat`; an unparseable value is
  treated as an error, not passed to SQL
- If `date_from` is later than `date_to`, show the error "Start date must be
  on or before end date." and fall back to the unfiltered data (HTTP 200)
- Empty-string parameters (form submitted with a blank field) count as "not
  provided"
- Keep the frontend framework-free: plain Jinja and vanilla CSS; no JS needed
- The filter must be scoped to `session["user_id"]` exactly as before — a date
  filter must never expose another user's expenses
- Unauthenticated requests still redirect to `/login`, with or without
  query parameters
- Refactor the three helpers minimally; do not move them into a new module

## Definition of done
- [ ] `/profile` with no query string looks and behaves exactly as in Step 5
- [ ] Setting only "From" shows expenses on or after that date; setting only
      "To" shows expenses on or before that date
- [ ] Setting both shows only expenses inside the range, boundary dates included
- [ ] Total spent, transaction count, top category, transaction list and
      category breakdown all reflect the same filtered set
- [ ] Category percentages in a filtered view still add up to 100 %
- [ ] The date inputs stay pre-filled with the applied range after submitting
- [ ] "Clear" returns to the unfiltered profile
- [ ] A range with no matching expenses shows ₹0.00, 0 transactions, an empty
      breakdown and a "No expenses in this period" message, with no errors
- [ ] `date_from` later than `date_to` shows the validation error and the
      unfiltered data
- [ ] `?date_from=not-a-date` does not crash (no 500) and shows an error
- [ ] `?date_from=2026-01-01' OR '1'='1` returns normally and leaks no other
      user's data
- [ ] Visiting `/profile?date_from=2026-01-01` while logged out redirects to
      `/login`
- [ ] All amounts still display the ₹ symbol
