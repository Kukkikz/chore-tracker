from django.urls import path

from . import views

urlpatterns = [
    path("whoareyou/", views.member_picker, name="member-picker"),
    path("history/", views.history, name="history"),
]
