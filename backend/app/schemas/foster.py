from datetime import date, datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel


class FosterRequestCreate(BaseModel):
    animal_id: int
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    dates_flexible: bool = False
    pickup_location: Optional[str] = None
    pickup_lat: Optional[float] = None
    pickup_lng: Optional[float] = None
    return_location: Optional[str] = None
    return_lat: Optional[float] = None
    return_lng: Optional[float] = None
    owner_provides: Dict[str, Any] = {}


class FosterRequestUpdate(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    dates_flexible: Optional[bool] = None
    pickup_location: Optional[str] = None
    pickup_lat: Optional[float] = None
    pickup_lng: Optional[float] = None
    return_location: Optional[str] = None
    return_lat: Optional[float] = None
    return_lng: Optional[float] = None
    owner_provides: Optional[Dict[str, Any]] = None
    status: Optional[str] = None
    published_at: Optional[datetime] = None


class FosterRequestResponse(FosterRequestCreate):
    id: int
    owner_id: int
    status: str
    published_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class FosterOfferCreate(BaseModel):
    message: Optional[str] = None
    proposed_start_date: Optional[date] = None
    proposed_end_date: Optional[date] = None


class FosterOfferResponse(BaseModel):
    id: int
    foster_request_id: int
    volunteer_id: int
    status: str
    message: Optional[str] = None
    proposed_start_date: Optional[date] = None
    proposed_end_date: Optional[date] = None
    created_at: datetime

    class Config:
        from_attributes = True


class FosterPlacementResponse(BaseModel):
    id: int
    foster_request_id: int
    volunteer_id: int
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class FosterVolunteerMatchResponse(BaseModel):
    id: int
    name: Optional[str] = None
    rating: float = 0.0
    distance: Optional[float] = None
    match_score: float