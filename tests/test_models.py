from datetime import date, timedelta

import pytest
from django.db import IntegrityError

from chores.models import Chore, Completion, Member


@pytest.mark.django_db
def test_member_chore_completion_relationships():
    member = Member.objects.create(name="Alex")
    chore = Chore.objects.create(
        name="Take out the trash",
        assigned_to=member,
        due_date=date.today() + timedelta(days=1),
    )
    completion = Completion.objects.create(chore=chore, completed_by=member)

    assert chore.assigned_to == member
    assert completion.chore == chore
    assert completion.completed_by == member
    assert completion.completed_at is not None


@pytest.mark.django_db
def test_duplicate_member_name_raises_integrity_error():
    Member.objects.create(name="Alex")

    with pytest.raises(IntegrityError):
        Member.objects.create(name="Alex")


@pytest.mark.django_db
def test_is_overdue_true_when_due_date_is_past_and_not_done():
    member = Member.objects.create(name="Alex")
    chore = Chore.objects.create(
        name="Dishes",
        assigned_to=member,
        due_date=date.today() - timedelta(days=1),
    )

    assert chore.is_overdue is True


@pytest.mark.django_db
def test_is_overdue_false_when_due_date_is_future():
    member = Member.objects.create(name="Alex")
    chore = Chore.objects.create(
        name="Dishes",
        assigned_to=member,
        due_date=date.today() + timedelta(days=1),
    )

    assert chore.is_overdue is False


@pytest.mark.django_db
def test_is_overdue_false_when_due_today():
    member = Member.objects.create(name="Alex")
    chore = Chore.objects.create(
        name="Dishes",
        assigned_to=member,
        due_date=date.today(),
    )

    assert chore.is_overdue is False


@pytest.mark.django_db
def test_is_overdue_false_when_done_even_if_past():
    member = Member.objects.create(name="Alex")
    chore = Chore.objects.create(
        name="Dishes",
        assigned_to=member,
        due_date=date.today() - timedelta(days=3),
        is_done=True,
    )

    assert chore.is_overdue is False


@pytest.mark.django_db
def test_complete_one_off_records_completion_and_returns_none():
    member = Member.objects.create(name="Alex")
    chore = Chore.objects.create(
        name="Dishes",
        assigned_to=member,
        due_date=date.today(),
    )

    result = chore.complete(member)

    assert result is None
    chore.refresh_from_db()
    assert chore.is_done is True
    assert chore.completions.count() == 1
    assert chore.completions.get().completed_by == member
    assert Chore.objects.count() == 1


@pytest.mark.django_db
def test_complete_recurring_spawns_next_occurrence():
    member = Member.objects.create(name="Alex")
    chore = Chore.objects.create(
        name="Water plants",
        assigned_to=member,
        due_date=date.today(),
        is_recurring=True,
        recurrence_rule="every_3_days",
    )

    new_chore = chore.complete(member)

    chore.refresh_from_db()
    assert chore.is_done is True
    assert new_chore is not None
    assert new_chore.pk != chore.pk
    assert new_chore.is_done is False
    assert new_chore.assigned_to == member
    assert new_chore.is_recurring is True
    assert new_chore.recurrence_rule == "every_3_days"
    assert new_chore.due_date == date.today() + timedelta(days=3)


@pytest.mark.django_db
def test_complete_on_done_chore_raises_and_writes_nothing():
    member = Member.objects.create(name="Alex")
    chore = Chore.objects.create(
        name="Dishes",
        assigned_to=member,
        due_date=date.today(),
        is_recurring=True,
        recurrence_rule="every_3_days",
        is_done=True,
    )

    with pytest.raises(ValueError):
        chore.complete(member)

    assert Completion.objects.count() == 0
    assert Chore.objects.count() == 1
