from datetime import date

from django.db import models, transaction

from chores.recurrence import next_due_date


class Member(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Chore(models.Model):
    name = models.CharField(max_length=200)
    is_recurring = models.BooleanField(default=False)
    recurrence_rule = models.CharField(max_length=50, null=True, blank=True)
    assigned_to = models.ForeignKey(
        Member,
        on_delete=models.PROTECT,
        related_name="chores",
    )
    due_date = models.DateField()
    is_done = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    @property
    def is_overdue(self):
        return self.is_done is False and self.due_date < date.today()

    def complete(self, member):
        if self.is_done:
            raise ValueError("Chore is already done")

        with transaction.atomic():
            Completion.objects.create(chore=self, completed_by=member)
            self.is_done = True
            self.save()

            if not self.is_recurring:
                return None

            return Chore.objects.create(
                name=self.name,
                assigned_to=self.assigned_to,
                is_recurring=True,
                recurrence_rule=self.recurrence_rule,
                is_done=False,
                due_date=next_due_date(self.recurrence_rule, self.due_date),
            )


class Completion(models.Model):
    chore = models.ForeignKey(
        Chore,
        on_delete=models.CASCADE,
        related_name="completions",
    )
    completed_by = models.ForeignKey(
        Member,
        on_delete=models.PROTECT,
        related_name="completions",
    )
    completed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.chore} completed by {self.completed_by}"
