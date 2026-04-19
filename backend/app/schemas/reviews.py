from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field


ReviewTargetType = Literal["volunteer", "organization", "task", "foster_request"]


class ReviewCreateRequest(BaseModel):
    """создание отзыва. reviewer берётся из токена"""

    reviewee_id: int
    target_type: ReviewTargetType
    target_id: int
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = Field(default=None, max_length=2000)


class ReviewResponse(BaseModel):
    id: int
    reviewer_id: int
    reviewee_id: int
    target_type: ReviewTargetType
    target_id: int
    rating: int
    comment: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

