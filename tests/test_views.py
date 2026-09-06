from datetime import date, timedelta

import pytest
from django.http import HttpResponse
from django.test import RequestFactory
from django.urls import reverse

from chores.models import Chore, Member
from chores.session import SESSION_KEY, get_current_member, require_member


def _make_chore(name, member, days, is_done=False):
    return Chore.objects.create(
        name=name,
        assigned_to=member,
        due_date=date.today() + timedelta(days=days),
        is_done=is_done,
    )


def _sign_in(client, member):
    session = client.session
    session[SESSION_KEY] = member.pk
    session.save()


@pytest.mark.django_db
def test_chore_list_shows_only_not_done_chores_in_due_date_order(client):
    member = Member.objects.create(name="Alex")
    _make_chore("Later", member, 5)
    _make_chore("Sooner", member, 1)
    _make_chore("Finished", member, 2, is_done=True)
    _sign_in(client, member)

    body = client.get(reverse("chore-list")).content.decode()

    assert "Finished" not in body
    assert body.index("Sooner") < body.index("Later")


@pytest.mark.django_db
def test_chore_list_flags_overdue_row_with_class_and_badge(client):
    member = Member.objects.create(name="Alex")
    _make_chore("Take out trash", member, -2)
    _sign_in(client, member)

    body = client.get(reverse("chore-list")).content.decode()

    assert "overdue" in body
    assert "Overdue" in body


@pytest.mark.django_db
def test_chore_list_does_not_flag_chore_due_today(client):
    member = Member.objects.create(name="Alex")
    _make_chore("Dishes", member, 0)
    _sign_in(client, member)

    body = client.get(reverse("chore-list")).content.decode()

    assert "overdue" not in body
    assert "Overdue" not in body


@pytest.mark.django_db
def test_chore_list_empty_state_message_and_no_table(client):
    member = Member.objects.create(name="Alex")
    _sign_in(client, member)

    body = client.get(reverse("chore-list")).content.decode()

    assert "Nothing to do" in body
    assert "<table" not in body


@pytest.mark.django_db
def test_chore_list_redirects_to_picker_without_member(client):
    response = client.get(reverse("chore-list"))

    assert response.status_code == 302
    assert reverse("member-picker") in response["Location"]


@pytest.mark.django_db
def test_picker_get_lists_all_members(client):
    Member.objects.create(name="Alice")
    Member.objects.create(name="Bob")

    response = client.get(reverse("member-picker"))

    assert response.status_code == 200
    content = response.content.decode()
    assert "Alice" in content
    assert "Bob" in content


@pytest.mark.django_db
def test_picker_get_with_no_members_shows_message_and_no_buttons(client):
    response = client.get(reverse("member-picker"))

    content = response.content.decode()
    assert "no members yet — add one in /admin" in content
    assert "<button" not in content


@pytest.mark.django_db
def test_post_sets_session_and_redirects_to_root(client):
    member = Member.objects.create(name="Alice")

    response = client.post(reverse("member-picker"), {"member_id": member.pk})

    assert response.status_code == 302
    assert response["Location"] == "/"
    assert client.session[SESSION_KEY] == member.pk


@pytest.mark.django_db
def test_post_honours_safe_next(client):
    member = Member.objects.create(name="Alice")

    response = client.post(
        reverse("member-picker"), {"member_id": member.pk, "next": "/chores/"}
    )

    assert response.status_code == 302
    assert response["Location"] == "/chores/"


@pytest.mark.django_db
def test_post_ignores_offsite_next(client):
    member = Member.objects.create(name="Alice")

    response = client.post(
        reverse("member-picker"),
        {"member_id": member.pk, "next": "https://evil.example.com/"},
    )

    assert response.status_code == 302
    assert response["Location"] == "/"


@pytest.mark.django_db
def test_guarded_view_redirects_to_picker_with_next_when_no_member(rf):
    guarded = require_member(lambda request: HttpResponse("ok"))
    request = rf.get("/chores/")
    request.session = {}

    response = guarded(request)

    assert response.status_code == 302
    assert response["Location"] == f"{reverse('member-picker')}?next=%2Fchores%2F"


@pytest.mark.django_db
def test_guarded_view_passes_through_when_member_set(rf):
    member = Member.objects.create(name="Alice")
    guarded = require_member(lambda request: HttpResponse("ok"))
    request = rf.get("/chores/")
    request.session = {SESSION_KEY: member.pk}

    response = guarded(request)

    assert response.status_code == 200


@pytest.mark.django_db
def test_get_current_member_none_for_unset_key(rf):
    request = rf.get("/")
    request.session = {}

    assert get_current_member(request) is None


@pytest.mark.django_db
def test_get_current_member_none_for_stale_id_and_clears_key(rf):
    request = rf.get("/")
    request.session = {SESSION_KEY: 999}

    assert get_current_member(request) is None
    assert SESSION_KEY not in request.session
