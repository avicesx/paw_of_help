"""Сервисы для работы с профилем волонтёра."""

from typing import List, Optional
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models import (
    VolunteerProfile, Skill, VolunteerSkill, Task, TaskResponse, Review,
    Achievement, UserAchievement, TaskCompletionReport, User
)


async def get_or_create_profile(user_id: int, db: AsyncSession) -> VolunteerProfile:
    """Возвращает профиль волонтёра, если есть, иначе создаёт пустой."""
    profile = await db.scalar(select(VolunteerProfile).where(VolunteerProfile.user_id == user_id))
    if not profile:
        profile = VolunteerProfile(user_id=user_id)
        db.add(profile)
        await db.commit()
        await db.refresh(profile)
    return profile


async def update_profile(user_id: int, data: dict, db: AsyncSession) -> VolunteerProfile:
    """Обновляет поля профиля волонтёра."""
    profile = await get_or_create_profile(user_id, db)
    for key, value in data.items():
        if hasattr(profile, key) and value is not None:
            setattr(profile, key, value)
    await db.commit()
    await db.refresh(profile)
    return profile


async def deactivate_profile(user_id: int, db: AsyncSession):
    """Деактивирует профиль пользователя."""
    user = await db.scalar(select(User).where(User.id == user_id))
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    user.is_active = False
    await db.commit()


async def get_volunteer_stats(user_id: int, db: AsyncSession) -> dict:
    """Вычисляет статистику волонтёра."""
    # total_completed_tasks: задачи с accepted откликом и status='done'
    completed_tasks_query = select(func.count(Task.id)).join(
        TaskResponse, and_(TaskResponse.task_id == Task.id, TaskResponse.volunteer_id == user_id, TaskResponse.status == 'accepted')
    ).where(Task.status == 'done')
    total_completed_tasks = await db.scalar(completed_tasks_query) or 0

    # rating_by_reviews: средний рейтинг из отзывов с reviewee_id=user_id
    reviews_query = select(func.avg(Review.rating), func.count(Review.id)).where(
        and_(Review.reviewee_id == user_id, Review.target_type == 'volunteer')
    )
    result = await db.execute(reviews_query)
    avg_rating, count_reviews = result.first() or (0.0, 0)
    rating_by_reviews = float(avg_rating) if avg_rating else 0.0
    total_reviews_count = count_reviews

    # volunteer_hours: сумма часов из TaskCompletionReport для завершённых задач
    hours_query = select(func.sum(TaskCompletionReport.hours_spent)).join(
        Task, Task.id == TaskCompletionReport.task_id
    ).where(
        and_(TaskCompletionReport.volunteer_id == user_id, Task.status == 'done')
    )
    volunteer_hours = await db.scalar(hours_query) or 0

    # achievements: список ачивок
    achievements_query = select(Achievement).join(
        UserAchievement, UserAchievement.achievement_id == Achievement.id
    ).where(UserAchievement.user_id == user_id)
    achievements = (await db.scalars(achievements_query)).all()

    return {
        "total_completed_tasks": total_completed_tasks,
        "rating_by_reviews": rating_by_reviews,
        "total_reviews_count": total_reviews_count,
        "volunteer_hours": volunteer_hours,
        "achievements": achievements
    }


async def get_active_tasks(user_id: int, db: AsyncSession) -> List[Task]:
    """Возвращает активные задачи волонтёра."""
    query = select(Task).join(
        TaskResponse, and_(TaskResponse.task_id == Task.id, TaskResponse.volunteer_id == user_id, TaskResponse.status == 'accepted')
    ).where(or_(Task.status == 'open', Task.status == 'in_progress'))
    return (await db.scalars(query)).all()


async def get_completed_tasks(user_id: int, db: AsyncSession) -> List[dict]:
    """Возвращает завершённые задачи с отзывами."""
    tasks_query = select(Task).join(
        TaskResponse, and_(TaskResponse.task_id == Task.id, TaskResponse.volunteer_id == user_id, TaskResponse.status == 'accepted')
    ).where(Task.status == 'done')
    tasks = (await db.scalars(tasks_query)).all()

    result = []
    for task in tasks:
        # Найти отзыв на задачу, где reviewer - заказчик, reviewee - волонтёр
        review_query = select(Review).where(
            and_(Review.target_type == 'task', Review.target_id == task.id, Review.reviewee_id == user_id)
        )
        review = await db.scalar(review_query)
        result.append({
            "task": task,
            "review": review
        })
    return result


async def get_skills(db: AsyncSession) -> List[Skill]:
    """Возвращает все навыки."""
    return (await db.scalars(select(Skill))).all()


async def get_my_skills(user_id: int, db: AsyncSession) -> List[int]:
    """Возвращает список id навыков волонтёра."""
    query = select(VolunteerSkill.skill_id).where(VolunteerSkill.user_id == user_id)
    return (await db.scalars(query)).all()


async def set_my_skills(user_id: int, skill_ids: List[int], db: AsyncSession):
    """Заменяет навыки волонтёра."""
    # Удалить старые
    await db.execute(VolunteerSkill.__table__.delete().where(VolunteerSkill.user_id == user_id))
    # Добавить новые
    for skill_id in skill_ids:
        db.add(VolunteerSkill(user_id=user_id, skill_id=skill_id))
    await db.commit()


async def delete_my_skill(user_id: int, skill_id: int, db: AsyncSession):
    """Удаляет один навык."""
    await db.execute(VolunteerSkill.__table__.delete().where(
        and_(VolunteerSkill.user_id == user_id, VolunteerSkill.skill_id == skill_id)
    ))
    await db.commit()