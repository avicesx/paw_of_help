from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel


class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    task_type: Optional[str] = None
    urgency: str = "normal"
    location: Optional[str] = None
    location_lat: Optional[float] = None
    location_lng: Optional[float] = None
    end_date: Optional[datetime] = None
    scheduled_time: Optional[Dict[str, Any]] = None
    animal_id: Optional[int] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    task_type: Optional[str] = None
    urgency: Optional[str] = None
    location: Optional[str] = None
    location_lat: Optional[float] = None
    location_lng: Optional[float] = None
    end_date: Optional[datetime] = None
    status: Optional[str] = None


class TaskResponse(BaseModel):
    id: int
    organization_id: int
    animal_id: Optional[int] = None
    created_by: int
    title: str
    description: Optional[str] = None
    task_type: Optional[str] = None
    urgency: str
    location: Optional[str] = None
    location_lat: Optional[float] = None
    location_lng: Optional[float] = None
    end_date: Optional[datetime] = None
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TaskResponseCreate(BaseModel):
    message: Optional[str] = None


class TaskResponseUpdate(BaseModel):
    status: str


class TaskResponseResponse(BaseModel):
    id: int
    task_id: int
    volunteer_id: int
    status: str
    message: Optional[str] = None
    responded_at: datetime

    class Config:
        from_attributes = True


class TaskCompletionReportCreate(BaseModel):
    hours_spent: Optional[int] = None
    comment: Optional[str] = None
    photos: Optional[list[str]] = None


class TaskCompletionReportUpdate(BaseModel):
    status: Optional[str] = None
    hours_spent: Optional[int] = None
    comment: Optional[str] = None
    photos: Optional[list[str]] = None


class TaskCompletionReportResponse(BaseModel):
    id: int
    task_id: int
    volunteer_id: int
    status: str
    hours_spent: Optional[int] = None
    comment: Optional[str] = None
    photos: list[str]
    submitted_at: datetime
    reviewed_by: Optional[int] = None
    reviewed_at: Optional[datetime] = None

    class Config:
        from_attributes = True