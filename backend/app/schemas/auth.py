"""Pydantic-схемы тел запросов и ответов эндпоинтов ``/auth/*``."""

from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

from backend.app.core.ru_identity import normalize_ru_mobile, validate_ru_person_name


class LoginRequest(BaseModel):
    """Вход: логин — email (без учёта регистра домена) или нормализованный РФ мобильный."""

    login: str
    password: str = Field(..., min_length=1, max_length=72)

    @field_validator("login", mode="before")
    @classmethod
    def normalize_login(cls, v: str) -> str:
        if v is None or not str(v).strip():
            raise ValueError("Укажите email или телефон")
        raw = str(v).strip()
        if "@" in raw:
            return raw.lower()
        return normalize_ru_mobile(raw)


class RegisterRequest(BaseModel):
    """Регистрация: обязательны имя, пароль и хотя бы один из контактов (email или телефон)."""

    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    password: str = Field(..., min_length=6, max_length=72)

    @field_validator("name", mode="before")
    @classmethod
    def check_name(cls, v: str) -> str:
        return validate_ru_person_name(v)

    @field_validator("phone", mode="before")
    @classmethod
    def check_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is None or (isinstance(v, str) and not v.strip()):
            return None
        return normalize_ru_mobile(str(v))

    @field_validator("email", mode="before")
    @classmethod
    def empty_email_none(cls, v: Optional[str]) -> Optional[str]:
        if v is None or (isinstance(v, str) and not str(v).strip()):
            return None
        return v

    @model_validator(mode="after")
    def validate_login_fields(self):
        if not self.email and not self.phone:
            raise ValueError("Укажите email или российский мобильный телефон")
        return self


class TokenResponse(BaseModel):
    """Ответ с access token (тип по умолчанию — Bearer)."""

    access_token: str
    token_type: str = "bearer"


class MeResponse(BaseModel):
    """Публичные поля текущего пользователя для ``GET /auth/me``."""

    id: int
    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    is_active: bool
