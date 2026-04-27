from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ArticleModerationItem(BaseModel):
    id: int
    title: str
    author_id: int
    content_preview: str
    created_at: datetime

    class Config:
        from_attributes = True


class ResolveArticleRequest(BaseModel):
    action: str
    rejection_reason: Optional[str] = None


class ReportModerationItem(BaseModel):
    id: int
    reporter_id: int
    target_type: str
    target_id: int
    reason: Optional[str]
    description: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class ResolveReportRequest(BaseModel):
    action: str