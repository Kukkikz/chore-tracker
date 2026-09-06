from django import forms

from .models import Chore
from .recurrence import is_valid_rule


class ChoreForm(forms.ModelForm):
    class Meta:
        model = Chore
        fields = ["name", "is_recurring", "recurrence_rule", "assigned_to", "due_date"]
        widgets = {"due_date": forms.DateInput(attrs={"type": "date"})}

    def clean(self):
        cleaned_data = super().clean()
        is_recurring = cleaned_data.get("is_recurring")
        rule = cleaned_data.get("recurrence_rule") or ""

        if is_recurring:
            if not rule:
                self.add_error(
                    "recurrence_rule", "A recurring chore needs a recurrence rule."
                )
            elif not is_valid_rule(rule):
                self.add_error("recurrence_rule", f'"{rule}" is not a recognised rule.')
        else:
            cleaned_data["recurrence_rule"] = ""

        return cleaned_data
