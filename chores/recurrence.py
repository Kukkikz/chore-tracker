"""Pure date arithmetic for recurring chores.

No database access and no clock reads: every result depends only on the
arguments passed in.
"""

import re
from datetime import date, timedelta

_WEEKDAYS = {
    "every_monday": 0,
    "every_tuesday": 1,
    "every_wednesday": 2,
    "every_thursday": 3,
    "every_friday": 4,
    "every_saturday": 5,
    "every_sunday": 6,
}

_EVERY_N_DAYS = re.compile(r"^every_(\d+)_days$")


def next_due_date(rule: str, from_date: date) -> date:
    """Return the next date a chore following ``rule`` is due after ``from_date``.

    ``every_monday`` .. ``every_sunday`` give the next occurrence of that
    weekday strictly after ``from_date`` (7 days on if ``from_date`` already
    falls on it). ``every_N_days`` with a positive integer ``N`` gives
    ``from_date + timedelta(days=N)``. Anything else raises ``ValueError``.
    """
    if not isinstance(rule, str):
        raise ValueError(f"Unrecognised recurrence rule: {rule!r}")

    if rule in _WEEKDAYS:
        target = _WEEKDAYS[rule]
        ahead = (target - from_date.weekday()) % 7
        if ahead == 0:
            ahead = 7
        return from_date + timedelta(days=ahead)

    match = _EVERY_N_DAYS.match(rule)
    if match is not None:
        days = int(match.group(1))
        if days > 0:
            return from_date + timedelta(days=days)

    raise ValueError(f"Unrecognised recurrence rule: {rule!r}")
