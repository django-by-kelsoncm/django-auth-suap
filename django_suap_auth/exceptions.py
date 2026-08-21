class SuapAuthError(Exception):
    """Base exception for django-suap-auth."""


class SuapTokenError(SuapAuthError):
    """Raised when the OAuth2 token exchange fails."""


class SuapUserInfoError(SuapAuthError):
    """Raised when fetching user info from SUAP fails."""

    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.status_code = status_code


class SuapStateMismatchError(SuapAuthError):
    """Raised when the OAuth2 state parameter does not match (possible CSRF)."""


class SuapAPIError(SuapAuthError):
    """Raised when a SUAP API call fails."""

    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.status_code = status_code


class SuapUserNotAllowedError(SuapAuthError):
    """Raised when a SUAP user has no local account and CREATE_USER is False."""
