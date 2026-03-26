"""Схемы пользователя для создания сущности и ответов API (без жёсткой валидации имени в ответе)."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.core import normalize_ru_mobile, validate_ru_person_name


class UserBase(BaseModel):
    """Общие поля профиля."""

    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None


class UserCreate(UserBase):
    """Данные для создания пользователя (те же правила имени и телефона, что при регистрации)."""

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


class UserResponse(UserBase):
    """Публичное представление пользователя из ORM (read model)."""

    id: int
    photo_url: Optional[str] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
