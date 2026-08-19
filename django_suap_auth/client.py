import logging
from urllib.parse import urlencode

import requests

from .exceptions import SuapTokenError, SuapUserInfoError

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "https://suap.ifrn.edu.br"

AUTHORIZE_PATH = "/o/authorize/"
TOKEN_PATH = "/o/token/"
USER_INFO_PATH = "/api/rh/eu/"
TOKEN_PAIR_PATH = "/api/token/pair"
TOKEN_REFRESH_PATH = "/api/token/refresh"
TOKEN_VERIFY_PATH = "/api/token/verify"

AVAILABLE_SCOPES = [
    "identificacao",
    "email",
    "documentos_pessoais",
    "dados_academicos",
    "dados_pessoais",
    "reitoria",
]


class SuapOAuth2Client:
    """Handles OAuth2 authorization code flow and API / JWT requests with SUAP."""

    def __init__(self, client_id=None, client_secret=None, redirect_uri=None, scopes=None, base_url=None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.scopes = scopes or ["identificacao", "email"]
        self.base_url = (base_url or DEFAULT_BASE_URL).rstrip("/")
        self._session = requests.Session()

    def get_authorization_url(self, state):
        """Return the full authorization URL to redirect the user to."""
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": " ".join(self.scopes),
            "state": state,
        }
        return f"{self.base_url}{AUTHORIZE_PATH}?{urlencode(params)}"

    def exchange_code_for_token(self, code, timeout=30):
        """Exchange an authorization code for an access token."""
        url = f"{self.base_url}{TOKEN_PATH}"
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "redirect_uri": self.redirect_uri,
            "grant_type": "authorization_code",
        }
        try:
            response = self._session.post(url, data=data, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as exc:
            raise SuapTokenError(f"Token exchange failed: {exc}") from exc
        except requests.RequestException as exc:
            raise SuapTokenError(f"Token exchange request error: {exc}") from exc
        except Exception as exc:
            raise SuapTokenError(f"Token exchange unexpected error: {exc}") from exc

    def get_endpoint_data(self, access_token, path_or_url, timeout=30):
        """Fetch JSON data from a specific SUAP API endpoint or full URL."""
        if path_or_url.startswith("http://") or path_or_url.startswith("https://"):
            url = path_or_url
        else:
            url = f"{self.base_url}/{path_or_url.lstrip('/')}"
        headers = {"Authorization": f"Bearer {access_token}"}
        try:
            response = self._session.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as exc:
            raise SuapUserInfoError(f"Failed to fetch endpoint '{path_or_url}': {exc}") from exc
        except requests.RequestException as exc:
            raise SuapUserInfoError(f"Endpoint '{path_or_url}' request error: {exc}") from exc
        except Exception as exc:
            raise SuapUserInfoError(f"Endpoint '{path_or_url}' unexpected error: {exc}") from exc

    def _post_json_endpoint(self, path_or_url, payload, timeout=30):
        """Send a POST request with JSON payload to a SUAP endpoint.

        Returns a tuple of ``(status_code, data_dict)``.
        """
        if path_or_url.startswith("http://") or path_or_url.startswith("https://"):
            url = path_or_url
        else:
            url = f"{self.base_url}/{path_or_url.lstrip('/')}"
        headers = {"Content-Type": "application/json"}
        try:
            response = self._session.post(url, json=payload, headers=headers, timeout=timeout)
            try:
                data = response.json()
            except Exception:
                data = {"detail": response.text} if response.text else {}
            return response.status_code, data
        except requests.Timeout as exc:
            logger.warning("Timeout communicating with SUAP at '%s': %s", url, exc)
            return 504, {"detail": f"Gateway timeout connecting to SUAP: {exc}"}
        except requests.RequestException as exc:
            logger.warning("Error communicating with SUAP at '%s': %s", url, exc)
            return 503, {"detail": f"SUAP service unavailable: {exc}"}
        except Exception as exc:
            logger.exception("Unexpected error communicating with SUAP at '%s': %s", url, exc)
            return 500, {"detail": f"Internal server error communicating with SUAP: {exc}"}

    def obtain_token_pair(self, username, password, timeout=30):
        """Request a JWT token pair (access, refresh) from SUAP.

        Returns a tuple of ``(status_code, data_dict)``.
        """
        return self._post_json_endpoint(TOKEN_PAIR_PATH, {"username": username, "password": password}, timeout=timeout)

    def refresh_token(self, refresh, timeout=30):
        """Refresh a JWT access token using a refresh token from SUAP.

        Returns a tuple of ``(status_code, data_dict)``.
        """
        return self._post_json_endpoint(TOKEN_REFRESH_PATH, {"refresh": refresh}, timeout=timeout)

    def verify_token(self, token, timeout=30):
        """Verify a JWT token with SUAP.

        Returns a tuple of ``(status_code, data_dict)``.
        """
        return self._post_json_endpoint(TOKEN_VERIFY_PATH, {"token": token}, timeout=timeout)

    post_token_pair = obtain_token_pair
    post_token_refresh = refresh_token
    post_token_verify = verify_token

    def get_user_info(self, access_token, timeout=30):
        """Fetch the authenticated user's profile from SUAP via the fetcher chain."""
        from .fetchers import run_user_info_fetcher_chain

        return run_user_info_fetcher_chain(self, access_token)


SuapClient = SuapOAuth2Client
