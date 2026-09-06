from datetime import date, timedelta

import pytest
from django.contrib.messages import get_messages
from django.http import HttpResponse
from django.test import RequestFactory
from django.urls import reverse
from django.utils import timezone

from chores.models import Chore, Completion, Member
from chores.session import SESSION_KEY, get_current_member, require_member


def _make_chore(name, member, days, is_done=False):
    return Chore.objects.create(
        name=name,
        assigned_to=member,
        due_date=date.today() + timedelta(days=days),
        is_done=is_done,
    )


def _make_due_chore(member, name):
    return Chore.objects.create(name=name, assigned_to=member, due_date=date.today())


def _sign_in(client, member):
    session = client.session
    session[SESSION_KEY] = member.pk
    session.save()


_select_member = _sign_in


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


def _chore_post_data(member, **overrides):
    data = {
        "name": "Vacuum",
        "is_recurring": "",
        "recurrence_rule": "",
        "assigned_to": str(member.pk),
        "due_date": date.today().isoformat(),
    }
    data.update(overrides)
    return data


@pytest.mark.django_db
def test_complete_one_off_logs_completion_and_drops_from_list(client):
    member = Member.objects.create(name="Alex")
    chore = _make_due_chore(member, "Sweep")
    _sign_in(client, member)

    response = client.post(reverse("chore-complete", args=[chore.pk]), follow=True)

    completion = Completion.objects.get()
    assert completion.completed_by == member
    assert "<td>Sweep</td>" not in response.content.decode()


@pytest.mark.django_db
def test_complete_recurring_spawns_next_occurrence(client):
    member = Member.objects.create(name="Alex")
    chore = Chore.objects.create(
        name="Water plants",
        assigned_to=member,
        due_date=date.today(),
        is_recurring=True,
        recurrence_rule="every_7_days",
    )
    _sign_in(client, member)

    body = client.post(
        reverse("chore-complete", args=[chore.pk]), follow=True
    ).content.decode()

    new_chore = Chore.objects.get(is_done=False)
    assert new_chore.due_date == date.today() + timedelta(days=7)
    assert "Water plants" in body


@pytest.mark.django_db
def test_complete_without_member_redirects_to_picker_and_logs_nothing(client):
    member = Member.objects.create(name="Alex")
    chore = _make_due_chore(member, "Sweep")

    response = client.post(reverse("chore-complete", args=[chore.pk]))

    assert response.status_code == 302
    assert reverse("member-picker") in response["Location"]
    assert Completion.objects.count() == 0


@pytest.mark.django_db
def test_complete_double_post_creates_exactly_one_completion(client):
    member = Member.objects.create(name="Alex")
    chore = _make_due_chore(member, "Sweep")
    _sign_in(client, member)

    client.post(reverse("chore-complete", args=[chore.pk]))
    response = client.post(reverse("chore-complete", args=[chore.pk]))

    assert response.status_code == 302
    assert Completion.objects.count() == 1


@pytest.mark.django_db
def test_complete_get_returns_405(client):
    member = Member.objects.create(name="Alex")
    chore = _make_due_chore(member, "Sweep")
    _sign_in(client, member)

    response = client.get(reverse("chore-complete", args=[chore.pk]))

    assert response.status_code == 405


@pytest.mark.django_db
def test_chore_create_get_renders_blank_form(client):
    member = Member.objects.create(name="Alex")
    _sign_in(client, member)

    response = client.get(reverse("chore-create"))

    assert response.status_code == 200
    assert "<form" in response.content.decode()


@pytest.mark.django_db
def test_chore_create_redirects_to_picker_without_member(client):
    response = client.get(reverse("chore-create"))

    assert response.status_code == 302
    assert reverse("member-picker") in response["Location"]


