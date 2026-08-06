from urllib.parse import urlencode

import requests

from .exceptions import SuapTokenError, SuapUserInfoError

DEFAULT_BASE_URL = "https://suap.ifrn.edu.br"

AUTHORIZE_PATH = "/o/authorize/"
TOKEN_PATH = "/o/token/"
USER_INFO_PATH = "/api/rh/eu/"

AVAILABLE_SCOPES = [
    "identificacao",
    "email",
    "documentos_pessoais",
    "dados_academicos",
    "dados_pessoais",
    "reitoria",
]


class SuapOAuth2Client:
    """Handles the OAuth2 authorization code flow with SUAP."""

    def __init__(self, client_id, client_secret, redirect_uri, scopes=None, base_url=None):
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

    def get_user_info(self, access_token, timeout=30):
        """Fetch the authenticated user's profile from SUAP via the fetcher chain."""
        from .fetchers import run_user_info_fetcher_chain

        return run_user_info_fetcher_chain(self, access_token)
