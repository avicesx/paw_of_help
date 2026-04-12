"""API для профиля волонтёра."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import get_db, get_current_user
from app.models import User, Task
from app.schemas.volunteer import (
    VolunteerProfileUpdate, VolunteerProfileFullResponse, SkillResponse, SkillListResponse,
    SkillIdsRequest, TaskBriefResponse, CompletedTaskResponse, ReviewResponse
)
from app.services.volunteer_service import (
    get_or_create_profile, update_profile, deactivate_profile, get_volunteer_stats,
    get_active_tasks, get_completed_tasks, get_skills, get_my_skills, set_my_skills, delete_my_skill
)
from app.services.task_scorer import default_scorer
from app.services.feed_cache import get_cached_feed, set_cached_feed

router = APIRouter(prefix="/volunteer", tags=["volunteer"])


@router.get(
    "/profile",
    response_model=VolunteerProfileFullResponse,
    summary="Получить профиль волонтёра",
    description="Возвращает профиль текущего авторизованного волонтёра с вычисляемой статистикой (количество завершённых задач, рейтинг, часы, достижения). Если профиль не существует, создаёт пустой.",
    openapi_extra={"security": [{"BearerAuth": []}]}
)
async def get_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получить профиль волонтёра с статистикой."""
    profile = await get_or_create_profile(current_user.id, db)
    stats = await get_volunteer_stats(current_user.id, db)
    return VolunteerProfileFullResponse(**profile.__dict__, stats=stats)


@router.patch(
    "/profile",
    response_model=VolunteerProfileFullResponse,
    summary="Обновить профиль волонтёра",
    description="Обновляет поля профиля волонтёра (локация, радиус, доступность, предпочтения и т.д.). Возвращает обновлённый профиль с статистикой.",
    openapi_extra={"security": [{"BearerAuth": []}]}
)
async def update_volunteer_profile(
    data: VolunteerProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Обновить профиль волонтёра."""
    profile = await update_profile(current_user.id, data.model_dump(exclude_unset=True), db)
    stats = await get_volunteer_stats(current_user.id, db)
    return VolunteerProfileFullResponse(**profile.__dict__, stats=stats)


@router.delete(
    "/profile",
    summary="Деактивировать профиль волонтёра",
    description="Деактивирует аккаунт волонтёра, устанавливая is_active = False. Профиль остаётся в базе, но доступ к системе блокируется.",
    openapi_extra={"security": [{"BearerAuth": []}]}
)
async def deactivate_volunteer_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Деактивировать профиль волонтёра."""
    await deactivate_profile(current_user.id, db)
    return {"message": "Профиль деактивирован"}


@router.get(
    "/skills",
    response_model=SkillListResponse,
    summary="Получить список навыков",
    description="Возвращает полный список доступных навыков волонтёра (экстренная помощь, транспортировка и т.д.) с их описаниями."
)
async def list_skills(db: AsyncSession = Depends(get_db)):
    """Получить список всех навыков."""
    skills = await get_skills(db)
    return SkillListResponse(skills=skills)


@router.get(
    "/my-skills",
    response_model=List[int],
    summary="Получить навыки волонтёра",
    description="Возвращает список ID навыков, выбранных текущим авторизованным волонтёром.",
    openapi_extra={"security": [{"BearerAuth": []}]}
)
async def get_my_skills_endpoint(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получить навыки волонтёра."""
    return await get_my_skills(current_user.id, db)


@router.post(
    "/my-skills",
    summary="Установить навыки волонтёра",
    description="Заменяет набор навыков волонтёра на новый список. Удаляет старые навыки и добавляет новые.",
    openapi_extra={"security": [{"BearerAuth": []}]}
)
async def set_my_skills_endpoint(
    data: SkillIdsRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Установить навыки волонтёра."""
    await set_my_skills(current_user.id, data.skill_ids, db)
    return {"message": "Навыки обновлены"}


@router.delete(
    "/my-skills/{skill_id}",
    summary="Удалить навык волонтёра",
    description="Удаляет указанный навык из списка навыков текущего авторизованного волонтёра.",
    openapi_extra={"security": [{"BearerAuth": []}]}
)
async def delete_my_skill_endpoint(
    skill_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Удалить навык волонтёра."""
    await delete_my_skill(current_user.id, skill_id, db)
    return {"message": "Навык удалён"}


@router.get(
    "/tasks",
    response_model=List[TaskBriefResponse],
    summary="Получить задачи волонтёра",
    description="Возвращает список задач волонтёра. По умолчанию активные задачи (в работе) или завершённые. Без ранжирования рекомендациями.",
    openapi_extra={"security": [{"BearerAuth": []}]}
)
async def get_volunteer_tasks(
    status: Optional[str] = "active",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получить задачи волонтёра."""
    if status == "active" or status is None:
        tasks = await get_active_tasks(current_user.id, db)
        return [TaskBriefResponse(
            id=task.id,
            title=task.title,
            description=task.description,
            status=task.status,
            created_at=task.created_at,
            end_date=task.end_date,
            author_id=task.created_by
        ) for task in tasks]
    elif status == "completed":
        task_reviews = await get_completed_tasks(current_user.id, db)
        result = []
        for item in task_reviews:
            task = item["task"]
            review = item["review"]
            review_resp = None
            if review:
                review_resp = ReviewResponse(
                    id=review.id,
                    reviewer_id=review.reviewer_id,
                    rating=review.rating,
                    comment=review.comment,
                    created_at=review.created_at
                )
            result.append(CompletedTaskResponse(
                id=task.id,
                title=task.title,
                description=task.description,
                status=task.status,
                created_at=task.created_at,
                end_date=task.end_date,
                author_id=task.created_by,
                completed_at=task.updated_at,  # предположим, что updated_at при завершении
                review=review_resp
            ))
        return result
    else:
        raise HTTPException(status_code=400, detail="Неверный статус")


@router.get(
    "/feed",
    response_model=List[TaskBriefResponse],
    summary="Получить рекомендованные задачи",
    description="Возвращает список открытых задач, отсортированных по рекомендациям для текущего волонтёра (срочность, навыки, расстояние, доступность).",
    openapi_extra={"security": [{"BearerAuth": []}]}
)
async def get_volunteer_feed(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получить рекомендованные задачи волонтёра."""
    await get_or_create_profile(current_user.id, db)
    cached_feed = await get_cached_feed(current_user.id)
    if cached_feed is not None:
        return cached_feed

    tasks = await default_scorer.get_feed(current_user.id, db)
    result = [TaskBriefResponse(
        id=task.id,
        title=task.title,
        description=task.description,
        status=task.status,
        created_at=task.created_at,
        end_date=task.end_date,
        author_id=task.created_by
    ) for task in tasks]

    background_tasks.add_task(set_cached_feed, current_user.id, result)
    return result