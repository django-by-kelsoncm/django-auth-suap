from .helpers import get_active_user, is_impersonating


def impersonation(request):
    """
    Context processor that adds 'active_user' and 'is_impersonating' to the template context.
    """
    return {
        "active_user": get_active_user(request),
        "is_impersonating": is_impersonating(request),
    }
