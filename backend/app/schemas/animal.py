from datetime import datetime
from typing import List, Literal, Optional
from pydantic import BaseModel, field_validator


AnimalGender = Literal["male", "female", "unknown"]
AnimalSize = Literal["small", "medium", "large", "extra_large"]
AnimalStatus = Literal["needs_home", "on_treatment", "on_adaptation", "adopted", "deceased"]


class AnimalBase(BaseModel):
    name: str
    description: Optional[str] = None
    species: Optional[str] = None
    breed: Optional[str] = None
    age: Optional[str] = None
    gender: Optional[AnimalGender] = None
    size: Optional[AnimalSize] = None
    character: Optional[str] = None
    health_status: Optional[str] = None
    special_needs: Optional[str] = None
    photos: List[str] = []

    @field_validator('age', mode='before')
    @classmethod
    def validate_age(cls, v):
        if isinstance(v, str) and v.strip() == "":
            return None
        return v


class AnimalCreate(AnimalBase):
    owner_type: Literal["private", "organization"]
    owner_id: int


class AnimalUpdate(BaseModel):
    name: Optional[str] = None
    species: Optional[str] = None
    breed: Optional[str] = None
    age: Optional[str] = None
    gender: Optional[AnimalGender] = None
    size: Optional[AnimalSize] = None
    character: Optional[str] = None
    health_status: Optional[str] = None
    special_needs: Optional[str] = None
    photos: Optional[List[str]] = None
    status: Optional[AnimalStatus] = None

    @field_validator('age', mode='before')
    @classmethod
    def validate_age_update(cls, v):
        if isinstance(v, str) and v.strip() == "":
            return None
        return v


class AnimalResponse(AnimalBase):
    id: int
    owner_type: Literal["private", "organization"]
    owner_id: int
    status: AnimalStatus
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True