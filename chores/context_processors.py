from .session import get_current_member


def current_member(request):
    return {"current_member": get_current_member(request)}
