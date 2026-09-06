# Chore Tracker — Backlog

The backlog now lives in GitHub issues:
https://github.com/Kukkikz/chore-tracker/issues

| # | Task |
|---|------|
| 1 | Scaffold the Django project with a passing test |
| 2 | Define the Member, Chore, and Completion models |
| 3 | Add the recurrence date helper |
| 4 | Add Chore.is_overdue and Chore.complete() |
| 5 | Register models in the Django admin |
| 6 | "Who are you?" member picker stored in session |
| 7 | Chore list page with overdue flagging |
| 8 | Create a chore |
| 9 | Reassign a chore |
| 10 | Mark a chore done |
| 11 | Completion history page |
| 12 | Seed data management command |
| 13 | Project README |

Shared context for every task: this is a Django + server-rendered templates +
SQLite app for tracking shared chores in a single household with no login. See
`_docs/plan.md` for the spec and stack decision and `_docs/data_model.md` for the
model definitions. App code lives in a single Django app called `chores`; the
project package is `chore_tracker`. Environment and dependencies are managed with
`venv` + `uv`, dependencies declared in `pyproject.toml` (runtime: `Django`; dev:
`pytest`, `pytest-django`). Run tests with `uv run pytest`.