@pytest.mark.django_db
def test_chore_create_happy_path_creates_and_redirects(client):
    member = Member.objects.create(name="Alex")
    _sign_in(client, member)

    response = client.post(reverse("chore-create"), _chore_post_data(member))

    assert response.status_code == 302
    assert response["Location"] == reverse("chore-list")
    chore = Chore.objects.get()
    assert chore.name == "Vacuum"
    assert [str(m) for m in get_messages(response.wsgi_request)] == ['Added "Vacuum"']


@pytest.mark.django_db
def test_chore_create_success_message_shows_on_list(client):
    member = Member.objects.create(name="Alex")
    _sign_in(client, member)

    response = client.post(
        reverse("chore-create"), _chore_post_data(member), follow=True
    )

    assert response.status_code == 200
    body = response.content.decode()
    assert "<article" in body
    assert "Added" in body and "Vacuum" in body


@pytest.mark.django_db
def test_chore_create_recurring_missing_rule_creates_nothing(client):
    member = Member.objects.create(name="Alex")
    _sign_in(client, member)

    response = client.post(
        reverse("chore-create"),
        _chore_post_data(member, is_recurring="on", recurrence_rule=""),
    )

    assert response.status_code == 200
    assert Chore.objects.count() == 0


@pytest.mark.django_db
def test_chore_create_recurring_bad_rule_creates_nothing(client):
    member = Member.objects.create(name="Alex")
    _sign_in(client, member)

    response = client.post(
        reverse("chore-create"),
        _chore_post_data(member, is_recurring="on", recurrence_rule="every_funday"),
    )

    assert response.status_code == 200
    assert Chore.objects.count() == 0


@pytest.mark.django_db
def test_chore_create_non_recurring_ignores_submitted_rule(client):
    member = Member.objects.create(name="Alex")
    _sign_in(client, member)

    client.post(
        reverse("chore-create"),
        _chore_post_data(member, is_recurring="", recurrence_rule="every_monday"),
    )

    assert Chore.objects.get().recurrence_rule == ""


@pytest.mark.django_db
def test_reassign_happy_path_changes_assignee_and_redirects(client):
    alex = Member.objects.create(name="Alex")
    sam = Member.objects.create(name="Sam")
    chore = _make_chore("Dishes", alex, 1)
    _sign_in(client, alex)

    response = client.post(
        reverse("chore-reassign", args=[chore.pk]), {"assigned_to": sam.pk}
    )

    assert response.status_code == 302
    assert response["Location"] == reverse("chore-list")
    chore.refresh_from_db()
    assert chore.assigned_to == sam


@pytest.mark.django_db
def test_reassign_same_member_is_a_no_op_success(client):
    alex = Member.objects.create(name="Alex")
    chore = _make_chore("Dishes", alex, 1)
    _sign_in(client, alex)

    response = client.post(
        reverse("chore-reassign", args=[chore.pk]), {"assigned_to": alex.pk}
    )

    assert response.status_code == 302
    chore.refresh_from_db()
    assert chore.assigned_to == alex


@pytest.mark.django_db
def test_reassign_done_chore_is_rejected(client):
    alex = Member.objects.create(name="Alex")
    sam = Member.objects.create(name="Sam")
    chore = _make_chore("Dishes", alex, 1, is_done=True)
    _sign_in(client, alex)

    response = client.post(
        reverse("chore-reassign", args=[chore.pk]), {"assigned_to": sam.pk}
    )

    assert response.status_code == 302
    chore.refresh_from_db()
    assert chore.assigned_to == alex
    assert "Can't reassign a completed chore" in [
        str(m) for m in get_messages(response.wsgi_request)
    ]


@pytest.mark.django_db
def test_reassign_invalid_member_id_is_rejected(client):
    alex = Member.objects.create(name="Alex")
    chore = _make_chore("Dishes", alex, 1)
    _sign_in(client, alex)

    response = client.post(
        reverse("chore-reassign", args=[chore.pk]), {"assigned_to": "9999"}
    )

    assert response.status_code == 302
    assert response["Location"] == reverse("chore-list")
    chore.refresh_from_db()
    assert chore.assigned_to == alex


