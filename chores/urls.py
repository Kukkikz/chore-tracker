from django.urls import path

from . import views

urlpatterns = [
    path("", views.chore_list, name="chore-list"),
    path("chores/new/", views.chore_create, name="chore-create"),
    path("whoareyou/", views.member_picker, name="member-picker"),
    path("history/", views.history, name="history"),
]
