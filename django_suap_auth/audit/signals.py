from django.dispatch import Signal

# Sinais de Autenticação OAuth2 / Backend
suap_auth_success = Signal()
suap_auth_failed = Signal()

# Sinais de JWT
suap_jwt_issued = Signal()
suap_jwt_refreshed = Signal()

# Sinais de Impersonate
suap_impersonate_started = Signal()
suap_impersonate_stopped = Signal()
