from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.core import get_current_user, get_db
from app.models import Notification, User
from app.schemas.communication import NotificationResponse


router = APIRouter(prefix="/notifications", tags=["notifications"])


async def _get_notification_or_404(db: AsyncSession, notification_id: int) -> Notification:
    n = await db.get(Notification, notification_id)
    if n is None:
        raise HTTPException(status_code=404, detail="Уведомление не найдено")
    return n


@router.get(
    "",
    response_model=list[NotificationResponse],
    openapi_extra={"security": [{"BearerAuth": []}]},
)
async def list_notifications(
    is_read: Optional[bool] = None,
    current: Annotated[User, Depends(get_current_user)],
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """Список уведомлений текущего пользователя с пагинацией"""
    limit = max(1, min(limit, 200))
    offset = max(0, offset)

    q = select(Notification).where(Notification.user_id == current.id).order_by(Notification.id.desc())
    if is_read is not None:
        q = q.where(Notification.is_read == is_read)
    q = q.limit(limit).offset(offset)

    rows = (await db.scalars(q)).all()
    return [NotificationResponse.model_validate(r) for r in rows]


@router.post(
    "/{notification_id}/read",
    response_model=NotificationResponse,
    openapi_extra={"security": [{"BearerAuth": []}]},
)
async def mark_read(
    notification_id: int,
    current: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    """Отметить прочитанным"""
    n = await _get_notification_or_404(db, notification_id)
    if n.user_id != current.id:
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    if not n.is_read:
        n.is_read = True
        await db.commit()
        await db.refresh(n)
    return NotificationResponse.model_validate(n)


@router.post(
    "/read-all",
    status_code=status.HTTP_204_NO_CONTENT,
    openapi_extra={"security": [{"BearerAuth": []}]},
)
async def mark_all_read(
    current: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    """Отметить все прочитанными"""
    await db.execute(
        update(Notification)
        .where(Notification.user_id == current.id, Notification.is_read.is_(False))
        .values(is_read=True)
    )
    await db.commit()
    return None