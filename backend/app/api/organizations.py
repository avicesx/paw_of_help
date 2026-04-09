from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core import get_current_user, get_db
from app.models import Notification, Organization, OrganizationUser, User
from app.schemas.organization import (
    InviteUserRequest,
    OrganizationCreate,
    OrganizationResponse,
    OrganizationUpdate,
    OrganizationUserResponse,
)


router = APIRouter(prefix="/organizations", tags=["organizations"])


async def _get_user_by_username(db: AsyncSession, username: str) -> User | None:
    raw = (username or "").strip()
    if not raw:
        return None
    return await db.scalar(select(User).where(User.username == raw))


async def _get_org_or_404(db: AsyncSession, org_id: int) -> Organization:
    org = await db.get(Organization, org_id)
    if org is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Организация не найдена")
    return org


async def _require_org_role(
    db: AsyncSession,
    org_id: int,
    user_id: int,
    roles: set[str],
) -> OrganizationUser:
    ou = await db.scalar(
        select(OrganizationUser).where(
            OrganizationUser.organization_id == org_id,
            OrganizationUser.user_id == user_id,
        )
    )
    if ou is None or ou.role not in roles or ou.invitation_status != "accepted":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав")
    return ou


@router.get("", response_model=list[OrganizationResponse])
async def list_organizations(db: AsyncSession = Depends(get_db)):
    """Публичный каталог организаций."""
    orgs = (await db.scalars(select(Organization).order_by(Organization.id.desc()))).all()
    return [OrganizationResponse.model_validate(o) for o in orgs]


@router.get("/{org_id}", response_model=OrganizationResponse)
async def get_organization(org_id: int, db: AsyncSession = Depends(get_db)):
    org = await _get_org_or_404(db, org_id)
    return OrganizationResponse.model_validate(org)


@router.post(
    "",
    response_model=OrganizationResponse,
    status_code=status.HTTP_201_CREATED,
    openapi_extra={"security": [{"BearerAuth": []}]},
)
async def create_organization(
    payload: OrganizationCreate,
    current: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    """Создать заявку на организацию. Статус верификации всегда pending до модерации."""
    org = Organization(
        name=payload.name,
        description=payload.description,
        inn=payload.inn,
        address=payload.address,
        address_lat=payload.address_lat,
        address_lng=payload.address_lng,
        address_components=payload.address_components,
        contacts=payload.contacts,
        documents=payload.documents,
        logo_url=payload.logo_url,
        photos=payload.photos,
        created_by=current.id,
        status="pending",
    )
    db.add(org)
    await db.commit()
    await db.refresh(org)

    db.add(
        OrganizationUser(
            organization_id=org.id,
            user_id=current.id,
            role="admin",
            invitation_status="accepted",
            invited_by=None,
        )
    )
    await db.commit()

    return OrganizationResponse.model_validate(org)


@router.patch(
    "/{org_id}",
    response_model=OrganizationResponse,
    openapi_extra={"security": [{"BearerAuth": []}]},
)
async def update_organization(
    org_id: int,
    payload: OrganizationUpdate,
    current: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    """Обновить профиль организации. Админ организации — все поля из схемы; куратор — только logo_url и photos."""
    org = await _get_org_or_404(db, org_id)
    ou = await _require_org_role(
        db, org_id=org_id, user_id=current.id, roles={"admin", "curator"}
    )

    data = payload.model_dump(exclude_unset=True)
    if ou.role == "curator":
        allowed = {"logo_url", "photos"}
        extra = set(data.keys()) - allowed
        if extra:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Куратор может менять только logo_url и photos",
            )
    for k, v in data.items():
        setattr(org, k, v)
    await db.commit()
    await db.refresh(org)
    return OrganizationResponse.model_validate(org)


@router.get(
    "/{org_id}/users",
    response_model=list[OrganizationUserResponse],
    openapi_extra={"security": [{"BearerAuth": []}]},
)
async def list_org_users(
    org_id: int,
    current: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    """Список сотрудников (админы, кураторы)"""
    await _get_org_or_404(db, org_id)
    await _require_org_role(db, org_id=org_id, user_id=current.id, roles={"admin", "curator"})

    rows = (
        await db.scalars(select(OrganizationUser).where(OrganizationUser.organization_id == org_id))
    ).all()
    return [OrganizationUserResponse.model_validate(r) for r in rows]


@router.post(
    "/{org_id}/invite",
    response_model=OrganizationUserResponse,
    status_code=status.HTTP_201_CREATED,
    openapi_extra={"security": [{"BearerAuth": []}]},
)
async def invite_user(
    org_id: int,
    payload: InviteUserRequest,
    current: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    """Пригласить пользователя по username (только админ)"""
    await _get_org_or_404(db, org_id)
    await _require_org_role(db, org_id=org_id, user_id=current.id, roles={"admin"})

    if payload.role not in {"admin", "curator"}:
        raise HTTPException(status_code=400, detail="Неверная роль")

    user = await _get_user_by_username(db, payload.username)
    if user is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    existing = await db.scalar(
        select(OrganizationUser).where(
            OrganizationUser.organization_id == org_id,
            OrganizationUser.user_id == user.id,
        )
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Пользователь уже в организации")

    ou = OrganizationUser(
        organization_id=org_id,
        user_id=user.id,
        role=payload.role,
        invitation_status="pending",
        invited_by=current.id,
    )
    db.add(ou)
    await db.commit()
    await db.refresh(ou)

    db.add(
        Notification(
            user_id=user.id,
            type="organization_invite",
            title="Приглашение в организацию",
            body=f"Вас пригласили в организацию «{org.name}» с ролью {payload.role}.",
            data={"organization_id": org_id, "role": payload.role},
        )
    )
    await db.commit()
    return OrganizationUserResponse.model_validate(ou)