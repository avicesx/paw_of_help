"""Сценарии регистрации и входа: проверки уникальности, пароль, выпуск токена."""

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import create_access_token, get_password_hash, verify_password
from app.models import User
from app.schemas import LoginRequest, RegisterRequest


async def register_user(payload: RegisterRequest, db: AsyncSession) -> str:
    """
    Сохраняет нового пользователя при уникальном email/телефоне.
    Возвращает подписанный access token (``sub`` = id пользователя).
    """
    duplicates = []
    if payload.email:
        duplicates.append(User.email == payload.email)
    if payload.phone:
        duplicates.append(User.phone == payload.phone)

    if duplicates:
        existing_user = await db.scalar(select(User).where(or_(*duplicates)))
        if existing_user:
            if payload.email and existing_user.email == payload.email:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Этот email уже зарегистрирован",
                )
            if payload.phone and existing_user.phone == payload.phone:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Этот номер телефона уже зарегистрирован",
                )

    user = User(
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        password_hash=get_password_hash(payload.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return create_access_token(str(user.id))


async def login_user(payload: LoginRequest, db: AsyncSession) -> str:
    """
    Находит пользователя по email или телефону, проверяет пароль, обновляет ``last_login``.
    Возвращает access token или 401 при неверных данных.
    """
    user = await db.scalar(
        select(User).where(or_(User.email == payload.login, User.phone == payload.login))
    )

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
