import os
from datetime import date, datetime
from urllib.parse import urlparse

import requests
from django.core.files.base import ContentFile


def parse_date(value, suap_info=None, date_format="%Y-%m-%d"):
    """Parse a date string into a datetime.date object.

    Returns None if value is empty or invalid format.
    """
    if not value:
        return None
    if isinstance(value, date):
        return value
    try:
        return datetime.strptime(str(value).strip(), date_format).date()
    except (ValueError, TypeError):
        return None


def format_cpf(value, suap_info=None):
    """Format an 11-digit CPF string into 'XXX.XXX.XXX-XX'.

    If invalid length or empty, returns cleaned digits.
    """
    if not value:
        return ""
    digits = "".join(filter(str.isdigit, str(value)))
    if len(digits) == 11:
        return f"{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}"
    return digits


def to_upper(value, suap_info=None):
    """Convert value to uppercase string."""
    return str(value).upper() if value is not None else ""


def to_lower(value, suap_info=None):
    """Convert value to lowercase string."""
    return str(value).lower() if value is not None else ""


def to_bool(value, suap_info=None):
    """Coerce value to boolean."""
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in ("true", "1", "t", "yes", "sim")
    return bool(value)


def fetch_image_file(value, suap_info=None, timeout=10, filename=None):
    """Download image from URL and return a Django ContentFile suitable for FileField/ImageField.

    Returns None if value is empty, invalid, or fetch fails.
    """
    if not value or not isinstance(value, str):
        return None

    try:
        response = requests.get(value, timeout=timeout)
        response.raise_for_status()
        if not filename:
            path = urlparse(value).path
            filename = os.path.basename(path) or "suap_photo.jpg"
            if not os.path.splitext(filename)[1]:
                filename += ".jpg"
        return ContentFile(response.content, name=filename)
    except Exception:
        return None
