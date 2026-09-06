Commands

- `uv sync` - install dependencies
- `uv run pytest` - the whole suite
- `uv run pytest tests/test_home.py` - one test file

Rules

- Dependencies are added in `pyproject.toml`. Do not add one without asking

Coding standards

- Keep changes small and surgical; match the style of the surrounding code.
- Business logic lives on models or plain helper functions, not in views or templates.
- Views stay thin: parse the request, call into a model/helper, render or redirect.
- Prefer Django's built-ins (ORM, forms, `get_object_or_404`, messages) over hand-rolled equivalents.
- Never store computed state (e.g. overdue) — derive it where it is needed.
- All state-changing actions are POST and CSRF-protected; GET stays side-effect free.
- Name things for the domain: `Member`, `Chore`, `Completion`, `is_overdue`, `next_due_date`.
- Every new behaviour ships with a test; pure logic gets a unit test with no database.
- Run `uv run pytest` before considering a task done.
- 4-space indent, one statement per line, no wildcard imports; let the formatter settle whitespace.

Documents

- `_docs/process.md` - how work is organized
- Before writing tests, read `_docs/testing-guidelines.md`
- For anything touching the UI, read `_docs/design-system.md`