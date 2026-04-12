from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import get_current_user, get_db
from app.models.user import User
from app.schemas.animal import AnimalCreate, AnimalUpdate, AnimalResponse
from app.services.animal import (
    create_animal as create_animal_service,
    get_animal as get_animal_service,
    update_animal as update_animal_service,
    delete_animal as delete_animal_service,
)

router = APIRouter(prefix="/animals", tags=["animals"])


@router.get("", response_model=list[AnimalResponse])
async def list_animals(db: AsyncSession = Depends(get_db)):
    """Получить список всех животных (публичный)."""
    from app.models.animal import Animal
    animals = (await db.scalars(
        select(Animal).order_by(Animal.id.desc())
    )).all()
    return [AnimalResponse.model_validate(a) for a in animals]


@router.get("/{animal_id}", response_model=AnimalResponse)
async def get_animal(animal_id: int, db: AsyncSession = Depends(get_db)):
    """Получить карточку животного (публичный доступ)."""
    animal = await get_animal_service(db, animal_id)
    return AnimalResponse.model_validate(animal)


@router.post(
    "",
    response_model=AnimalResponse,
    status_code=status.HTTP_201_CREATED,
    openapi_extra={"security": [{"BearerAuth": []}]},
)
async def create_animal(
    payload: AnimalCreate,
    current: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    """Создать карточку животного (только владелец или админ/куратор организации)."""
    animal = await create_animal_service(db, payload, current)
    return AnimalResponse.model_validate(animal)


@router.patch(
    "/{animal_id}",
    response_model=AnimalResponse,
    openapi_extra={"security": [{"BearerAuth": []}]},
)
async def update_animal(
    animal_id: int,
    payload: AnimalUpdate,
    current: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    """Обновить карточку животного (только владелец или админ/куратор организации)."""
    animal = await update_animal_service(db, animal_id, payload, current)
    return AnimalResponse.model_validate(animal)


@router.delete(
    "/{animal_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    openapi_extra={"security": [{"BearerAuth": []}]},
)
async def delete_animal(
    animal_id: int,
    current: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    """Удалить карточку животного (только владелец или админ/куратор организации)."""
    await delete_animal_service(db, animal_id, current)