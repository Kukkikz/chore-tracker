# Chore Tracker

A shared chore tracker for a single household. It is a Django app with
server-rendered templates and a SQLite database. There is no login: you pick
your name from a member picker, and that choice is remembered in your session.

## Features

- Household members and chores, managed through the Django admin.
- One-off chores and recurring chores (e.g. every Monday, every 3 days).
- Manual assignment and reassignment of any chore to any member.
- Mark a chore done, which records who completed it and when.
- Completion history page showing past completions.
- Undo a completion.
- Automatic creation of the next occurrence when a recurring chore is completed.
- Due dates, with chores past their due date flagged as overdue (derived, never stored).
- Edit and delete chores.
- Django admin for creating members and initial chores.

## Setup

Run these in order from the repo root:

```
python -m venv .venv
.venv\Scripts\activate            # Windows
source .venv/bin/activate         # macOS / Linux
uv sync
uv run python manage.py migrate
uv run python manage.py createsuperuser
uv run python manage.py seed_demo
uv run python manage.py runserver
```

Then open http://127.0.0.1:8000/.

Notes:

- The Django admin at `/admin/` is how members and initial chores are created.
  Log in with the superuser you just created.
- `seed_demo` is optional and loads demo data. It is DESTRUCTIVE: it deletes every
  existing Completion, Chore, and Member before reseeding (see issue #12). Skip it
  if you have real data.

## Running tests

```
uv run pytest                       # the whole suite
uv run pytest tests/test_models.py  # one test file
```

Tests run with `pytest` (via `pytest-django`). `manage.py test` is not used.

## Project layout

- `chore_tracker/` - the Django project package (settings, URLs, WSGI).
- `chores/` - the single application (models, views, templates, admin).
- `tests/` - the test suite.

## Documentation

See `_docs/`:

- `plan.md` - product spec and tech-stack decision.
- `data_model.md` - models, fields, and key logic (overdue, completion, recurrence).
- `process.md` - how work is organized.
- `task-template.md` - the template for a groomed task.
- `testing-guidelines.md` - how to write tests for this project.
- `design-system.md` - UI and styling conventions.
- `team/` - role descriptions (PM, software engineer, QA engineer).
