from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core import get_password_hash, verify_password
from app.models import User
from app.schemas.settings import ChangePasswordRequest, UserSettingsUpdateRequest


async def update_me(user: User, payload: UserSettingsUpdateRequest, db: AsyncSession) -> User:
    data = payload.model_dump(exclude_unset=True)

    new_username = data.get("username")
    if new_username is not None and new_username != user.username:
        existing = await db.scalar(
            select(User).where(User.username == new_username, User.id != user.id)
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Этот username уже занят",
            )

    new_email = data.get("email")
    if new_email is not None and new_email != user.email:
        existing = await db.scalar(select(User).where(User.email == new_email, User.id != user.id))
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Этот email уже занят",
            )

    new_phone = data.get("phone")
    if new_phone is not None and new_phone != user.phone:
        existing = await db.scalar(select(User).where(User.phone == new_phone, User.id != user.id))
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Этот телефон уже занят",
            )

    for key, value in data.items():
        if hasattr(user, key):
            setattr(user, key, value)

    await db.commit()
    await db.refresh(user)
    return user


async def change_password(user: User, payload: ChangePasswordRequest, db: AsyncSession) -> None:
    if not verify_password(payload.current_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Текущий пароль указан неверно",
        )

    user.password_hash = get_password_hash(payload.new_password)
    await db.commit()

