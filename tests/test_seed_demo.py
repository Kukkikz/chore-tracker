import pytest
from django.core.management import call_command

from chores.models import Chore, Completion, Member


@pytest.mark.django_db
def test_seed_demo_creates_believable_household():
    call_command("seed_demo")

    assert Member.objects.exists()
    assert any(chore.is_overdue for chore in Chore.objects.all())
    assert Chore.objects.filter(is_recurring=True).exists()
    assert Completion.objects.exists()


@pytest.mark.django_db
def test_seed_demo_is_idempotent():
    call_command("seed_demo")
    counts = (Member.objects.count(), Chore.objects.count(), Completion.objects.count())

    call_command("seed_demo")

    assert (
        Member.objects.count(),
        Chore.objects.count(),
        Completion.objects.count(),
    ) == counts
