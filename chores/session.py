from functools import wraps

from django.shortcuts import redirect
from django.urls import reverse
from django.utils.http import urlencode

from .models import Member

SESSION_KEY = "member_id"


def get_current_member(request):
    """Return the Member for the session's member_id, or None.

    Clears the session key when it points at a member that no longer exists.
    """
    member_id = request.session.get(SESSION_KEY)
    if member_id is None:
        return None

    member = Member.objects.filter(pk=member_id).first()
    if member is None:
        del request.session[SESSION_KEY]
    return member


def require_member(view):
    """Redirect to the member picker (with ?next=) when no member is selected."""

    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if get_current_member(request) is None:
            picker = reverse("member-picker")
            return redirect(f"{picker}?{urlencode({'next': request.path})}")
        return view(request, *args, **kwargs)

    return wrapper
