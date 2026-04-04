"""Pydantic схемы для профиля волонтёра."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from datetime import datetime


class VolunteerProfileCreate(BaseModel):
    """Схема создания профиля волонтёра."""
    location: Optional[str] = None
    location_lat: Optional[float] = None
    location_lng: Optional[float] = None
    radius_km: Optional[int] = None
    availability: Dict[str, Any] = {}
    preferred_animal_types: List[str] = []
    ready_for_foster: bool = False
    housing_type: Optional[str] = None
    has_other_pets: Dict[str, Any] = {}
    has_children: bool = False
    foster_restrictions: Optional[str] = None
    foster_photos: List[str] = []


class VolunteerProfileUpdate(BaseModel):
    """Схема обновления профиля волонтёра (все поля опциональны)."""
    location: Optional[str] = None
    location_lat: Optional[float] = None
    location_lng: Optional[float] = None
    radius_km: Optional[int] = None
    availability: Optional[Dict[str, Any]] = None
    preferred_animal_types: Optional[List[str]] = None
    ready_for_foster: Optional[bool] = None
    housing_type: Optional[str] = None
    has_other_pets: Optional[Dict[str, Any]] = None
    has_children: Optional[bool] = None
    foster_restrictions: Optional[str] = None
    foster_photos: Optional[List[str]] = None


class VolunteerProfileResponse(VolunteerProfileCreate):
    """Ответ с данными профиля волонтёра (базовой информацией без статистики)."""
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SkillResponse(BaseModel):
    """Ответ с информацией о навыке."""
    id: int
    name: str
    description: Optional[str] = None

    class Config:
        from_attributes = True


class SkillListResponse(BaseModel):
    """Ответ со списком навыков."""
    skills: List[SkillResponse]


class SkillIdsRequest(BaseModel):
    """Запрос на обновление списка навыков волонтёра."""
    skill_ids: List[int]


class AchievementResponse(BaseModel):
    """Ответ с информацией о достижении."""
    id: int
    code: str
    title: str
    description: Optional[str] = None
    icon: Optional[str] = None

    class Config:
        from_attributes = True


class VolunteerStats(BaseModel):
    """Вычисляемая статистика волонтёра (часы, рейтинг, задачи, достижения)."""
    total_completed_tasks: int
    rating_by_reviews: float
    total_reviews_count: int
    volunteer_hours: Optional[int] = None
    achievements: List[AchievementResponse]


class VolunteerProfileFullResponse(VolunteerProfileResponse):
    """Полный ответ профиля волонтёра с вычисляемой статистикой."""
    stats: VolunteerStats


class TaskBriefResponse(BaseModel):
    """Краткая информация о задаче (для списка активных/завершённых задач)."""
    id: int
    title: str
    description: Optional[str] = None
    status: str
    created_at: datetime
    end_date: Optional[datetime] = None
    author_id: int

    class Config:
        from_attributes = True


class ReviewResponse(BaseModel):
    """Ответ с информацией об отзыве (оценка и комментарий)."""
    id: int
    reviewer_id: int
    rating: int
    comment: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class CompletedTaskResponse(TaskBriefResponse):
    """Информация о завершённой задаче с отзывом (если есть)."""
    completed_at: Optional[datetime] = None
    review: Optional[ReviewResponse] = None


class VolunteerSkillCreate(BaseModel):
    """Запрос на добавление навыка волонтёру."""
    skill_id: int
    level: Optional[str] = None


class VolunteerSkillResponse(BaseModel):
    """Ответ с информацией о навыке волонтёра (уровень, ID)."""
    user_id: int
    skill_id: int
    level: Optional[str] = None

    class Config:
        from_attributes = True