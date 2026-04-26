from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Notification


async def create_notification(
    *,
    user_id: int,
    notification_type: str,
    db: AsyncSession,
    title: Optional[str] = None,
    body: Optional[str] = None,
    data: Optional[dict[str, Any]] = None,
) -> Notification:
    notification = Notification(
        user_id=user_id,
        type=notification_type,
        title=title,
        body=body,
        data=data or {},
    )
    db.add(notification)
    await db.commit()
    await db.refresh(notification)
    return notification
