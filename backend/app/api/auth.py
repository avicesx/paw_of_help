"""HTTP-роуты регистрации и входа (ЕУЗ)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import settings, get_db, get_current_user, limiter
from app.models import User
from app.schemas import LoginRequest, MeResponse, RegisterRequest, TokenResponse
from app.services import login_user, register_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
@limiter.limit(settings.AUTH_RATE_LIMIT)
async def register(
    request: Request,
    payload: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """Создаёт пользователя и возвращает JWT access token."""
    access_token = await register_user(payload=payload, db=db)
    return TokenResponse(access_token=access_token)


@router.post("/login", response_model=TokenResponse)
@limiter.limit(settings.AUTH_RATE_LIMIT)
async def login(
    request: Request,
    payload: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Выдаёт JWT по email или нормализованному российскому мобильному номеру и паролю."""
    access_token = await login_user(payload=payload, db=db)
    return TokenResponse(access_token=access_token)


@router.get(
    "/me",
    response_model=MeResponse,
    summary="Текущий пользователь",
    openapi_extra={"security": [{"BearerAuth": []}]},
)
async def me(current: Annotated[User, Depends(get_current_user)]):
    """Данные пользователя по валидному Bearer access token."""
    return MeResponse(
        id=current.id,
        name=current.name,
        email=current.email,
        phone=current.phone,
        is_active=current.is_active,
    )
