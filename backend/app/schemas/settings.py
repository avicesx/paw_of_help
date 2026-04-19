from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator
from app.core import normalize_ru_mobile, validate_ru_person_name


class UserSettingsUpdateRequest(BaseModel):
    """обновление полей аккаунта, все поля опциональны"""
    name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = Field(default=None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None

    @field_validator("name", mode="before")
    @classmethod
    def validate_name(cls, v: object) -> object:
        if v is None:
            return None
        s = str(v).strip()
        if not s:
            return None
        return validate_ru_person_name(s)

    @field_validator("last_name", mode="before")
    @classmethod
    def validate_last_name(cls, v: object) -> object:
        if v is None:
            return None
        s = str(v).strip()
        if not s:
            return None
        return validate_ru_person_name(s)

    @field_validator("username", mode="before")
    @classmethod
    def validate_username(cls, v: object) -> object:
        if v is None:
            return None
        s = str(v).strip()
        if not s:
            return None
        if not s.isascii() or not s.isalnum():
            raise ValueError("Username должен содержать только латинские буквы и цифры")
        return s

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v: object) -> object:
        if v is None:
            return None
        s = str(v).strip()
        if not s:
            return None
        return s.lower()

    @field_validator("phone", mode="before")
    @classmethod
    def normalize_phone(cls, v: object) -> object:
        if v is None:
            return None
        s = str(v).strip()
        if not s:
            return None
        return normalize_ru_mobile(s)


class ChangePasswordRequest(BaseModel):
    """смена пароля"""
    current_password: str = Field(..., min_length=1, max_length=72)
    new_password: str = Field(..., min_length=6, max_length=72)