from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select, update, delete
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
    summary="Список уведомлений",
    openapi_extra={"security": [{"BearerAuth": []}]},
)
async def list_notifications(
    current: Annotated[User, Depends(get_current_user)],
    is_read: Optional[bool] = None,
    type: Optional[str] = None,
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
    if type is not None:
        q = q.where(Notification.type == type)
    q = q.limit(limit).offset(offset)

    rows = (await db.scalars(q)).all()
    return [NotificationResponse.model_validate(r) for r in rows]


@router.get(
    "/unread-count",
    summary="Количество непрочитанных уведомлений",
    openapi_extra={"security": [{"BearerAuth": []}]},
)
async def unread_count(
    current: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    count = await db.scalar(
        select(func.count(Notification.id)).where(
            Notification.user_id == current.id,
            Notification.is_read.is_(False),
        )
    )
    return {"unread_count": int(count or 0)}


@router.get(
    "/{notification_id}",
    response_model=NotificationResponse,
    summary="Получить уведомление",
    openapi_extra={"security": [{"BearerAuth": []}]},
)
async def get_notification(
    notification_id: int,
    current: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    n = await _get_notification_or_404(db, notification_id)
    if n.user_id != current.id:
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    return NotificationResponse.model_validate(n)


@router.post(
    "/{notification_id}/unread",
    response_model=NotificationResponse,
    summary="Отметить непрочитанным",
    openapi_extra={"security": [{"BearerAuth": []}]},
)
async def mark_unread(
    notification_id: int,
    current: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    n = await _get_notification_or_404(db, notification_id)
    if n.user_id != current.id:
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    if n.is_read:
        n.is_read = False
        await db.commit()
        await db.refresh(n)
    return NotificationResponse.model_validate(n)


@router.delete(
    "/{notification_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить уведомление",
    openapi_extra={"security": [{"BearerAuth": []}]},
)
async def delete_notification(
    notification_id: int,
    current: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    n = await _get_notification_or_404(db, notification_id)
    if n.user_id != current.id:
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    await db.delete(n)
    await db.commit()
    return None


@router.delete(
    "",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Очистить уведомления",
    description="Удаляет уведомления текущего пользователя. Если передан is_read=true/false — удаляет только соответствующие",
    openapi_extra={"security": [{"BearerAuth": []}]},
)
async def clear_notifications(
    current: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
    is_read: Optional[bool] = None,
):
    stmt = delete(Notification).where(Notification.user_id == current.id)
    if is_read is not None:
        stmt = stmt.where(Notification.is_read == is_read)
    await db.execute(stmt)
    await db.commit()
    return None


@router.post(
    "/{notification_id}/read",
    response_model=NotificationResponse,
    summary="Отметить прочитанным",
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
    summary="Отметить все прочитанными",
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
