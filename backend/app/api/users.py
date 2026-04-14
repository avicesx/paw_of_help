from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core import get_current_user, get_db
from app.models import User
from app.schemas import ChangePasswordRequest, MeResponse, UserSettingsUpdateRequest
from app.services import change_password, update_me

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/me",
    response_model=MeResponse,
    summary="Текущий пользователь",
    openapi_extra={"security": [{"BearerAuth": []}]},
)
async def me(current: Annotated[User, Depends(get_current_user)]):
    return MeResponse(
        id=current.id,
        name=current.name,
        last_name=current.last_name,
        username=current.username,
        email=current.email,
        phone=current.phone,
        is_active=current.is_active,
    )


@router.patch(
    "/me",
    response_model=MeResponse,
    summary="Обновить настройки аккаунта",
    openapi_extra={"security": [{"BearerAuth": []}]},
)
async def patch_me(
    payload: UserSettingsUpdateRequest,
    current: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    user = await update_me(user=current, payload=payload, db=db)
    return MeResponse(
        id=user.id,
        name=user.name,
        last_name=user.last_name,
        username=user.username,
        email=user.email,
        phone=user.phone,
        is_active=user.is_active,
    )


@router.post(
    "/me/change-password",
    summary="Сменить пароль",
    openapi_extra={"security": [{"BearerAuth": []}]},
)
async def post_change_password(
    payload: ChangePasswordRequest,
    current: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await change_password(user=current, payload=payload, db=db)
    return {"message": "Пароль обновлён"}