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
