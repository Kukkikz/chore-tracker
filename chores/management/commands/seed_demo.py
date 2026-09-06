from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.db import transaction

from chores.models import Chore, Completion, Member
from chores.recurrence import next_due_date

MEMBER_NAMES = ["Alex", "Bailey", "Casey", "Devon"]


class Command(BaseCommand):
    help = (
        "Populate the database with demo household data. DESTRUCTIVE: deletes "
        "every existing Completion, Chore and Member before recreating a fixed "
        "set of members and chores with due dates relative to today."
    )

    def handle(self, *args, **options):
        self.stdout.write(
            "WARNING: deleting all Completion, Chore and Member rows, then reseeding."
        )

        today = date.today()

        with transaction.atomic():
            Completion.objects.all().delete()
            Chore.objects.all().delete()
            Member.objects.all().delete()

            members = [Member.objects.create(name=name) for name in MEMBER_NAMES]

            weekday_rule = "every_monday"
            interval_rule = "every_3_days"

            specs = [
                dict(name="Take out the trash", assigned_to=members[0],
                     due_date=today - timedelta(days=2), is_done=False),
                dict(name="Water the plants", assigned_to=members[1],
                     due_date=today - timedelta(days=5), is_done=False),
                dict(name="Empty the dishwasher", assigned_to=members[2],
                     due_date=today, is_done=False),
                dict(name="Buy groceries", assigned_to=members[3],
                     due_date=today + timedelta(days=3), is_done=False),
                dict(name="Clean the bathroom", assigned_to=members[0],
                     due_date=today + timedelta(days=7), is_done=False),
                dict(name="Vacuum living room", assigned_to=members[1],
                     due_date=next_due_date(weekday_rule, today), is_done=False,
                     is_recurring=True, recurrence_rule=weekday_rule),
                dict(name="Wipe kitchen counters", assigned_to=members[2],
                     due_date=next_due_date(interval_rule, today), is_done=False,
                     is_recurring=True, recurrence_rule=interval_rule),
                dict(name="Mow the lawn", assigned_to=members[3],
                     due_date=today - timedelta(days=1), is_done=True),
            ]

            chores = [Chore.objects.create(**spec) for spec in specs]

            done_chore = chores[-1]
            Completion.objects.create(
                chore=done_chore, completed_by=done_chore.assigned_to
            )

        self.stdout.write(
            "Seeded {members} members, {chores} chores, {completions} completions.".format(
                members=Member.objects.count(),
                chores=Chore.objects.count(),
                completions=Completion.objects.count(),
            )
        )
