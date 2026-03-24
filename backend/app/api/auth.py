"""HTTP-роуты регистрации и входа (ЕУЗ)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.core.deps import get_current_user
from backend.app.core.rate_limit import limiter
from backend.app.models.user import User
from backend.app.schemas.auth import LoginRequest, MeResponse, RegisterRequest, TokenResponse
from backend.app.services.auth_service import login_user, register_user

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
