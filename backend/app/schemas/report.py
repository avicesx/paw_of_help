from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ReportCreate(BaseModel):
    target_type: str
    target_id: int
    reason: Optional[str] = None
    description: Optional[str] = None


class ReportResponse(BaseModel):
    id: int
    reporter_id: int
    target_type: str
    target_id: int
    reason: Optional[str]
    description: Optional[str]
    status: str
    moderator_id: Optional[int] = None
    moderation_comment: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True