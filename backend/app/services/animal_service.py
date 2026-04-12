from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.animal import Animal
from app.models.organization import OrganizationUser
from app.models.user import User
from app.schemas.animal import AnimalCreate, AnimalUpdate


async def create_animal(
        db: AsyncSession,
        payload: AnimalCreate,
        current_user: User,
) -> Animal:
    if payload.owner_type not in ("private", "organization"):
        raise HTTPException(status_code=400, detail="owner_type must be 'private' or 'organization'")

    if payload.owner_type == "private":
        if payload.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="Cannot create animal for another user")
    else:
        ou = await db.scalar(
            select(OrganizationUser).where(
                OrganizationUser.organization_id == payload.owner_id,
                OrganizationUser.user_id == current_user.id,
                OrganizationUser.role.in_(["admin", "curator"]),
                OrganizationUser.invitation_status == "accepted",
            )
        )
        if ou is None:
            raise HTTPException(status_code=403, detail="Insufficient permissions to create animal for organization")

    animal = Animal(**payload.model_dump())
    db.add(animal)
    await db.commit()
    await db.refresh(animal)
    return animal


async def get_animal(db: AsyncSession, animal_id: int) -> Animal:
    animal = await db.get(Animal, animal_id)
    if not animal:
        raise HTTPException(status_code=404, detail="Animal not found")
    return animal


async def update_animal(
        db: AsyncSession,
        animal_id: int,
        payload: AnimalUpdate,
        current_user: User,
) -> Animal:
    animal = await get_animal(db, animal_id)

    if animal.owner_type == "private" and animal.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    elif animal.owner_type == "organization":
        ou = await db.scalar(
            select(OrganizationUser).where(
                OrganizationUser.organization_id == animal.owner_id,
                OrganizationUser.user_id == current_user.id,
                OrganizationUser.role.in_(["admin", "curator"]),
                OrganizationUser.invitation_status == "accepted",
            )
        )
        if ou is None:
            raise HTTPException(status_code=403, detail="Insufficient permissions")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(animal, field, value)
    await db.commit()
    await db.refresh(animal)
    return animal


async def delete_animal(db: AsyncSession, animal_id: int, current_user: User):
    animal = await get_animal(db, animal_id)
    if animal.owner_type == "private" and animal.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    elif animal.owner_type == "organization":
        ou = await db.scalar(
            select(OrganizationUser).where(
                OrganizationUser.organization_id == animal.owner_id,
                OrganizationUser.user_id == current_user.id,
                OrganizationUser.role.in_(["admin", "curator"]),
                OrganizationUser.invitation_status == "accepted",
            )
        )
        if ou is None:
            raise HTTPException(status_code=403, detail="Insufficient permissions")

    await db.delete(animal)
    await db.commit()