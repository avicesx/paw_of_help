from datetime import datetime
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.chats import OpenChatRequest, open_chat
from app.core import settings
from app.models import (
    Animal,
    FosterOffer,
    FosterPlacement,
    FosterRequest,
    Review,
    User,
    VolunteerProfile,
)
from app.schemas.foster import (
    FosterOfferCreate,
    FosterRequestCreate,
    FosterRequestUpdate,
    FosterVolunteerMatchResponse,
)
from app.services.notification_service import create_notification
from app.services.task_scorer import haversine_distance


async def _get_foster_request_or_404(db: AsyncSession, request_id: int) -> FosterRequest:
    foster_request = await db.get(FosterRequest, request_id)
    if foster_request is None:
        raise HTTPException(status_code=404, detail="Заявка на передержку не найдена")
    return foster_request


async def _get_offer_or_404(db: AsyncSession, offer_id: int) -> FosterOffer:
    offer = await db.get(FosterOffer, offer_id)
    if offer is None:
        raise HTTPException(status_code=404, detail="Отклик на передержку не найден")
    return offer


async def _get_placement_or_404(db: AsyncSession, placement_id: int) -> FosterPlacement:
    placement = await db.get(FosterPlacement, placement_id)
    if placement is None:
        raise HTTPException(status_code=404, detail="Передержка не найдена")
    return placement


async def create_foster_request(
    *,
    owner_id: int,
    payload: FosterRequestCreate,
    db: AsyncSession,
    publish_now: bool = False,
) -> FosterRequest:
    animal = await db.get(Animal, payload.animal_id)
    if animal is None:
        raise HTTPException(status_code=404, detail="Животное не найдено")
    if animal.owner_id != owner_id:
        raise HTTPException(status_code=403, detail="Можно создавать заявки только для своих животных")

    foster_request = FosterRequest(
        owner_id=owner_id,
        animal_id=payload.animal_id,
        start_date=payload.start_date,
        end_date=payload.end_date,
        dates_flexible=payload.dates_flexible,
        pickup_location=payload.pickup_location,
        pickup_lat=payload.pickup_lat,
        pickup_lng=payload.pickup_lng,
        return_location=payload.return_location,
        return_lat=payload.return_lat,
        return_lng=payload.return_lng,
        owner_provides=payload.owner_provides,
        status="published" if publish_now else "draft",
        published_at=datetime.utcnow() if publish_now else None,
    )
    db.add(foster_request)
    await db.commit()
    await db.refresh(foster_request)

    if publish_now:
        await publish_request(request_id=foster_request.id, owner_id=owner_id, db=db)
        await db.refresh(foster_request)
    return foster_request


async def update_foster_request(
    *,
    request_id: int,
    owner_id: int,
    payload: FosterRequestUpdate,
    db: AsyncSession,
) -> FosterRequest:
    foster_request = await _get_foster_request_or_404(db, request_id)
    if foster_request.owner_id != owner_id:
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    if foster_request.status in {"booked", "closed", "cancelled"}:
        raise HTTPException(status_code=400, detail="Нельзя изменить заявку в текущем статусе")

    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(foster_request, key, value)

    await db.commit()
    await db.refresh(foster_request)
    return foster_request


async def publish_request(*, request_id: int, owner_id: int, db: AsyncSession) -> FosterRequest:
    foster_request = await _get_foster_request_or_404(db, request_id)
    if foster_request.owner_id != owner_id:
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    if foster_request.status in {"booked", "closed", "cancelled"}:
        raise HTTPException(status_code=400, detail="Нельзя опубликовать заявку в текущем статусе")

    foster_request.status = "published"
    foster_request.published_at = datetime.utcnow()
    await db.commit()
    await db.refresh(foster_request)

    matches = await match_volunteers(request_id=request_id, db=db)
    for match in matches:
        await create_notification(
            db=db,
            user_id=match.id,
            type="foster_request_published",
            title="Новая заявка на передержку",
            body=f"Появилась подходящая заявка на передержку #{foster_request.id}",
            data={"foster_request_id": foster_request.id, "match_score": match.match_score},
            commit=True,
        )
    return foster_request


