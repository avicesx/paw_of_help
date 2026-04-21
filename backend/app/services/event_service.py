from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Event, EventParticipant, OrganizationUser, Subscription


async def require_org_staff(db: AsyncSession, *, org_id: int, user_id: int) -> OrganizationUser:
    ou = await db.scalar(
        select(OrganizationUser).where(
            OrganizationUser.organization_id == org_id,
            OrganizationUser.user_id == user_id,
            OrganizationUser.invitation_status == "accepted",
            OrganizationUser.role.in_(["admin", "curator"]),
        )
    )
    if ou is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав")
    return ou


async def get_event_or_404(db: AsyncSession, event_id: int) -> Event:
    ev = await db.get(Event, event_id)
    if ev is None:
        raise HTTPException(status_code=404, detail="Мероприятие не найдено")
    return ev


async def list_subscriber_ids(db: AsyncSession, *, organization_id: int) -> list[int]:
    ids = (
        await db.scalars(select(Subscription.user_id).where(Subscription.organization_id == organization_id))
    ).all()
    return list(ids)


async def register_participant(db: AsyncSession, *, event_id: int, user_id: int) -> EventParticipant:
    existing = await db.get(EventParticipant, {"event_id": event_id, "user_id": user_id})
    if existing:
        if existing.status != "registered":
            existing.status = "registered"
            await db.commit()
            await db.refresh(existing)
        return existing

    ep = EventParticipant(event_id=event_id, user_id=user_id, status="registered")
    db.add(ep)
    await db.commit()
    await db.refresh(ep)
    return ep


async def cancel_participation(db: AsyncSession, *, event_id: int, user_id: int) -> None:
    ep = await db.get(EventParticipant, {"event_id": event_id, "user_id": user_id})
    if ep is None:
        raise HTTPException(status_code=404, detail="Участие не найдено")
    ep.status = "cancelled"
    await db.commit()