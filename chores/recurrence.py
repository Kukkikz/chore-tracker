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


def is_valid_rule(rule: str) -> bool:
    """Return whether ``rule`` is an accepted recurrence rule.

    The single source of truth for the rule vocabulary: ``every_monday`` ..
    ``every_sunday`` and ``every_N_days`` with ``N`` a positive integer.
    """
    if not isinstance(rule, str):
        return False
    if rule in _WEEKDAYS:
        return True
    match = _EVERY_N_DAYS.match(rule)
    return match is not None and int(match.group(1)) > 0


def next_due_date(rule: str, from_date: date) -> date:
    """Return the next date a chore following ``rule`` is due after ``from_date``.

    ``every_monday`` .. ``every_sunday`` give the next occurrence of that
    weekday strictly after ``from_date`` (7 days on if ``from_date`` already
    falls on it). ``every_N_days`` with a positive integer ``N`` gives
    ``from_date + timedelta(days=N)``. Anything else raises ``ValueError``.
    """
    if not is_valid_rule(rule):
        raise ValueError(f"Unrecognised recurrence rule: {rule!r}")

    if rule in _WEEKDAYS:
        target = _WEEKDAYS[rule]
        ahead = (target - from_date.weekday()) % 7
        if ahead == 0:
            ahead = 7
        return from_date + timedelta(days=ahead)

    days = int(_EVERY_N_DAYS.match(rule).group(1))
    return from_date + timedelta(days=days)