async def match_volunteers(*, request_id: int, db: AsyncSession) -> list[FosterVolunteerMatchResponse]:
    foster_request = await _get_foster_request_or_404(db, request_id)
    animal = await db.get(Animal, foster_request.animal_id)
    if animal is None:
        return []

    profiles = (
        await db.scalars(
            select(VolunteerProfile).where(VolunteerProfile.ready_for_foster.is_(True))
        )
    ).all()
    if not profiles:
        return []

    rating_subquery = (
        select(Review.reviewee_id, func.avg(Review.rating).label("avg_rating"))
        .where(Review.target_type == "volunteer")
        .group_by(Review.reviewee_id)
        .subquery()
    )
    users = (
        await db.execute(
            select(User.id, User.name, rating_subquery.c.avg_rating).outerjoin(
                rating_subquery, rating_subquery.c.reviewee_id == User.id
            )
        )
    ).all()
    user_meta = {row.id: {"name": row.name, "rating": float(row.avg_rating or 0.0)} for row in users}

    result: list[FosterVolunteerMatchResponse] = []
    for profile in profiles:
        score = 0.0
        distance: Optional[float] = None

        preferred_types = profile.preferred_animal_types or []
        if preferred_types and animal.species in preferred_types:
            score += settings.WEIGHT_SKILL

        if (
            profile.location_lat is not None
            and profile.location_lng is not None
            and foster_request.pickup_lat is not None
            and foster_request.pickup_lng is not None
        ):
            distance = haversine_distance(
                profile.location_lat,
                profile.location_lng,
                foster_request.pickup_lat,
                foster_request.pickup_lng,
            )
            radius = float(profile.radius_km or 50)
            if distance <= radius:
                score += (1 - (distance / radius)) * settings.WEIGHT_DISTANCE
            else:
                continue

        score += settings.WEIGHT_FOSTER
        rating = user_meta.get(profile.user_id, {}).get("rating", 0.0)
        score += rating * 2
        result.append(
            FosterVolunteerMatchResponse(
                id=profile.user_id,
                name=user_meta.get(profile.user_id, {}).get("name"),
                rating=round(rating, 2),
                distance=round(distance, 2) if distance is not None else None,
                match_score=round(score, 2),
            )
        )

    result.sort(key=lambda item: item.match_score, reverse=True)
    return result


async def create_offer(
    *,
    request_id: int,
    volunteer_id: int,
    payload: FosterOfferCreate,
    db: AsyncSession,
) -> FosterOffer:
    foster_request = await _get_foster_request_or_404(db, request_id)
    if foster_request.owner_id == volunteer_id:
        raise HTTPException(status_code=400, detail="Нельзя откликнуться на свою заявку")
    if foster_request.status != "published":
        raise HTTPException(status_code=400, detail="Отклик возможен только на опубликованную заявку")

    profile = await db.get(VolunteerProfile, volunteer_id)
    if profile is None or not profile.ready_for_foster:
        raise HTTPException(status_code=403, detail="Ваш профиль не готов к передержке")

    existing = await db.scalar(
        select(FosterOffer).where(
            FosterOffer.foster_request_id == request_id,
            FosterOffer.volunteer_id == volunteer_id,
            FosterOffer.status == "pending",
        )
    )
    if existing:
        raise HTTPException(status_code=409, detail="У вас уже есть активный отклик на эту заявку")

    offer = FosterOffer(
        foster_request_id=request_id,
        volunteer_id=volunteer_id,
        type="response",
        status="pending",
        proposed_start_date=payload.proposed_start_date,
        proposed_end_date=payload.proposed_end_date,
        message=payload.message,
    )
    db.add(offer)
    await db.commit()
    await db.refresh(offer)

    await create_notification(
        db=db,
        user_id=foster_request.owner_id,
        type="foster_offer_created",
        title="Новый отклик на передержку",
        body=f"По вашей заявке #{foster_request.id} появился отклик",
        data={"foster_request_id": foster_request.id, "offer_id": offer.id},
        commit=True,
    )
    return offer


