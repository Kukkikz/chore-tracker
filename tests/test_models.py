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


@pytest.mark.django_db
def test_undo_one_off_clears_is_done_and_removes_row():
    member = Member.objects.create(name="Alex")
    chore = Chore.objects.create(
        name="Dishes", assigned_to=member, due_date=date.today()
    )
    chore.complete(member)
    completion = Completion.objects.get()

    completion.undo()

    chore.refresh_from_db()
    assert chore.is_done is False
    assert Completion.objects.count() == 0


@pytest.mark.django_db
def test_undo_recurring_removes_clean_spawned_chore():
    member = Member.objects.create(name="Alex")
    chore = Chore.objects.create(
        name="Water plants",
        assigned_to=member,
        due_date=date.today(),
        is_recurring=True,
        recurrence_rule="every_3_days",
    )
    spawned = chore.complete(member)
    completion = chore.completions.get()

    completion.undo()

    chore.refresh_from_db()
    assert chore.is_done is False
    assert not Chore.objects.filter(pk=spawned.pk).exists()
    assert Completion.objects.count() == 0


@pytest.mark.django_db
def test_undo_refused_when_spawned_chore_is_done():
    member = Member.objects.create(name="Alex")
    chore = Chore.objects.create(
        name="Water plants",
        assigned_to=member,
        due_date=date.today(),
        is_recurring=True,
        recurrence_rule="every_3_days",
    )
    spawned = chore.complete(member)
    spawned.complete(member)
    completion = chore.completions.get()

    assert completion.is_undoable is False
    with pytest.raises(ValueError):
        completion.undo()

    chore.refresh_from_db()
    assert chore.is_done is True
    assert Chore.objects.filter(pk=spawned.pk).exists()
    assert Completion.objects.filter(pk=completion.pk).exists()


@pytest.mark.django_db
def test_undo_refused_when_spawned_chore_has_its_own_completion():
    member = Member.objects.create(name="Alex")
    chore = Chore.objects.create(
        name="Water plants",
        assigned_to=member,
        due_date=date.today(),
        is_recurring=True,
        recurrence_rule="every_3_days",
    )
    spawned = chore.complete(member)
    Completion.objects.create(chore=spawned, completed_by=member)
    completion = chore.completions.get()

    assert completion.is_undoable is False
    with pytest.raises(ValueError):
        completion.undo()

    assert Completion.objects.filter(pk=completion.pk).exists()
    assert Chore.objects.filter(pk=spawned.pk).exists()


@pytest.mark.django_db
def test_only_the_latest_completion_of_a_chore_is_undoable():
    member = Member.objects.create(name="Alex")
    chore = Chore.objects.create(
        name="Dishes", assigned_to=member, due_date=date.today()
    )
    old = Completion.objects.create(chore=chore, completed_by=member)
    new = Completion.objects.create(chore=chore, completed_by=member)

    assert old.is_undoable is False
    assert new.is_undoable is True
    with pytest.raises(ValueError):
        old.undo()


@pytest.mark.django_db
def test_undo_recurring_without_valid_rule_behaves_like_one_off():
    member = Member.objects.create(name="Alex")
    chore = Chore.objects.create(
        name="Water plants",
        assigned_to=member,
        due_date=date.today(),
        is_recurring=True,
        recurrence_rule="every_3_days",
    )
    chore.complete(member)
    Chore.objects.filter(pk=chore.pk).update(recurrence_rule="")
    completion = Completion.objects.get()

    completion.undo()

    assert Completion.objects.count() == 0
