from datetime import date

import pytest

from chores.recurrence import next_due_date


def test_weekday_midweek_returns_next_occurrence():
    # 2026-09-06 is a Sunday.
    result = next_due_date("every_wednesday", date(2026, 9, 6))

    assert result == date(2026, 9, 9)


def test_weekday_on_same_weekday_returns_seven_days_later():
    # 2026-09-07 is a Monday.
    result = next_due_date("every_monday", date(2026, 9, 7))

    assert result == date(2026, 9, 14)


def test_every_n_days_adds_n_days():
    result = next_due_date("every_3_days", date(2026, 9, 6))

    assert result == date(2026, 9, 9)


def test_every_1_days_returns_next_calendar_day():
    result = next_due_date("every_1_days", date(2026, 9, 6))

    assert result == date(2026, 9, 7)


def test_unknown_keyword_raises_value_error_naming_rule():
    with pytest.raises(ValueError, match="every_funday"):
        next_due_date("every_funday", date(2026, 9, 6))


def test_every_zero_days_raises_value_error():
    with pytest.raises(ValueError, match="every_0_days"):
        next_due_date("every_0_days", date(2026, 9, 6))


def test_negative_days_raises_value_error():
    with pytest.raises(ValueError, match="every_-2_days"):
        next_due_date("every_-2_days", date(2026, 9, 6))


def test_empty_string_raises_value_error():
    with pytest.raises(ValueError):
        next_due_date("", date(2026, 9, 6))


def test_non_string_rule_raises_value_error():
    with pytest.raises(ValueError):
        next_due_date(None, date(2026, 9, 6))
