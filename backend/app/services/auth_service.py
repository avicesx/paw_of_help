"""Сценарии регистрации и входа: проверки уникальности, пароль, выпуск токена."""

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import create_access_token, get_password_hash, normalize_ru_mobile, verify_password
from app.models import User
from app.schemas import LoginRequest, RegisterRequest


async def register_user(payload: RegisterRequest, db: AsyncSession) -> str:
    """
    Сохраняет нового пользователя при уникальном username.
    Возвращает подписанный access token (``sub`` = id пользователя).
    """
    existing_user = await db.scalar(select(User).where(User.username == payload.username))
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Этот username уже занят",
        )

    user = User(
        username=payload.username,
        password_hash=get_password_hash(payload.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return create_access_token(str(user.id))


async def login_user(payload: LoginRequest, db: AsyncSession) -> str:
    """
    Находит пользователя по username, email или телефону, проверяет пароль, обновляет ``last_login``.
    Возвращает access token или 401 при неверных данных.
    """
    login = payload.login.strip()
    
    # Сначала ищем по username
    user = await db.scalar(select(User).where(User.username == login))
    
    if not user:
        # Если не найдено, проверяем, является ли login email
        if "@" in login:
            user = await db.scalar(select(User).where(User.email == login.lower()))
        else:
            # Иначе пытаемся нормализовать как phone
            try:
                normalized_phone = normalize_ru_mobile(login)
                user = await db.scalar(select(User).where(User.phone == normalized_phone))
            except ValueError:
                pass  # Не phone, продолжаем

    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Аккаунт заблокирован",
        )

    user.last_login = datetime.now(timezone.utc)
    await db.commit()

    return create_access_token(str(user.id))
