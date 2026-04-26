from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import get_current_user, get_db
from app.models import User
from app.schemas.foster import (
    FosterOfferCreate,
    FosterOfferResponse,
    FosterPlacementResponse,
    FosterRequestCreate,
    FosterRequestResponse,
    FosterRequestUpdate,
    FosterVolunteerMatchResponse,
)
from app.services.foster_service import (
    accept_offer,
    complete_placement,
    create_foster_request,
    create_offer,
    get_my_request_by_id,
    list_available_requests,
    list_my_offers,
    list_my_requests,
    match_volunteers,
    publish_request,
    update_foster_request,
    update_offer_status,
)

router = APIRouter(prefix="/foster", tags=["foster"])


@router.post(
    "/requests",
    response_model=FosterRequestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать заявку на передержку",
    openapi_extra={"security": [{"BearerAuth": []}]},
)
async def create_request(
    payload: FosterRequestCreate,
    current: Annotated[User, Depends(get_current_user)],
    publish: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
):
    foster_request = await create_foster_request(
        owner_id=current.id,
        payload=payload,
        db=db,
        publish_now=publish,
    )
    return FosterRequestResponse.model_validate(foster_request)


@router.get(
    "/requests/my",
    response_model=list[FosterRequestResponse],
    summary="Мои заявки на передержку",
    openapi_extra={"security": [{"BearerAuth": []}]},
)
async def get_my_requests(
    current: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    rows = await list_my_requests(owner_id=current.id, db=db)
    return [FosterRequestResponse.model_validate(item) for item in rows]


@router.get(
    "/requests/{request_id}",
    response_model=FosterRequestResponse,
    summary="Получить свою заявку",
    openapi_extra={"security": [{"BearerAuth": []}]},
)
async def get_request(
    request_id: int,
    current: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    foster_request = await get_my_request_by_id(request_id=request_id, owner_id=current.id, db=db)
    return FosterRequestResponse.model_validate(foster_request)


@router.patch(
    "/requests/{request_id}",
    response_model=FosterRequestResponse,
    summary="Обновить свою заявку",
    openapi_extra={"security": [{"BearerAuth": []}]},
)
async def patch_request(
    request_id: int,
    payload: FosterRequestUpdate,
    current: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    foster_request = await update_foster_request(
        request_id=request_id,
        owner_id=current.id,
        payload=payload,
        db=db,
    )
    return FosterRequestResponse.model_validate(foster_request)


@router.post(
    "/requests/{request_id}/publish",
    response_model=FosterRequestResponse,
    summary="Опубликовать заявку",
    openapi_extra={"security": [{"BearerAuth": []}]},
)
async def post_publish_request(
    request_id: int,
    current: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    foster_request = await publish_request(request_id=request_id, owner_id=current.id, db=db)
    return FosterRequestResponse.model_validate(foster_request)


@router.get(
    "/requests/{request_id}/matches",
    response_model=list[FosterVolunteerMatchResponse],
    summary="Подобрать волонтёров для заявки",
    openapi_extra={"security": [{"BearerAuth": []}]},
)
async def get_request_matches(
    request_id: int,
    current: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    await get_my_request_by_id(request_id=request_id, owner_id=current.id, db=db)
    return await match_volunteers(request_id=request_id, db=db)


@router.post(
    "/requests/{request_id}/accept-offer/{offer_id}",
    response_model=FosterPlacementResponse,
    summary="Принять отклик волонтёра",
    openapi_extra={"security": [{"BearerAuth": []}]},
)
async def post_accept_offer(
    request_id: int,
    offer_id: int,
    current: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    placement = await accept_offer(request_id=request_id, offer_id=offer_id, owner=current, db=db)
    return FosterPlacementResponse.model_validate(placement)


@router.get(
    "/available",
    response_model=list[FosterRequestResponse],
    summary="Доступные заявки для волонтёра",
    openapi_extra={"security": [{"BearerAuth": []}]},
)
async def get_available_requests(
    current: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    rows = await list_available_requests(volunteer_id=current.id, db=db)
    return [FosterRequestResponse.model_validate(item) for item in rows]


@router.post(
    "/requests/{request_id}/offer",
    response_model=FosterOfferResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Откликнуться на заявку",
    openapi_extra={"security": [{"BearerAuth": []}]},
)
async def post_offer(
    request_id: int,
    payload: FosterOfferCreate,
    current: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    offer = await create_offer(
        request_id=request_id,
        volunteer_id=current.id,
        payload=payload,
        db=db,
    )
    return FosterOfferResponse.model_validate(offer)


@router.get(
    "/my-offers",
    response_model=list[FosterOfferResponse],
    summary="Мои отклики на передержку",
    openapi_extra={"security": [{"BearerAuth": []}]},
)
async def get_my_offers(
    current: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    rows = await list_my_offers(volunteer_id=current.id, db=db)
    return [FosterOfferResponse.model_validate(item) for item in rows]


@router.patch(
    "/offers/{offer_id}",
    response_model=FosterOfferResponse,
    summary="Изменить статус своего отклика",
    openapi_extra={"security": [{"BearerAuth": []}]},
)
async def patch_offer(
    offer_id: int,
    current: Annotated[User, Depends(get_current_user)],
    status_value: str = Query(..., alias="status"),
    db: AsyncSession = Depends(get_db),
):
    offer = await update_offer_status(
        offer_id=offer_id,
        volunteer_id=current.id,
        new_status=status_value,
        db=db,
    )
    return FosterOfferResponse.model_validate(offer)


@router.post(
    "/placements/{placement_id}/complete",
    response_model=FosterPlacementResponse,
    summary="Завершить передержку",
    openapi_extra={"security": [{"BearerAuth": []}]},
)
async def post_complete_placement(
    placement_id: int,
    current: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    placement = await complete_placement(placement_id=placement_id, user_id=current.id, db=db)
    return FosterPlacementResponse.model_validate(placement)