async def update_offer_status(
    *,
    offer_id: int,
    volunteer_id: int,
    new_status: str,
    db: AsyncSession,
) -> FosterOffer:
    if new_status not in {"accepted", "declined"}:
        raise HTTPException(status_code=400, detail="Поддерживаются только статусы accepted или declined")

    offer = await _get_offer_or_404(db, offer_id)
    if offer.volunteer_id != volunteer_id:
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    if offer.status != "pending":
        raise HTTPException(status_code=400, detail="Можно изменить только pending-отклик")

    offer.status = new_status
    await db.commit()
    await db.refresh(offer)
    return offer


async def accept_offer(
    *,
    request_id: int,
    offer_id: int,
    owner: User,
    db: AsyncSession,
) -> FosterPlacement:
    foster_request = await _get_foster_request_or_404(db, request_id)
    if foster_request.owner_id != owner.id:
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    if foster_request.status != "published":
        raise HTTPException(status_code=400, detail="Можно принять отклик только для опубликованной заявки")

    offer = await _get_offer_or_404(db, offer_id)
    if offer.foster_request_id != foster_request.id:
        raise HTTPException(status_code=400, detail="Отклик не относится к этой заявке")
    if offer.status not in {"pending", "accepted"}:
        raise HTTPException(status_code=400, detail="Нельзя принять отклик в текущем статусе")

    await db.execute(
        update(FosterOffer)
        .where(
            FosterOffer.foster_request_id == foster_request.id,
            FosterOffer.id != offer.id,
            FosterOffer.status == "pending",
        )
        .values(status="declined")
    )
    offer.status = "accepted"
    foster_request.status = "booked"

    placement = FosterPlacement(
        foster_request_id=foster_request.id,
        volunteer_id=offer.volunteer_id,
        start_date=offer.proposed_start_date or foster_request.start_date,
        end_date=offer.proposed_end_date or foster_request.end_date,
        status="active",
    )
    db.add(placement)
    await db.commit()
    await db.refresh(placement)

    await open_chat(
        payload=OpenChatRequest(context_type="foster_request", context_id=foster_request.id),
        current=owner,
        db=db,
    )
    await create_notification(
        db=db,
        user_id=offer.volunteer_id,
        type="foster_offer_accepted",
        title="Ваш отклик принят",
        body=f"Вас выбрали для передержки по заявке #{foster_request.id}",
        data={"foster_request_id": foster_request.id, "offer_id": offer.id, "placement_id": placement.id},
        commit=True,
    )
    return placement


async def complete_placement(*, placement_id: int, user_id: int, db: AsyncSession) -> FosterPlacement:
    placement = await _get_placement_or_404(db, placement_id)
    foster_request = await _get_foster_request_or_404(db, placement.foster_request_id)
    if user_id not in {placement.volunteer_id, foster_request.owner_id}:
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    if placement.status != "active":
        raise HTTPException(status_code=400, detail="Передержка уже завершена или отменена")

    placement.status = "completed"
    foster_request.status = "closed"
    await db.commit()
    await db.refresh(placement)
    return placement


async def list_my_requests(*, owner_id: int, db: AsyncSession) -> list[FosterRequest]:
    q = select(FosterRequest).where(FosterRequest.owner_id == owner_id).order_by(FosterRequest.id.desc())
    return list((await db.scalars(q)).all())


async def get_my_request_by_id(*, request_id: int, owner_id: int, db: AsyncSession) -> FosterRequest:
    foster_request = await _get_foster_request_or_404(db, request_id)
    if foster_request.owner_id != owner_id:
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    return foster_request


async def list_available_requests(*, volunteer_id: int, db: AsyncSession) -> list[FosterRequest]:
    profile = await db.get(VolunteerProfile, volunteer_id)
    if profile is None or not profile.ready_for_foster:
        raise HTTPException(status_code=403, detail="Доступно только волонтёрам с ready_for_foster=true")
    q = select(FosterRequest).where(
        FosterRequest.status == "published",
        FosterRequest.owner_id != volunteer_id,
    ).order_by(FosterRequest.id.desc())
    return list((await db.scalars(q)).all())


async def list_my_offers(*, volunteer_id: int, db: AsyncSession) -> list[FosterOffer]:
    q = select(FosterOffer).where(FosterOffer.volunteer_id == volunteer_id).order_by(FosterOffer.id.desc())
    return list((await db.scalars(q)).all())

