from datetime import date, timedelta

import pytest

from chores.forms import ChoreForm
from chores.models import Member


def _data(member, **overrides):
    data = {
        "name": "Water plants",
        "is_recurring": "",
        "recurrence_rule": "",
        "assigned_to": str(member.pk),
        "due_date": date.today().isoformat(),
    }
    data.update(overrides)
    return data


@pytest.mark.django_db
def test_valid_non_recurring_chore():
    member = Member.objects.create(name="Alex")

    form = ChoreForm(_data(member))

    assert form.is_valid()


@pytest.mark.django_db
def test_past_due_date_is_allowed():
    member = Member.objects.create(name="Alex")

    form = ChoreForm(
        _data(member, due_date=(date.today() - timedelta(days=10)).isoformat())
    )

    assert form.is_valid()


@pytest.mark.django_db
def test_recurring_without_rule_errors_on_rule():
    member = Member.objects.create(name="Alex")

    form = ChoreForm(_data(member, is_recurring="on", recurrence_rule=""))

    assert not form.is_valid()
    assert "recurrence_rule" in form.errors


@pytest.mark.django_db
def test_recurring_with_bad_rule_errors_on_rule():
    member = Member.objects.create(name="Alex")

    form = ChoreForm(_data(member, is_recurring="on", recurrence_rule="every_funday"))

    assert not form.is_valid()
    assert "recurrence_rule" in form.errors


@pytest.mark.django_db
def test_recurring_with_valid_rule_is_valid():
    member = Member.objects.create(name="Alex")

    form = ChoreForm(_data(member, is_recurring="on", recurrence_rule="every_monday"))

    assert form.is_valid()


@pytest.mark.django_db
def test_non_recurring_discards_submitted_rule():
    member = Member.objects.create(name="Alex")

    form = ChoreForm(_data(member, is_recurring="", recurrence_rule="every_monday"))

    assert form.is_valid()
    chore = form.save()
    assert chore.recurrence_rule == ""
