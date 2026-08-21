import logging

from django.apps import apps

logger = logging.getLogger(__name__)


def report_sync_error_to_sentry(exc, endpoint="", status_code=None, user=None):
    """Notify Sentry if sentry_sdk is installed and initialized."""
    try:
        import sentry_sdk

        if sentry_sdk.is_initialized():
            with sentry_sdk.push_scope() as scope:
                if endpoint:
                    scope.set_extra("endpoint", endpoint)
                if status_code is not None:
                    scope.set_extra("status_code", status_code)
                if user is not None:
                    scope.set_user({"id": getattr(user, "pk", None), "username": getattr(user, "username", str(user))})
                if isinstance(exc, Exception):
                    sentry_sdk.capture_exception(exc)
                else:
                    sentry_sdk.capture_message(str(exc))
    except Exception as e:
        logger.warning("Could not send error report to Sentry: %s", e)


def save_sync_error(endpoint, status_code=None, mensagem_erro="", user=None, exc=None):
    """Report error to Sentry (if available) and save SincronizacaoErro in DB (if app is installed)."""
    report_sync_error_to_sentry(exc or mensagem_erro, endpoint=endpoint, status_code=status_code, user=user)

    if apps.is_installed("django_suap_auth.erros"):
        try:
            from .models import SincronizacaoErro

            return SincronizacaoErro.objects.create(
                usuario=user,
                endpoint=str(endpoint)[:255],
                status_code=status_code,
                mensagem_erro=str(mensagem_erro),
            )
        except Exception as e:
            logger.warning("Could not save SincronizacaoErro to DB: %s", e)
    return None


def save_sync_errors_for_user(user, sync_errors):
    """Save a list of pending sync error dicts for a user instance."""
    if not sync_errors:
        return []
    records = []
    for err in sync_errors:
        record = save_sync_error(
            endpoint=err.get("endpoint", ""),
            status_code=err.get("status_code"),
            mensagem_erro=err.get("mensagem_erro", ""),
            user=user,
            exc=err.get("exc"),
        )
        if record:
            records.append(record)
    return records
