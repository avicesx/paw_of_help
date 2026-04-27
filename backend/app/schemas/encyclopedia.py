from pydantic import BaseModel
from typing import Optional


class SpeciesResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None

    class Config:
        from_attributes = True


class BreedResponse(BaseModel):
    id: int
    name: str
    description_short: Optional[str] = None

    class Config:
        from_attributes = True


class BreedDetailResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    common_diseases: Optional[str] = None
    feeding_tips: Optional[str] = None
    socialization_tips: Optional[str] = None
    image_url: Optional[str] = None

    class Config:
        from_attributes = True