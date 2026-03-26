"""Ядро приложения: конфиг, БД, безопасность."""
from app.core.config import settings
from app.core.database import Base, get_db
from app.core.security import create_access_token, get_password_hash, verify_password
from app.core.rate_limit import limiter
from app.core.deps import get_current_user, get_current_user_id
from app.core.ru_identity import normalize_ru_mobile, validate_ru_person_name

__all__ = [
    "settings",
    "Base",
    "get_db",
    "create_access_token",
    "get_password_hash",
    "verify_password",
    "limiter",
    "get_current_user",
    "get_current_user_id",
    "normalize_ru_mobile",
    "validate_ru_person_name",
]
