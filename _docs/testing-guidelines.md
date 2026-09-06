# Testing Guidelines

## Tools

- `pytest` with `pytest-django` is the only test runner. Do not use
  `manage.py test` or `unittest.TestCase`.
- Config lives in `pyproject.toml` under `[tool.pytest.ini_options]` with
  `DJANGO_SETTINGS_MODULE = "chore_tracker.settings"`.
- Run the suite with `uv run pytest`; a single file with
  `uv run pytest tests/test_home.py`.

## Layout

- Tests live in a top-level `tests/` directory, one file per unit under test
  (`tests/test_models.py`, `tests/test_recurrence.py`, `tests/test_views.py`).
- Name tests `test_<behaviour>` — describe the expected behaviour, not the method.

## What to test

- Every new behaviour ships with a test in the same change.
- Pure logic (e.g. `next_due_date`) gets a plain unit test with **no database** —
  no `@pytest.mark.django_db`, no fixtures.
- Anything touching the ORM uses `@pytest.mark.django_db`.
- Model methods (`Chore.complete()`, `Chore.is_overdue`) are tested at the model
  level, not through a view.
- Views get one test per path: the happy path plus each redirect/guard
  (no member selected, chore already done, invalid form).

## Style

- Arrange–act–assert, with a blank line between the three parts.
- Prefer factory helpers or plain `Model.objects.create(...)` over fixtures for
  a project this small.
- Freeze "today" explicitly when a test depends on the current date — pass an
  explicit `due_date` relative to `date.today()` rather than hard-coding a date.
- One logical assertion per test where practical; a test that needs a paragraph
  of setup is a hint the code under test is doing too much.
