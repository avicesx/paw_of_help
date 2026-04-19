"""Алгоритмы ранжирования задач для ленты волонтёра."""

import math
from abc import ABC, abstractmethod
from typing import List, Tuple

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models import Task, VolunteerProfile, VolunteerSkill, Skill, Animal


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Вычисляет дистанцию между двумя точками на Земле в километрах."""
    R = 6371.0
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


class BaseTaskScorer(ABC):
    """Интерфейс алгоритма скоринга. Легко заменить на ML-стратегию в будущем."""

    @abstractmethod
    async def get_feed(self, user_id: int, db: AsyncSession) -> List[Task]:
        pass


class HeuristicTaskScorer(BaseTaskScorer):
    """Эвристический алгоритм ранжирования (MVP)."""

    # Маппинг типов задач к требуемым навыкам (русские названия)
    TASK_SKILL_MAP = {
        "walking": ["прогулки"],
        "foster": ["передержка"],
        "transport": ["транспортировка"],
        "vet_help": ["ветпомощь", "инъекции"],
        "socialization": ["социализация", "дрессировка"],
        "repair": ["ремонт"],
        "photography": ["фотосъёмка"],
        "fundraising": ["фандрайзинг"],
    }

    async def get_feed(self, user_id: int, db: AsyncSession) -> List[Task]:
        profile = await db.scalar(
            select(VolunteerProfile).where(VolunteerProfile.user_id == user_id)
        )
        if not profile:
            return []

        skills_query = select(Skill.name).join(
            VolunteerSkill, Skill.id == VolunteerSkill.skill_id
        ).where(VolunteerSkill.user_id == user_id)
        volunteer_skills = set(await db.scalars(skills_query))

        q = select(Task).where(Task.status == "open")

        v_lat = profile.location_lat
        v_lng = profile.location_lng
        v_radius = profile.radius_km or 50.0

        if v_lat is not None and v_lng is not None:
            lat_delta = v_radius / 110.574
            lng_delta = v_radius / (111.320 * max(math.cos(math.radians(v_lat)), 1e-6))

            q = q.where(Task.location_lat.is_not(None), Task.location_lng.is_not(None))
            q = q.where(Task.location_lat.between(v_lat - lat_delta, v_lat + lat_delta))
            q = q.where(Task.location_lng.between(v_lng - lng_delta, v_lng + lng_delta))

        if profile.preferred_animal_types:
            q = q.outerjoin(Animal, Task.animal_id == Animal.id).where(
                or_(
                    Task.animal_id.is_(None),
                    Animal.id.is_(None),
                    Animal.species.in_(profile.preferred_animal_types)
                )
            )

        tasks = (await db.scalars(q)).all()

        scored_tasks: List[Tuple[float, Task]] = []

        for task in tasks:
            score = 0.0

            if task.urgency == "urgent":
                score += settings.WEIGHT_URGENCY

            if v_lat is not None and v_lng is not None and task.location_lat is not None and task.location_lng is not None:
                dist = haversine_distance(v_lat, v_lng, task.location_lat, task.location_lng)
                if v_radius > 0:
                    if dist <= v_radius:
                        score += (1 - (dist / v_radius)) * settings.WEIGHT_DISTANCE
                    else:
                        continue
                elif dist == 0:
                    # Если радиус 0, и задача в той же точке, полный бонус
                    score += settings.WEIGHT_DISTANCE
                else:
                    continue

            # Бонус за навыки: если task_type соответствует навыкам волонтёра
            if task.task_type and task.task_type in self.TASK_SKILL_MAP:
                required_skills = set(self.TASK_SKILL_MAP[task.task_type])
                if volunteer_skills & required_skills:
                    score += settings.WEIGHT_SKILL

            if task.task_type == "foster" and profile.ready_for_foster:
                score += settings.WEIGHT_FOSTER

            if profile.availability and task.scheduled_time:
                if set(profile.availability.keys()) & set(task.scheduled_time.keys()):
                    score += settings.WEIGHT_TIME

            scored_tasks.append((score, task))

        scored_tasks.sort(key=lambda x: x[0], reverse=True)
        return [t[1] for t in scored_tasks]


default_scorer = HeuristicTaskScorer()
