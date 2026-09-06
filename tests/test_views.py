import pytest
from django.http import HttpResponse
from django.test import RequestFactory
from django.urls import reverse

from chores.models import Member
from chores.session import SESSION_KEY, get_current_member, require_member


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
