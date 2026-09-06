from django.urls import path

from . import views

urlpatterns = [
    path("", views.chore_list, name="chore-list"),
    path("chores/new/", views.chore_create, name="chore-create"),
    path("chores/<int:pk>/reassign/", views.chore_reassign, name="chore-reassign"),
    path("chores/<int:pk>/complete/", views.chore_complete, name="chore-complete"),
    path("chores/<int:pk>/edit/", views.chore_edit, name="chore-edit"),
    path("chores/<int:pk>/delete/", views.chore_delete, name="chore-delete"),
    path("whoareyou/", views.member_picker, name="member-picker"),
    path("history/", views.history, name="history"),
    path(
        "completions/<int:pk>/undo/",
        views.completion_undo,
        name="completion-undo",
    ),
]
