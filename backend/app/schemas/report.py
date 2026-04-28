from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Literal


ReportTargetType = Literal["user", "organization", "task", "review", "post", "comment", "article"]
ReportReasonTargetType = Literal["user", "organization", "article", "post", "comment"]


class ReportCreate(BaseModel):
    target_type: ReportTargetType
    target_id: int
    reason_code: str
    description: Optional[str] = None


class ReportResponse(BaseModel):
    id: int
    reporter_id: int
    target_type: ReportTargetType
    target_id: int
    reason_code: Optional[str] = None
    reason: Optional[str]
    description: Optional[str]
    status: str
    moderator_id: Optional[int] = None
    moderation_comment: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ReportReasonResponse(BaseModel):
    id: int
    target_type: ReportReasonTargetType
    code: str
    title: str
    is_active: bool
    sort_order: int

    class Config:
        from_attributes = True