@pytest.mark.django_db
def test_reassign_get_returns_405(client):
    alex = Member.objects.create(name="Alex")
    chore = _make_chore("Dishes", alex, 1)
    _sign_in(client, alex)

    response = client.get(reverse("chore-reassign", args=[chore.pk]))

    assert response.status_code == 405


@pytest.mark.django_db
def test_reassign_without_member_redirects_to_picker(client):
    alex = Member.objects.create(name="Alex")
    chore = _make_chore("Dishes", alex, 1)

    response = client.post(
        reverse("chore-reassign", args=[chore.pk]), {"assigned_to": alex.pk}
    )

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


@pytest.mark.django_db
def test_history_redirects_to_picker_when_no_member(client):
    response = client.get(reverse("history"))

    assert response.status_code == 302
    assert reverse("member-picker") in response["Location"]


@pytest.mark.django_db
def test_history_lists_completions_newest_first(client):
    alice = Member.objects.create(name="Alice")
    older = Completion.objects.create(
        chore=_make_due_chore(alice, "Dishes"), completed_by=alice
    )
    Completion.objects.create(chore=_make_due_chore(alice, "Trash"), completed_by=alice)
    Completion.objects.filter(pk=older.pk).update(
        completed_at=timezone.now() - timedelta(days=2)
    )
    _select_member(client, alice)

    content = client.get(reverse("history")).content.decode()

    assert content.index("Trash") < content.index("Dishes")


@pytest.mark.django_db
def test_history_member_filter_narrows(client):
    alice = Member.objects.create(name="Alice")
    bob = Member.objects.create(name="Bob")
    Completion.objects.create(chore=_make_due_chore(alice, "Dishes"), completed_by=alice)
    Completion.objects.create(chore=_make_due_chore(bob, "Laundry"), completed_by=bob)
    _select_member(client, alice)

    content = client.get(reverse("history"), {"member": alice.pk}).content.decode()

    assert "Dishes" in content
    assert "Laundry" not in content


@pytest.mark.django_db
def test_history_invalid_member_falls_back_to_all(client):
    alice = Member.objects.create(name="Alice")
    bob = Member.objects.create(name="Bob")
    Completion.objects.create(chore=_make_due_chore(alice, "Dishes"), completed_by=alice)
    Completion.objects.create(chore=_make_due_chore(bob, "Laundry"), completed_by=bob)
    _select_member(client, alice)

    content = client.get(reverse("history"), {"member": "nope"}).content.decode()

    assert "Dishes" in content
    assert "Laundry" in content


@pytest.mark.django_db
def test_history_empty_state_renders_message(client):
    alice = Member.objects.create(name="Alice")
    _select_member(client, alice)

    content = client.get(reverse("history")).content.decode()

    assert "No completions recorded yet." in content


# --- edit / delete a chore -------------------------------------------------


@pytest.mark.django_db
def test_chore_list_shows_edit_delete_on_not_done_rows(client):
    member = Member.objects.create(name="Alex")
    _make_chore("Active", member, 3)
    _sign_in(client, member)

    body = client.get(reverse("chore-list")).content.decode()

    assert ">Edit</a>" in body
    assert '"secondary">Delete</a>' in body


@pytest.mark.django_db
def test_chore_list_hides_edit_delete_when_all_done(client):
    member = Member.objects.create(name="Alex")
    _make_chore("Finished", member, 3, is_done=True)
    _make_chore("Active", member, 1)
    _sign_in(client, member)

    body = client.get(reverse("chore-list")).content.decode()

    assert body.count(">Edit</a>") == 1
    assert body.count(">Delete</a>") == 1


