from typing import Optional
from pydantic import BaseModel


class AnimalSpeciesCreate(BaseModel):
    code: str
    name: str
    description: Optional[str] = None


class AnimalSpeciesResponse(AnimalSpeciesCreate):
    id: int

    class Config:
        from_attributes = True

