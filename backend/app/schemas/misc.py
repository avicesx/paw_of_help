from datetime import datetime
from typing import Any, Dict, Optional
 
from pydantic import BaseModel
 
 
# отзывы
 
class ReviewCreate(BaseModel):
    reviewee_id: int
    target_type: str
    target_id: int
    rating: int
    comment: Optional[str] = None


class ReviewResponse(ReviewCreate):
    id: int
    reviewer_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# жалобы

class ReportCreate(BaseModel):
    target_type: str
    target_id: int
    reason: Optional[str] = None
    description: Optional[str] = None


class ReportResponse(ReportCreate):
    id: int
    reporter_id: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
 
 
# находки животных
 
class SightingCreate(BaseModel):
    location: Optional[str] = None
    last_seen_at: Optional[datetime] = None
    photos: list = []
    description: Optional[str] = None


class SightingResponse(SightingCreate):
    id: int
    user_id: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


# тикеты поддержки

class SupportTicketCreate(BaseModel):
    subject: str
    body: str
    related_entity_type: Optional[str] = None
    related_entity_id: Optional[int] = None


class SupportTicketResponse(SupportTicketCreate):
    id: int
    user_id: int
    status: str
    priority: str
    assigned_to: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SupportTicketMessageCreate(BaseModel):
    body: str


class SupportTicketMessageResponse(BaseModel):
    id: int
    ticket_id: int
    sender_id: int
    body: str
    is_staff: bool
    created_at: datetime

    class Config:
        from_attributes = True
 
 
# ачивки
 
class AchievementResponse(BaseModel):
    id: int
    code: str
    title: str
    description: Optional[str] = None
    icon: Optional[str] = None

    class Config:
        from_attributes = True


class UserAchievementResponse(BaseModel):
    id: int
    user_id: int
    achievement_id: int
    earned_at: datetime
    achievement: Optional[AchievementResponse] = None

    class Config:
        from_attributes = True