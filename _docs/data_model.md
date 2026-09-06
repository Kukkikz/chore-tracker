## Data Model

**Member**
- name (CharField, unique)

**Chore**
- name (CharField)
- is_recurring (BooleanField)
- recurrence_rule (CharField, e.g. "every_monday", "every_3_days" — null if one-off)
- assigned_to (ForeignKey → Member)
- due_date (DateField)
- is_done (BooleanField, default False)

**Completion**
- chore (ForeignKey → Chore)
- completed_by (ForeignKey → Member)
- completed_at (DateTimeField, auto_now_add)

## Key Logic

- **Overdue** = `is_done=False` and `due_date < today` (computed, not stored — check it in the view/template).
- **Completing a chore**: create a `Completion` record, set `is_done=True`. If `is_recurring`, also create a new `Chore` row with the next `due_date` (computed from `recurrence_rule`) and `is_done=False`.
- **No Household model needed** — since it's single-household, `Member` and `Chore` are global to the app.