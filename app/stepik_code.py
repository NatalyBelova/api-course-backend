import hashlib
import hmac
from datetime import date

from app.config import settings


def generate_stepik_code(practice: str) -> str:
    week = date.today().isocalendar()
    week_key = f"{week[0]}-W{week[1]:02d}"
    message = f"{practice}-{week_key}".encode()
    digest = hmac.new(settings.STEPIK_CODE_SECRET.encode(), message, hashlib.sha256).hexdigest()

    return digest[:8].upper()
