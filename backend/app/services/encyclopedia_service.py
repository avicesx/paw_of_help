from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.encyclopedia import Breed, BreedCard
from app.models.animal_species import AnimalSpecies


async def get_all_species(db: AsyncSession) -> list[AnimalSpecies]:
    result = await db.scalars(select(AnimalSpecies))
    return result.all()


async def get_breeds_by_species(db: AsyncSession, species_id: int) -> list[Breed]:
    result = await db.scalars(
        select(Breed).where(Breed.species_id == species_id)
    )
    return result.all()


async def get_breed_detail(db: AsyncSession, breed_id: int) -> BreedCard | None:
    breed_card = await db.get(BreedCard, breed_id)
    return breed_card