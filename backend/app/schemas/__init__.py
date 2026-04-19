"""Pydantic схемы."""
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, MeResponse
from app.schemas.reviews import ReviewCreateRequest, ReviewResponse
from app.schemas.settings import ChangePasswordRequest, UserSettingsUpdateRequest
from app.schemas.user import UserBase, UserCreate, UserResponse
from app.schemas.animal_species import AnimalSpeciesCreate, AnimalSpeciesResponse

__all__ = [
    "LoginRequest",
    "RegisterRequest",
    "TokenResponse",
    "MeResponse",
    "ReviewCreateRequest",
    "ReviewResponse",
    "ChangePasswordRequest",
    "UserSettingsUpdateRequest",
    "UserBase",
    "UserCreate",
    "UserResponse",
    "AnimalSpeciesCreate",
    "AnimalSpeciesResponse",
]