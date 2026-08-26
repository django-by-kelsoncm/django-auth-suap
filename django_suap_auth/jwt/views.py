import json
import logging

from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from django_suap_auth.utils import get_oauth2_client

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


@method_decorator(csrf_exempt, name="dispatch")
class SuapUserInfoFetchView(BaseSuapTokenView):
    """
    Entrypoint for fetching SUAP data with a JWT access token (/api/rh/eu/ or /api/token/user-info).

    Accepts GET/POST with 'Authorization: Bearer <access_token>' header
    OR POST with JSON payload:
        {"token": "<access_token>", "endpoint": "/api/rh/eu/"}
    """

    http_method_names = ["get", "post", "options"]

    def dispatch(self, request, *args, **kwargs):
        if request.method.lower() not in self.http_method_names:
            return self.http_method_not_allowed(request, *args, **kwargs)
        return super().dispatch(request, *args, **kwargs)

    def handle_request(self, request, *args, **kwargs):
        token = None
        endpoint = "/api/rh/eu/"

        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()

        if request.body:
            data, error_response = self.parse_json_body(request)
            if error_response and not token:
                return error_response
            if isinstance(data, dict):
                token = token or data.get("token") or data.get("access")
                if data.get("endpoint"):
                    endpoint = data.get("endpoint")

        if not token and request.GET.get("token"):
            token = request.GET.get("token")
        if request.GET.get("endpoint"):
            endpoint = request.GET.get("endpoint")

        if not token:
            return JsonResponse(
                {"token": ["This field is required in request header (Authorization: Bearer <token>) or JSON body."]},
                status=400,
            )

        client = self.get_client()
        try:
            response_data = client.get_endpoint_data(token, endpoint)
            return JsonResponse(response_data, status=200, safe=False)
        except Exception as exc:
            return JsonResponse({"detail": str(exc)}, status=400)

    def get(self, request, *args, **kwargs):
        return self.handle_request(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.handle_request(request, *args, **kwargs)


# Aliases for convenience and compatibility
TokenObtainPairView = SuapTokenPairView
SuapTokenObtainPairView = SuapTokenPairView
TokenRefreshView = SuapTokenRefreshView
TokenVerifyView = SuapTokenVerifyView
SuapApiFetchView = SuapUserInfoFetchView
