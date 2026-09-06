from django.contrib import admin

from .models import Chore, Completion, Member


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Chore)
class ChoreAdmin(admin.ModelAdmin):
    list_display = ("name", "assigned_to", "due_date", "is_recurring", "is_done")
    list_filter = ("is_done", "is_recurring", "assigned_to")
    search_fields = ("name",)


@admin.register(Completion)
class CompletionAdmin(admin.ModelAdmin):
    list_display = ("chore", "completed_by", "completed_at")
    list_filter = ("completed_by",)
    ordering = ("-completed_at",)
    readonly_fields = ("completed_at",)
