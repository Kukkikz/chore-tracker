# Chore Tracker — Backlog

Context for every task: this is a Django + server-rendered templates + SQLite app
for tracking shared chores in a single household with no login. See
`_docs/plan.md` for the spec and stack decision and `_docs/data_model.md` for the
model definitions. App code lives in a single Django app called `chores`; the
project package is `chore_tracker`. Only dependency is `Django`. Run tests with
`python manage.py test`.

## 1. Scaffold the Django project with a passing test
Goal: An empty but runnable Django project with one trivial test that passes.
Description: Create a virtualenv and `requirements.txt` pinning `Django`, run
`django-admin startproject chore_tracker .` and `python manage.py startapp
chores`, and register `chores` in `INSTALLED_APPS`. Add a single smoke test (e.g.
asserting `1 + 1 == 2` or that the home URL is reachable) and confirm
`python manage.py test` and `python manage.py runserver` both work. Update
`.gitignore` if needed.

## 2. Define the Member, Chore, and Completion models
Goal: The three models from `data_model.md` exist with a generated migration.
Description: In `chores/models.py` create `Member` (unique `name`), `Chore`
(`name`, `is_recurring`, `recurrence_rule` nullable, `assigned_to` FK to Member,
`due_date`, `is_done` default False), and `Completion` (`chore` FK, `completed_by`
FK to Member, `completed_at` auto_now_add). Add `__str__` methods and run
`makemigrations`. Write model tests that create one of each and assert the FK
relationships work.

## 3. Add the recurrence date helper
Goal: A pure function that computes the next due date from a recurrence rule.
Description: Add `next_due_date(rule: str, from_date: date) -> date` (in
`chores/recurrence.py`) supporting `every_monday`..`every_sunday` (next occurrence
of that weekday strictly after `from_date`) and `every_N_days` (from_date plus N
days). Raise `ValueError` on an unrecognised rule. Cover each rule shape and the
error case with unit tests; no database needed.

## 4. Add Chore.is_overdue and Chore.complete()
Goal: Model-level behaviour for completing chores and flagging overdue ones.
Description: Add an `is_overdue` property to `Chore` (`not is_done and due_date <
today`). Add `complete(member)` which creates a `Completion`, sets
`is_done=True`, and — if `is_recurring` — creates a new `Chore` row copying name
/ rule / assignee with `due_date = next_due_date(recurrence_rule, self.due_date)`
and `is_done=False`. Depends on the models (task 2) and the recurrence helper
(task 3). Test both the one-off and recurring paths.

## 5. Register models in the Django admin
Goal: All three models are manageable through `/admin`.
Description: In `chores/admin.py` register `Member`, `Chore`, and `Completion`
with sensible `list_display`, `list_filter`, and `search_fields` (e.g. Chore
shows name, assigned_to, due_date, is_done). Add a `createsuperuser` note to the
README. This is how members and initial chores get seeded for v1.

## 6. "Who are you?" member picker stored in session
Goal: A visitor picks their name from the member list; it persists in the session.
Description: Add a view + template listing all `Member` names as buttons/links;
selecting one stores `member_id` in `request.session`. Add a small helper
(e.g. `get_current_member(request)`) and a header partial showing the current
name with a "switch" link. Redirect to the picker when no member is selected.
Depends on the Member model (task 2).

## 7. Chore list page with overdue flagging
Goal: The main page lists chores, visually flagging overdue ones.
Description: Add the root view/template rendering all chores that are not done,
sorted by due date, showing name, assignee, and due date. Rows where
`is_overdue` is true get an "overdue" CSS class / badge. Include Pico.css via CDN
and a small `chores/static/chores/style.css` for the overdue styling. Depends on
the models (task 2) and `is_overdue` (task 4).

## 8. Create a chore
Goal: A form to add a new chore.
Description: Add a Django `ModelForm` for `Chore` (name, is_recurring,
recurrence_rule, assigned_to, due_date) plus a view and template, linked from the
chore list. On success redirect back to the list. Validate that
`recurrence_rule` is present when `is_recurring` is checked. Depends on the
models (task 2).

## 9. Reassign a chore
Goal: Change which member a not-yet-done chore is assigned to.
Description: Add a POST endpoint / small form on each chore row (or a detail page)
that updates `Chore.assigned_to` to another member, allowed only while
`is_done=False`. Redirect back to the list. Depends on the models (task 2) and
the chore list (task 7).

## 10. Mark a chore done
Goal: Completing a chore from the UI logs history and spawns recurrences.
Description: Add a POST endpoint on each chore row that calls
`chore.complete(current_member)` using the session member, then redirects to the
list with a confirmation message. Handle the no-member-selected case by
redirecting to the picker. Depends on `Chore.complete()` (task 4) and the member
session helper (task 6).

## 11. Completion history page
Goal: A page showing who completed what and when.
Description: Add a view/template listing `Completion` records newest first,
showing chore name, `completed_by`, and `completed_at`, linked from the main
nav. Optionally allow filtering by member. Depends on the models (task 2).

## 12. Seed data management command
Goal: One command populates a realistic set of members and chores for demoing.
Description: Add `chores/management/commands/seed_demo.py` implementing a
`seed_demo` command that creates a few members and a mix of one-off and recurring
chores with varied due dates (some overdue). Make it idempotent or clearly
destructive-and-recreate. Depends on the models (task 2).

## 13. Project README
Goal: A README that lets a newcomer run the app and tests.
Description: Write `README.md` covering setup (virtualenv, `pip install -r
requirements.txt`, `migrate`, `createsuperuser`, `seed_demo`, `runserver`), how
to run tests, the feature list, and a pointer to `_docs/`. Independent of the
code tasks beyond referencing commands they establish.
