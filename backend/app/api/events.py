from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core import get_current_user, get_db
from app.models import Event, EventParticipant, Subscription, User
from app.schemas import EventCreate, EventParticipantResponse, EventResponse, EventUpdate
from app.services import (
    cancel_participation,
    create_notification,
    get_event_or_404,
    list_subscriber_ids,
    register_participant,
    require_org_staff,
)


router = APIRouter(prefix="/events", tags=["events"])


@router.get("", response_model=list[EventResponse])
async def list_events(
    organization_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
):
    q = select(Event).order_by(Event.id.desc())
    if organization_id is not None:
        q = q.where(Event.organization_id == organization_id)
    rows = (await db.scalars(q)).all()
    return [EventResponse.model_validate(r) for r in rows]


@router.get(
    "/subscribed",
    response_model=list[EventResponse],
    summary="Лента мероприятий подписок",
    openapi_extra={"security": [{"BearerAuth": []}]},
)
async def subscribed_events(
    current: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    org_ids = (
        await db.scalars(
            select(Subscription.organization_id).where(Subscription.user_id == current.id)
        )
    ).all()
    if not org_ids:
        return []
    rows = (
        await db.scalars(
            select(Event).where(Event.organization_id.in_(org_ids)).order_by(Event.id.desc())
        )
    ).all()
    return [EventResponse.model_validate(r) for r in rows]


@router.post(
    "/organizations/{org_id}",
    response_model=EventResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать мероприятие организации",
    openapi_extra={"security": [{"BearerAuth": []}]},
)
async def create_event(
    org_id: int,
    payload: EventCreate,
    current: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    await require_org_staff(db, org_id=org_id, user_id=current.id)

    ev = Event(
        organization_id=org_id,
        title=payload.title,
        description=payload.description,
        event_type=payload.event_type,
        start_datetime=payload.start_datetime,
        end_datetime=payload.end_datetime,
        location=payload.location,
        created_by=current.id,
    )
    db.add(ev)
    await db.commit()
    await db.refresh(ev)

    # Уведомить подписчиков организации
    subscriber_ids = await list_subscriber_ids(db, organization_id=org_id)
    for uid in set(subscriber_ids):
        await create_notification(
            db,
            user_id=uid,
            type="event_created",
            title="Новое мероприятие",
            body=f"Организация добавила мероприятие «{ev.title}»",
            data={"event_id": ev.id, "organization_id": org_id},
            commit=False,
        )
    await db.commit()

    return EventResponse.model_validate(ev)


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(event_id: int, db: AsyncSession = Depends(get_db)):
    ev = await get_event_or_404(db, event_id)
    return EventResponse.model_validate(ev)


@router.patch(
    "/{event_id}",
    response_model=EventResponse,
    summary="Обновить мероприятие",
    openapi_extra={"security": [{"BearerAuth": []}]},
)
async def update_event(
    event_id: int,
    payload: EventUpdate,
    current: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    ev = await get_event_or_404(db, event_id)
    await require_org_staff(db, org_id=ev.organization_id, user_id=current.id)

    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(ev, k, v)
    await db.commit()
    await db.refresh(ev)

    subscriber_ids = await list_subscriber_ids(db, organization_id=ev.organization_id)
    for uid in set(subscriber_ids):
        await create_notification(
            db,
            user_id=uid,
            type="event_updated",
            title="Мероприятие обновлено",
            body=f"Обновлено мероприятие «{ev.title}»",
            data={"event_id": ev.id, "organization_id": ev.organization_id},
            commit=False,
        )
    await db.commit()

    return EventResponse.model_validate(ev)


@router.delete(
    "/{event_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить мероприятие",
    openapi_extra={"security": [{"BearerAuth": []}]},
)
async def delete_event(
    event_id: int,
    current: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    ev = await get_event_or_404(db, event_id)
    await require_org_staff(db, org_id=ev.organization_id, user_id=current.id)
    await db.delete(ev)
    await db.commit()
    return None


@router.post(
    "/{event_id}/register",
    response_model=EventParticipantResponse,
    summary="Зарегистрироваться на мероприятие",
    openapi_extra={"security": [{"BearerAuth": []}]},
)
async def register(
    event_id: int,
    current: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    await get_event_or_404(db, event_id)
    ep = await register_participant(db, event_id=event_id, user_id=current.id)
    return EventParticipantResponse.model_validate(ep)


@router.delete(
    "/{event_id}/register",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Отменить участие",
    openapi_extra={"security": [{"BearerAuth": []}]},
)
async def unregister(
    event_id: int,
    current: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    await cancel_participation(db, event_id=event_id, user_id=current.id)
    return None


@router.get(
    "/{event_id}/participants",
    response_model=list[EventParticipantResponse],
    summary="Список участников (для организации)",
    openapi_extra={"security": [{"BearerAuth": []}]},
)
async def list_participants(
    event_id: int,
    current: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    ev = await get_event_or_404(db, event_id)
    await require_org_staff(db, org_id=ev.organization_id, user_id=current.id)
    rows = (await db.scalars(select(EventParticipant).where(EventParticipant.event_id == event_id))).all()
    return [EventParticipantResponse.model_validate(r) for r in rows]