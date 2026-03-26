from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel


# мероприятия

class EventCreate(BaseModel):
    title: str
    description: Optional[str] = None
    event_type: Optional[str] = None
    start_datetime: Optional[datetime] = None
    end_datetime: Optional[datetime] = None
    location: Optional[str] = None


class EventResponse(EventCreate):
    id: int
    organization_id: int
    created_by: int
    created_at: datetime

    class Config:
        from_attributes = True


class EventParticipantResponse(BaseModel):
    event_id: int
    user_id: int
    status: str
    registered_at: datetime
 
    class Config:
        from_attributes = True


# уведомления

class NotificationResponse(BaseModel):
    id: int
    type: str
    title: Optional[str] = None
    body: Optional[str] = None
    data: Dict[str, Any] = {}
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


# чат

class ChatResponse(BaseModel):
    id: int
    context_type: str
    context_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ChatMessageCreate(BaseModel):
    content: str
    message_type: str = "text"


class ChatMessageResponse(BaseModel):
    id: int
    chat_id: int
    sender_id: int
    message_type: str
    content: Optional[str] = None
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True