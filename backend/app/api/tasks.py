from math import cos, radians
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core import get_current_user, get_db
from app.models import OrganizationUser, Task, User
from app.schemas.task import TaskCreate, TaskResponse, TaskUpdate
from app.services.feed_cache import invalidate_all_cached_feeds


router = APIRouter(prefix="/tasks", tags=["tasks"])


async def _get_task_or_404(db: AsyncSession, task_id: int) -> Task:
    task = await db.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    return task


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
    if ou is None or ou.invitation_status != "accepted" or ou.role not in roles:
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    return ou


@router.get("", response_model=list[TaskResponse])
async def list_tasks(
    organization_id: Optional[int] = None,
    status_filter: Optional[str] = None,
    urgency: Optional[str] = None,
    task_type: Optional[str] = None,
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    radius_km: Optional[float] = None,
    db: AsyncSession = Depends(get_db),
):
    """Публичная лента задач, фильтры опциональные"""
    q = select(Task).order_by(Task.id.desc())
    if organization_id is not None:
        q = q.where(Task.organization_id == organization_id)
    if status_filter is not None:
        q = q.where(Task.status == status_filter)
    if urgency is not None:
        q = q.where(Task.urgency == urgency)
    if task_type is not None:
        q = q.where(Task.task_type == task_type)

    # Геофильтр по радиусу
    if lat is not None or lng is not None or radius_km is not None:
        if lat is None or lng is None or radius_km is None:
            raise HTTPException(
                status_code=400,
                detail="Для фильтра по радиусу нужны параметры lat, lng и radius_km",
            )
        if radius_km <= 0:
            raise HTTPException(status_code=400, detail="radius_km должен быть > 0")

        lat_delta = radius_km / 110.574
        lng_delta = radius_km / (111.320 * max(cos(radians(lat)), 1e-6))

        q = q.where(Task.location_lat.is_not(None), Task.location_lng.is_not(None))
        q = q.where(Task.location_lat.between(lat - lat_delta, lat + lat_delta))
        q = q.where(Task.location_lng.between(lng - lng_delta, lng + lng_delta))
    tasks = (await db.scalars(q)).all()
    return [TaskResponse.model_validate(t) for t in tasks]


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: int, db: AsyncSession = Depends(get_db)):
    task = await _get_task_or_404(db, task_id)
    return TaskResponse.model_validate(task)


@router.post(
    "/organizations/{org_id}",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    openapi_extra={"security": [{"BearerAuth": []}]},
)
async def create_task(
    org_id: int,
    payload: TaskCreate,
    current: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    """Создать задачу от организации (админ/куратор)"""
    await _require_org_role(db, org_id=org_id, user_id=current.id, roles={"admin", "curator"})

    task = Task(
        organization_id=org_id,
        animal_id=payload.animal_id,
        created_by=current.id,
        title=payload.title,
        description=payload.description,
        task_type=payload.task_type,
        urgency=payload.urgency,
        location=payload.location,
        location_lat=payload.location_lat,
        location_lng=payload.location_lng,
        end_date=payload.end_date,
        scheduled_time=payload.scheduled_time,
        status="open",
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    # Инвалидируем кэш лент всех волонтёров, так как задача изменилась
    await invalidate_all_cached_feeds()
    return TaskResponse.model_validate(task)


@router.patch(
    "/{task_id}",
    response_model=TaskResponse,
    openapi_extra={"security": [{"BearerAuth": []}]},
)
async def update_task(
    task_id: int,
    payload: TaskUpdate,
    current: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    """Обновить задачу (админ/куратор)"""
    task = await _get_task_or_404(db, task_id)
    await _require_org_role(
        db,
        org_id=task.organization_id,
        user_id=current.id,
        roles={"admin", "curator"},
    )

    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(task, k, v)
    await db.commit()
    await db.refresh(task)
    # Инвалидируем кэш лент всех волонтёров, так как задача изменилась
    await invalidate_all_cached_feeds()
    return TaskResponse.model_validate(task)


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    openapi_extra={"security": [{"BearerAuth": []}]},
)
async def delete_task(
    task_id: int,
    current: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    """Удалить задачу (админ/куратор)"""
    task = await _get_task_or_404(db, task_id)
    await _require_org_role(
        db,
        org_id=task.organization_id,
        user_id=current.id,
        roles={"admin", "curator"},
    )
    await db.delete(task)
    await db.commit()
    # Инвалидируем кэш лент всех волонтёров, так как задача удалена
    await invalidate_all_cached_feeds()
    return None

