from django.contrib.auth import get_user_model


def get_active_user(request):
    """
    Return the active user for the given request.

    If a superuser is currently impersonating another user (stored in session under
    "impersonated_user"), return the impersonated User instance. Otherwise, return
    request.user.
    """
    if request is None or not getattr(request, "user", None) or not request.user.is_authenticated:
        return getattr(request, "user", None)

    if request.user.is_superuser:
        impersonated_username = request.session.get("impersonated_user")
        if impersonated_username:
            User = get_user_model()
            username_field = getattr(User, "USERNAME_FIELD", "username")
            target_user = User.objects.filter(**{username_field: impersonated_username}).first()
            if target_user and not target_user.is_superuser:
                return target_user

    return request.user


def is_impersonating(request):
    """
    Return True if the current request is an active user impersonation session.
    """
    if request is None or not getattr(request, "user", None) or not request.user.is_authenticated:
        return False

    if not request.user.is_superuser:
        return False

    impersonated_username = request.session.get("impersonated_user")
    if not impersonated_username:
        return False

    User = get_user_model()
    username_field = getattr(User, "USERNAME_FIELD", "username")
    target_user = User.objects.filter(**{username_field: impersonated_username}).first()
    return bool(target_user and not target_user.is_superuser)
