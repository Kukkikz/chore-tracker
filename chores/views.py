from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import (
    require_GET,
    require_http_methods,
    require_POST,
)

from .forms import ChoreForm
from .models import Chore, Completion, Member
from .session import SESSION_KEY, require_member


@require_GET
@require_member
def chore_list(request):
    chores = (
        Chore.objects.filter(is_done=False)
        .select_related("assigned_to")
        .order_by("due_date", "name")
    )
    return render(
        request,
        "chores/chore_list.html",
        {"chores": chores, "members": Member.objects.all()},
    )


@require_POST
@require_member
def chore_reassign(request, pk):
    chore = get_object_or_404(Chore, pk=pk)

    if chore.is_done:
        messages.error(request, "Can't reassign a completed chore")
        return redirect("chore-list")

    member = Member.objects.filter(pk=request.POST.get("assigned_to")).first()
    if member is None:
        messages.error(request, "Pick a member to reassign to")
        return redirect("chore-list")

    chore.assigned_to = member
    chore.save()
    messages.success(request, f'Reassigned "{chore.name}" to {member.name}')
    return redirect("chore-list")


@require_http_methods(["GET", "POST"])
@require_member
def chore_create(request):
    if request.method == "POST":
        form = ChoreForm(request.POST)
        if form.is_valid():
            chore = form.save()
            messages.success(request, f'Added "{chore.name}"')
            return redirect("chore-list")
    else:
        form = ChoreForm()

    return render(request, "chores/chore_form.html", {"form": form})


@require_http_methods(["GET", "POST"])
def member_picker(request):
    if request.method == "POST":
        member = Member.objects.filter(pk=request.POST.get("member_id")).first()
        if member is not None:
            request.session[SESSION_KEY] = member.pk

        next_url = request.POST.get("next") or request.GET.get("next")
        if next_url and url_has_allowed_host_and_scheme(
            next_url, allowed_hosts={request.get_host()}
        ):
            return redirect(next_url)
        return redirect("/")

    return render(
        request,
        "chores/member_picker.html",
        {"members": Member.objects.all(), "next": request.GET.get("next", "")},
    )


@require_GET
@require_member
def history(request):
    completions = Completion.objects.select_related("chore", "completed_by").order_by(
        "-completed_at"
    )

    member_id = request.GET.get("member", "")
    selected_member = None
    if member_id.isdigit():
        selected_member = Member.objects.filter(pk=member_id).first()
    if selected_member is not None:
        completions = completions.filter(completed_by=selected_member)

    return render(
        request,
        "chores/history.html",
        {
            "completions": completions,
            "members": Member.objects.all(),
            "selected_member_id": selected_member.pk if selected_member else None,
        },
    )
