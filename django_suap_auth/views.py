import logging
from urllib.parse import urlsplit, urlunsplit

from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View

from .exceptions import SuapStateMismatchError, SuapTokenError, SuapUserInfoError, SuapUserNotAllowedError
from .jwt_views import (
    BaseSuapTokenView,
    SuapApiFetchView,
    SuapTokenObtainPairView,
    SuapTokenPairView,
    SuapTokenRefreshView,
    SuapTokenVerifyView,
    SuapUserInfoFetchView,
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from .utils import generate_state, get_oauth2_client, get_suap_settings

logger = logging.getLogger(__name__)

__all__ = [
    "SuapLoginView",
    "SuapCallbackView",
    "SuapAuthenticationError",
    "BaseSuapTokenView",
    "SuapTokenPairView",
    "SuapTokenRefreshView",
    "SuapTokenVerifyView",
    "SuapUserInfoFetchView",
    "SuapApiFetchView",
    "TokenObtainPairView",
    "SuapTokenObtainPairView",
    "TokenRefreshView",
    "TokenVerifyView",
]


class SuapLoginView(View):
    """
    Initiates the SUAP OAuth2 authorization code flow.

    If ``SUAP_AUTH['DIRECT_REDIRECT']`` is ``True`` (the default), the user is
    redirected immediately to SUAP. Set it to ``False`` to render an
    intermediate confirmation page instead — subclass this view and override
    ``get_intermediate_template`` to customize the template rendered.
    """

    intermediate_template = "django_suap_auth/login.html"

    def get(self, request):
        cfg = get_suap_settings()
        storage = messages.get_messages(request)
        if not cfg["direct_redirect"] or bool(storage):
            from django.shortcuts import render

            return render(request, self.intermediate_template)

        client = get_oauth2_client()
        state = generate_state()
        request.session["suap_oauth2_state"] = state
        authorization_url = client.get_authorization_url(state)
        return redirect(authorization_url)

    def post(self, request):
        """Handle form submission from the intermediate login page."""
        client = get_oauth2_client()
        state = generate_state()
        request.session["suap_oauth2_state"] = state
        authorization_url = client.get_authorization_url(state)
        return redirect(authorization_url)


class SuapAuthenticationError(Exception):
    """Raised when SUAP authentication fails."""


class SuapCallbackView(View):
    """Handles the OAuth2 callback from SUAP."""

    def get(self, request):
        from django.conf import settings

        cfg = get_suap_settings()
        error = request.GET.get("error")
        if error:
            messages.error(request, f"SUAP login error: {error}")
            return redirect(settings.LOGIN_URL)

        try:
            # 1. Validar state (CSRF protection)
            received_state = request.GET.get("state", "")
            stored_state = request.session.pop("suap_oauth2_state", None)

            if not stored_state or received_state != stored_state:
                raise SuapStateMismatchError("OAuth2 state mismatch — possible CSRF attack.")

            # 2. Trocar código por token
            code = request.GET.get("code")

            client = get_oauth2_client()
            try:
                token_data = client.exchange_code_for_token(code)
            except Exception as e:
                raise SuapTokenError(f"Failed to exchange code for token: {e}")

            access_token = token_data.get("access_token")
            if not access_token:
                raise SuapTokenError("access_token not found in token response")

            # 3. Buscar informações do usuário
            try:
                user_info = client.get_user_info(access_token)
            except Exception as e:
                raise SuapUserInfoError(f"Failed to retrieve user info: {e}")

            # 4. Autenticar usuário no Django
            user = authenticate(request, suap_user_info=user_info)

            if user is not None:
                backend_path = getattr(user, "backend", cfg["backend"])
                login(request, user, backend=backend_path)

                # 5. Redirecionar para próxima página
                next_url = request.GET.get("next", "")

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
                    safe_redirect = urlunsplit(("", "", parsed_next.path, parsed_next.query, ""))
                    return HttpResponseRedirect(safe_redirect)
                else:
                    return redirect(settings.LOGIN_REDIRECT_URL)
            else:
                raise SuapAuthenticationError("Authentication failed. User not found or invalid credentials.")

        except SuapStateMismatchError as e:
            logger.warning("SUAP state mismatch error: %s", e)
            messages.error(request, "Security check failed. Please try logging in again.")
            return redirect(settings.LOGIN_URL)
        except SuapTokenError as e:
            logger.warning("SUAP authorization code exchange error: %s", e)
            messages.error(request, "Failed to complete login. Please try again.")
            return redirect(settings.LOGIN_URL)
        except SuapUserInfoError as e:
            logger.warning("SUAP user info error: %s", e)
            messages.error(request, "Failed to retrieve your profile. Please try again.")
            return redirect(settings.LOGIN_URL)
        except SuapUserNotAllowedError as e:
            logger.warning("SUAP user not allowed: %s", e)
            messages.error(request, "Your account is not authorised to access this application.")
            return redirect(settings.LOGIN_URL)
        except SuapAuthenticationError as e:
            logger.warning("SUAP authentication error: %s", e)
            messages.error(request, "Authentication failed. Please try again.")
            return redirect(settings.LOGIN_URL)
        except Exception as e:
            logger.exception("Unexpected error during SUAP callback: %s", e)
            messages.error(request, "An unexpected error occurred. Please try again.")
            return redirect(settings.LOGIN_URL)
