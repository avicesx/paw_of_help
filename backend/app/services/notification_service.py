from typing import Any, Dict, Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Notification


async def create_notification(
    db: AsyncSession,
    *,
    user_id: int,
    type: str,
    title: Optional[str] = None,
    body: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None,
    commit: bool = True,
) -> Notification:
    """
    Создаёт уведомление для пользователя
    """
    n = Notification(
        user_id=user_id,
        type=type,
        title=title,
        body=body,
        data=data or {},
    )
    db.add(n)
    if commit:
        await db.commit()
        await db.refresh(n)
    return n


async def create_unread_notification_once(
    db: AsyncSession,
    *,
    user_id: int,
    type: str,
    dedupe_data: Dict[str, Any],
    title: Optional[str] = None,
    body: Optional[str] = None,
) -> Notification | None:
    """
    Создаёт ОДНО непрочитанное уведомление с данным type+dedupe_data.
    """
    existing = await db.scalar(
        select(Notification.id).where(
            Notification.user_id == user_id,
            Notification.type == type,
            Notification.is_read.is_(False),
            Notification.data == dedupe_data,
        )
    )
    if existing:
        return None
    return await create_notification(
        db,
        user_id=user_id,
        type=type,
        title=title,
        body=body,
        data=dedupe_data,
        commit=True,
    )


async def mark_notification_read_by_data(
    db: AsyncSession,
    *,
    user_id: int,
    type: str,
    data: Dict[str, Any],
) -> None:
    """Пометить непрочитанные уведомления как прочитанные"""
    await db.execute(
        update(Notification)
        .where(
            Notification.user_id == user_id,
            Notification.type == type,
            Notification.is_read.is_(False),
            Notification.data == data,
        )
        .values(is_read=True)
    )
    await db.commit()