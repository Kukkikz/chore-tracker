from django.db import models


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
