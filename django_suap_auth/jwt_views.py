import json
import logging

from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from .utils import get_oauth2_client

logger = logging.getLogger(__name__)


class BaseSuapTokenView(View):
    """Base class-based view for SUAP JWT token endpoints."""

    http_method_names = ["post", "options"]

    def http_method_not_allowed(self, request, *args, **kwargs):
        logger.warning("Method %s not allowed on %s", request.method, request.path)
        response = JsonResponse(
            {"detail": f'Method "{request.method}" not allowed.'},
            status=405,
        )
        response["Allow"] = ", ".join(self._allowed_methods())
        return response

    def parse_json_body(self, request):
        """Parse JSON from request body.

        Returns a tuple ``(data_dict, error_response)``.
        """
        if not request.body:
            return None, JsonResponse({"detail": "Request body cannot be empty."}, status=400)
        try:
            data = json.loads(request.body.decode("utf-8"))
            if not isinstance(data, dict):
                return None, JsonResponse(
                    {"detail": "Invalid JSON format: expected a JSON object."},
                    status=400,
                )
            return data, None
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            return None, JsonResponse({"detail": f"Invalid JSON: {exc}"}, status=400)

    def get_client(self):
        """Return SUAP client configured from Django settings."""
        return get_oauth2_client(require_oauth=False)


@method_decorator(csrf_exempt, name="dispatch")
class SuapTokenPairView(BaseSuapTokenView):
    """
    Entrypoint for SUAP JWT Token Obtain Pair (/api/token/pair).

    Accepts POST with JSON payload:
        {"username": "<str>", "password": "<str>"}

    Returns 200 OK with:
        {"access": "<access_token>", "refresh": "<refresh_token>", "username": "<username>"}
    or error response forwarded from SUAP (e.g. 401 Unauthorized).
    """

    def post(self, request, *args, **kwargs):
        data, error_response = self.parse_json_body(request)
        if error_response:
            return error_response

        username = data.get("username")
        password = data.get("password")

        errors = {}
        if not username or not isinstance(username, str):
            errors["username"] = ["This field is required."]
        if not password or not isinstance(password, str):
            errors["password"] = ["This field is required."]

        if errors:
            return JsonResponse(errors, status=400)

        client = self.get_client()
        status_code, response_data = client.obtain_token_pair(username, password)
        return JsonResponse(response_data, status=status_code)


@method_decorator(csrf_exempt, name="dispatch")
class SuapTokenRefreshView(BaseSuapTokenView):
    """
    Entrypoint for SUAP JWT Token Refresh (/api/token/refresh).

    Accepts POST with JSON payload:
        {"refresh": "<str>"}

    Returns 200 OK with:
        {"access": "<access_token>", "refresh": "<refresh_token>"}
    or error response forwarded from SUAP (e.g. 401 Unauthorized).
    """

    def post(self, request, *args, **kwargs):
        data, error_response = self.parse_json_body(request)
        if error_response:
            return error_response

        refresh = data.get("refresh")
        if not refresh or not isinstance(refresh, str):
            return JsonResponse({"refresh": ["This field is required."]}, status=400)

        client = self.get_client()
        status_code, response_data = client.refresh_token(refresh)
        return JsonResponse(response_data, status=status_code)


@method_decorator(csrf_exempt, name="dispatch")
class SuapTokenVerifyView(BaseSuapTokenView):
    """
    Entrypoint for SUAP JWT Token Verify (/api/token/verify).

    Accepts POST with JSON payload:
        {"token": "<str>"}

    Returns 200 OK with:
        {}
    or error response forwarded from SUAP (e.g. 401 Unauthorized).
    """

    def post(self, request, *args, **kwargs):
        data, error_response = self.parse_json_body(request)
        if error_response:
            return error_response

        token = data.get("token")
        if not token or not isinstance(token, str):
            return JsonResponse({"token": ["This field is required."]}, status=400)

        client = self.get_client()
        status_code, response_data = client.verify_token(token)
        return JsonResponse(response_data, status=status_code)


# Aliases for convenience and compatibility
TokenObtainPairView = SuapTokenPairView
SuapTokenObtainPairView = SuapTokenPairView
TokenRefreshView = SuapTokenRefreshView
TokenVerifyView = SuapTokenVerifyView
