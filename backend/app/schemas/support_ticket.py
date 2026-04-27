from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class SupportTicketCreate(BaseModel):
    subject: str
    body: str
    related_entity_type: Optional[str] = None
    related_entity_id: Optional[int] = None


class SupportTicketResponse(BaseModel):
    id: int
    user_id: int
    subject: str
    body: str
    status: str
    priority: str
    assigned_to: Optional[int] = None
    related_entity_type: Optional[str] = None
    related_entity_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SupportTicketListResponse(BaseModel):
    id: int
    subject: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True