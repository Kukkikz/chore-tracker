from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_GET, require_http_methods

from .models import Chore, Member
from .session import SESSION_KEY, require_member


@require_GET
@require_member
def chore_list(request):
    chores = (
        Chore.objects.filter(is_done=False)
        .select_related("assigned_to")
        .order_by("due_date", "name")
    )
    return render(request, "chores/chore_list.html", {"chores": chores})


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
