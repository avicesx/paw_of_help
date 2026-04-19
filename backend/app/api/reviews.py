from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core import get_current_user, get_db
from app.models import User
from app.schemas import ReviewCreateRequest, ReviewResponse
from app.schemas.reviews import ReviewTargetType
from app.services import create_review, list_reviews

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.post(
    "",
    response_model=ReviewResponse,
    summary="Оставить отзыв",
    openapi_extra={"security": [{"BearerAuth": []}]},
)
async def post_review(
    payload: ReviewCreateRequest,
    current: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    review = await create_review(reviewer_id=current.id, payload=payload, db=db)
    return ReviewResponse.model_validate(review)


@router.get(
    "",
    response_model=list[ReviewResponse],
    summary="Список отзывов по сущности",
)
async def get_reviews(
    target_type: ReviewTargetType,
    target_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    reviews = await list_reviews(target_type=target_type, target_id=target_id, db=db)
    return [ReviewResponse.model_validate(r) for r in reviews]

