import logging
from urllib.parse import urlsplit, urlunsplit

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View

logger = logging.getLogger(__name__)

__all__ = [
    "ImpersonateView",
    "StopImpersonatingView",
    "impersonate",
    "stop_impersonating",
]


def _get_safe_redirect(request):
    next_url = request.GET.get("next") or request.META.get("HTTP_REFERER") or ""
    safe_next_url = next_url.replace("\\", "")
    parsed_next = urlsplit(safe_next_url)
    is_safe = (
        safe_next_url
        and safe_next_url.startswith("/")
        and not parsed_next.scheme
        and not parsed_next.netloc
        and url_has_allowed_host_and_scheme(
            url=safe_next_url,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        )
    )
    if is_safe:
        return redirect(urlunsplit(("", "", parsed_next.path, parsed_next.query, "")))
    return redirect(getattr(settings, "LOGIN_REDIRECT_URL", "/"))


class ImpersonateView(View):
    """
    Allows a superuser to impersonate another non-superuser.
    """

    def get(self, request, username=None):
        return self._handle_impersonation(request, username)

    def post(self, request, username=None):
        return self._handle_impersonation(request, username)

    def _handle_impersonation(self, request, username=None):
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated or not user.is_superuser:
            raise PermissionDenied("Only superusers can impersonate users.")

        target_username = username or request.GET.get("username") or request.POST.get("username")
        if not target_username:
            messages.error(request, "Username is required for impersonation.")
            return _get_safe_redirect(request)

        if "impersonated_user" in request.session:
            messages.error(request, "Nested impersonation is not allowed.")
            return _get_safe_redirect(request)

        User = get_user_model()
        username_field = getattr(User, "USERNAME_FIELD", "username")
        target_user = User.objects.filter(**{username_field: target_username}).first()

        if not target_user:
            messages.error(request, f"User '{target_username}' does not exist.")
            return _get_safe_redirect(request)

        if target_user.is_superuser:
            messages.error(request, "Impersonating another superuser is not allowed.")
            return _get_safe_redirect(request)

        request.session["impersonated_user"] = getattr(target_user, username_field)
        request.session["_impersonate_by"] = user.pk
        from django_suap_auth.audit.signals import suap_impersonate_started

        suap_impersonate_started.send(
            sender=self.__class__, request=request, impersonator=user, target_user=target_user
        )

        messages.success(request, f"You are now impersonating {target_username}.")
        return _get_safe_redirect(request)


class StopImpersonatingView(View):
    """
    Ends active user impersonation for the current session.
    """

    def get(self, request):
        return self._handle_stop(request)

    def post(self, request):
        return self._handle_stop(request)

    def _handle_stop(self, request):
        if "impersonated_user" in request.session:
            impersonator = getattr(request, "user", None)
            request.session.pop("impersonated_user", None)
            request.session.pop("_impersonate_by", None)
            from django_suap_auth.audit.signals import suap_impersonate_stopped

            suap_impersonate_stopped.send(
                sender=self.__class__,
                request=request,
                impersonator=impersonator,
                target_user=None,
            )

            messages.success(request, "Impersonation ended successfully.")
        return _get_safe_redirect(request)


impersonate = ImpersonateView.as_view()
stop_impersonating = StopImpersonatingView.as_view()
