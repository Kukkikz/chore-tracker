from datetime import date

from django.db import models, transaction
from django.db.models import Max

from chores.recurrence import is_valid_rule, next_due_date


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

    @staticmethod
    def latest_completion_pks():
        """Return the pk of the most recent Completion for every chore.

        Completions are only ever created (never reordered), so the highest
        pk per chore is its latest completion.
        """
        return {
            row["mx"]
            for row in Completion.objects.values("chore_id").annotate(mx=Max("pk"))
        }

    @property
    def _is_latest_for_chore(self):
        latest = self.chore.completions.order_by("-pk").first()
        return latest is not None and latest.pk == self.pk

    def _spawned_next_chore(self):
        """Best-effort match for the occurrence this completion spawned.

        ``Chore`` has no FK back to the ``Completion`` that created it, so we
        match on the fields ``Chore.complete()`` copies onto the new row: same
        name and recurrence rule, still recurring, due on
        ``next_due_date(rule, original.due_date)``, and created after the
        original (proxied by a higher pk, since ids increment). The earliest
        such candidate wins. Returns ``None`` when the chore was not recurring
        or its rule is no longer valid (rule since removed -> nothing spawned).

        ``is_done`` / own-completion state is deliberately *not* filtered here
        so that :meth:`is_undoable` can still see a spawned occurrence that has
        already been worked on and refuse the undo.
        """
        chore = self.chore
        if not chore.is_recurring or not is_valid_rule(chore.recurrence_rule or ""):
            return None

        due = next_due_date(chore.recurrence_rule, chore.due_date)
        return (
            Chore.objects.filter(
                name=chore.name,
                recurrence_rule=chore.recurrence_rule,
                is_recurring=True,
                due_date=due,
                pk__gt=chore.pk,
            )
            .order_by("pk")
            .first()
        )

    @property
    def is_undoable(self):
        """True iff this is the latest Completion for its chore and any
        occurrence it spawned is still clean (not done, no Completion)."""
        if not self._is_latest_for_chore:
            return False

        spawned = self._spawned_next_chore()
        if spawned is not None and (spawned.is_done or spawned.completions.exists()):
            return False
        return True

    def undo(self):
        """Reverse this completion: raise ``ValueError`` unless undoable, else
        drop any clean spawned occurrence, mark the chore not-done, and delete
        this row -- all inside one transaction."""
        if not self.is_undoable:
            raise ValueError("This completion cannot be undone")

        with transaction.atomic():
            spawned = self._spawned_next_chore()
            if spawned is not None:
                spawned.delete()

            self.chore.is_done = False
            self.chore.save()
            self.delete()
