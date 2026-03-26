from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class VolunteerProfileCreate(BaseModel):
    location: Optional[str] = None
    location_lat: Optional[float] = None
    location_lng: Optional[float] = None
    radius_km: Optional[int] = None
    availability: Dict[str, Any] = {}
    preferred_animal_types: List[str] = []
    ready_for_foster: bool = False
    housing_type: Optional[str] = None
    has_other_pets: Dict[str, Any] = {}
    has_children: bool = False
    foster_restrictions: Optional[str] = None
    foster_photos: List[str] = []


class VolunteerProfileUpdate(BaseModel):
    location: Optional[str] = None
    location_lat: Optional[float] = None
    location_lng: Optional[float] = None
    radius_km: Optional[int] = None
    availability: Optional[Dict[str, Any]] = None
    preferred_animal_types: Optional[List[str]] = None
    ready_for_foster: Optional[bool] = None
    housing_type: Optional[str] = None
    has_other_pets: Optional[Dict[str, Any]] = None
    has_children: Optional[bool] = None
    foster_restrictions: Optional[str] = None
    foster_photos: Optional[List[str]] = None


class VolunteerProfileResponse(VolunteerProfileCreate):
    user_id: int

    class Config:
        from_attributes = True


class SkillResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None

    class Config:
        from_attributes = True


class VolunteerSkillCreate(BaseModel):
    skill_id: int
    level: Optional[str] = None


class VolunteerSkillResponse(BaseModel):
    user_id: int
    skill_id: int
    level: Optional[str] = None

    class Config:
        from_attributes = True