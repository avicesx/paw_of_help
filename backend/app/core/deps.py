"""Зависимости FastAPI: текущий пользователь по JWT Bearer."""

from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.models.user import User

security = HTTPBearer(auto_error=False)


async def get_current_user_id(
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
) -> int:
    """Извлекает id пользователя из access JWT (поле ``sub``)."""
    if creds is None or creds.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Нужен заголовок Authorization: Bearer <токен>",
        )
    try:
        payload = jwt.decode(
            creds.credentials,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        sub = payload.get("sub")
        if sub is None:
            raise ValueError
        return int(sub)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Срок действия токена истёк",
        )
    except (jwt.InvalidTokenError, ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительный токен",
        )


async def get_current_user(
    db: Annotated[AsyncSession, Depends(get_db)],
    user_id: Annotated[int, Depends(get_current_user_id)],
) -> User:
    """Загружает пользователя из БД; неактивный — 403."""
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Аккаунт заблокирован",
        )
    return user