@pytest.mark.django_db
def test_edit_get_prefills_form(client):
    member = Member.objects.create(name="Alex")
    chore = _make_chore("Mop floor", member, 3)
    _sign_in(client, member)

    body = client.get(reverse("chore-edit", args=[chore.pk])).content.decode()

    assert "Mop floor" in body
    assert "<form" in body


@pytest.mark.django_db
def test_edit_happy_path_saves_and_redirects(client):
    member = Member.objects.create(name="Alex")
    chore = _make_chore("Mop", member, 3)
    _sign_in(client, member)

    response = client.post(
        reverse("chore-edit", args=[chore.pk]),
        _chore_post_data(member, name="Mop the kitchen"),
    )

    assert response.status_code == 302
    assert response["Location"] == reverse("chore-list")
    chore.refresh_from_db()
    assert chore.name == "Mop the kitchen"
    assert "Mop the kitchen" in [str(m) for m in get_messages(response.wsgi_request)][0]


@pytest.mark.django_db
def test_edit_invalid_recurrence_rerenders_and_saves_nothing(client):
    member = Member.objects.create(name="Alex")
    chore = _make_chore("Mop", member, 3)
    _sign_in(client, member)

    response = client.post(
        reverse("chore-edit", args=[chore.pk]),
        _chore_post_data(
            member, name="Changed", is_recurring="on", recurrence_rule="every_funday"
        ),
    )

    assert response.status_code == 200
    assert "not a recognised rule" in response.content.decode()
    chore.refresh_from_db()
    assert chore.name == "Mop"


@pytest.mark.django_db
def test_edit_recurring_missing_rule_is_a_form_error(client):
    member = Member.objects.create(name="Alex")
    chore = _make_chore("Mop", member, 3)
    _sign_in(client, member)

    response = client.post(
        reverse("chore-edit", args=[chore.pk]),
        _chore_post_data(member, is_recurring="on", recurrence_rule=""),
    )

    assert response.status_code == 200
    assert "needs a recurrence rule" in response.content.decode()


@pytest.mark.django_db
def test_edit_done_chore_is_rejected_and_unchanged(client):
    member = Member.objects.create(name="Alex")
    chore = _make_chore("Mop", member, 3, is_done=True)
    _sign_in(client, member)

    get_response = client.get(reverse("chore-edit", args=[chore.pk]))
    post_response = client.post(
        reverse("chore-edit", args=[chore.pk]),
        _chore_post_data(member, name="Changed"),
    )

    assert get_response.status_code == 302
    assert post_response.status_code == 302
    chore.refresh_from_db()
    assert chore.name == "Mop"
    assert "Can't edit a completed chore" in [
        str(m) for m in get_messages(post_response.wsgi_request)
    ]


@pytest.mark.django_db
def test_edit_wrong_verb_returns_405(client):
    member = Member.objects.create(name="Alex")
    chore = _make_chore("Mop", member, 3)
    _sign_in(client, member)

    response = client.put(reverse("chore-edit", args=[chore.pk]))

    assert response.status_code == 405


@pytest.mark.django_db
def test_edit_unknown_id_returns_404(client):
    member = Member.objects.create(name="Alex")
    _sign_in(client, member)

    response = client.get(reverse("chore-edit", args=[9999]))

    assert response.status_code == 404


@pytest.mark.django_db
def test_edit_without_member_redirects_to_picker(client):
    member = Member.objects.create(name="Alex")
    chore = _make_chore("Mop", member, 3)

    response = client.get(reverse("chore-edit", args=[chore.pk]))

    assert response.status_code == 302
    assert reverse("member-picker") in response["Location"]


@pytest.mark.django_db
def test_delete_get_renders_confirm_page_and_deletes_nothing(client):
    member = Member.objects.create(name="Alex")
    chore = _make_chore("Mop", member, 3)
    _sign_in(client, member)

    body = client.get(reverse("chore-delete", args=[chore.pk])).content.decode()

    assert "Mop" in body
    assert '<form method="post">' in body
    assert Chore.objects.filter(pk=chore.pk).exists()


