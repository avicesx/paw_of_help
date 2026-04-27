from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import get_current_user, get_db
from app.schemas.encyclopedia import SpeciesResponse, BreedResponse, BreedDetailResponse
from app.services.encyclopedia_service import get_all_species, get_breeds_by_species, get_breed_detail

router = APIRouter(prefix="/encyclopedia", tags=["encyclopedia"])


@router.get("/categories", response_model=List[SpeciesResponse])
async def list_species(db: AsyncSession = Depends(get_db)):
    species = await get_all_species(db)
    return species


@router.get("/breeds/{species_id}", response_model=List[BreedResponse])
async def list_breeds(species_id: int, db: AsyncSession = Depends(get_db)):
    breeds = await get_breeds_by_species(db, species_id)
    return breeds


@router.get("/breed/{breed_id}", response_model=BreedDetailResponse)
async def get_breed_detail(breed_id: int, db: AsyncSession = Depends(get_db)):
    card = await get_breed_detail(db, breed_id)
    if not card:
        raise HTTPException(status_code=404, detail="Карточка породы не найдена")
    return card