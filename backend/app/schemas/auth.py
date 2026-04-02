"""Pydantic-схемы тел запросов и ответов эндпоинтов ``/auth/*``."""

from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

from app.core import normalize_ru_mobile, validate_ru_person_name


class LoginRequest(BaseModel):
    """Вход: логин — username, email или нормализованный РФ мобильный."""

    login: str
    password: str = Field(..., min_length=1, max_length=72)


class RegisterRequest(BaseModel):
    """Регистрация: обязательны username и password."""

    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=72)

    @field_validator("username", mode="before")
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not v.isascii() or not v.isalnum():
            raise ValueError("Username должен содержать только латинские буквы и цифры")
        return v


class TokenResponse(BaseModel):
    """Ответ с access token (тип по умолчанию — Bearer)."""

    access_token: str
    token_type: str = "bearer"


class MeResponse(BaseModel):
    """Публичные поля текущего пользователя для ``GET /auth/me``."""

    id: int
    name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    is_active: bool