@pytest.mark.django_db
def test_delete_confirm_page_reports_completion_count(client):
    member = Member.objects.create(name="Alex")
    chore = _make_chore("Mop", member, 3)
    Completion.objects.create(chore=chore, completed_by=member)
    Completion.objects.create(chore=chore, completed_by=member)
    _sign_in(client, member)

    body = client.get(reverse("chore-delete", args=[chore.pk])).content.decode()

    assert "2 completion" in body


@pytest.mark.django_db
def test_delete_happy_path_removes_chore_and_completions(client):
    member = Member.objects.create(name="Alex")
    chore = _make_chore("Mop", member, 3)
    Completion.objects.create(chore=chore, completed_by=member)
    _sign_in(client, member)

    response = client.post(reverse("chore-delete", args=[chore.pk]))

    assert response.status_code == 302
    assert response["Location"] == reverse("chore-list")
    assert not Chore.objects.filter(pk=chore.pk).exists()
    assert Completion.objects.count() == 0


@pytest.mark.django_db
def test_delete_message_notes_completion_count(client):
    member = Member.objects.create(name="Alex")
    chore = _make_chore("Mop", member, 3)
    Completion.objects.create(chore=chore, completed_by=member)
    _sign_in(client, member)

    response = client.post(reverse("chore-delete", args=[chore.pk]))

    message = [str(m) for m in get_messages(response.wsgi_request)][0]
    assert "1 completion" in message


@pytest.mark.django_db
def test_delete_message_omits_count_when_zero(client):
    member = Member.objects.create(name="Alex")
    chore = _make_chore("Mop", member, 3)
    _sign_in(client, member)

    response = client.post(reverse("chore-delete", args=[chore.pk]))

    message = [str(m) for m in get_messages(response.wsgi_request)][0]
    assert "completion" not in message
    assert "Mop" in message


@pytest.mark.django_db
def test_delete_done_chore_is_allowed_and_cascades(client):
    member = Member.objects.create(name="Alex")
    chore = _make_chore("Mop", member, 3, is_done=True)
    Completion.objects.create(chore=chore, completed_by=member)
    _sign_in(client, member)

    confirm = client.get(reverse("chore-delete", args=[chore.pk])).content.decode()
    response = client.post(reverse("chore-delete", args=[chore.pk]))

    assert "1 completion" in confirm
    assert response.status_code == 302
    assert not Chore.objects.filter(pk=chore.pk).exists()
    assert Completion.objects.count() == 0


@pytest.mark.django_db
def test_delete_without_csrf_returns_403():
    from django.test import Client

    csrf_client = Client(enforce_csrf_checks=True)
    member = Member.objects.create(name="Alex")
    chore = _make_chore("Mop", member, 3)
    _sign_in(csrf_client, member)

    response = csrf_client.post(reverse("chore-delete", args=[chore.pk]))

    assert response.status_code == 403
    assert Chore.objects.filter(pk=chore.pk).exists()


@pytest.mark.django_db
def test_delete_wrong_verb_returns_405(client):
    member = Member.objects.create(name="Alex")
    chore = _make_chore("Mop", member, 3)
    _sign_in(client, member)

    response = client.patch(reverse("chore-delete", args=[chore.pk]))

    assert response.status_code == 405


@pytest.mark.django_db
def test_delete_unknown_id_returns_404(client):
    member = Member.objects.create(name="Alex")
    _sign_in(client, member)

    response = client.get(reverse("chore-delete", args=[9999]))

    assert response.status_code == 404


@pytest.mark.django_db
def test_delete_without_member_redirects_to_picker(client):
    member = Member.objects.create(name="Alex")
    chore = _make_chore("Mop", member, 3)

    response = client.get(reverse("chore-delete", args=[chore.pk]))

    assert response.status_code == 302
    assert reverse("member-picker") in response["Location"]
