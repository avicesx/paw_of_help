from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class AnimalBase(BaseModel):
    name: str
    species: Optional[str] = None
    breed: Optional[str] = None
    age: Optional[str] = None
    gender: Optional[str] = None
    size: Optional[str] = None
    character: Optional[str] = None
    health_status: Optional[str] = None
    special_needs: Optional[str] = None
    photos: List[str] = []


class AnimalCreate(AnimalBase):
    owner_type: str
    owner_id: int


class AnimalUpdate(BaseModel):
    name: Optional[str] = None
    species: Optional[str] = None
    breed: Optional[str] = None
    age: Optional[str] = None
    gender: Optional[str] = None
    size: Optional[str] = None
    character: Optional[str] = None
    health_status: Optional[str] = None
    special_needs: Optional[str] = None
    photos: Optional[List[str]] = None
    status: Optional[str] = None


class AnimalResponse(AnimalBase):
    id: int
    owner_type: str
    owner_id: int
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True