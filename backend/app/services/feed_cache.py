"""Сервис кэширования умной ленты волонтёра в Redis."""

import json
from typing import List, Optional

import redis.asyncio as redis
from app.core import settings
from app.schemas.volunteer import TaskBriefResponse

_redis_client: Optional[redis.Redis] = None


def get_redis() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis_client


async def get_cached_feed(user_id: int) -> Optional[List[TaskBriefResponse]]:
    """Получает отсортированную ленту из кэша, если она есть."""
    client = get_redis()
    cache_key = f"feed:volunteer:{user_id}"

    cached_data = await client.get(cache_key)
    if cached_data:
        tasks_dicts = json.loads(cached_data)
        return [TaskBriefResponse(**task) for task in tasks_dicts]
    return None


async def invalidate_cached_feed(user_id: int) -> None:
    """Удаляет кэш ленты для пользователя."""
    client = get_redis()
    cache_key = f"feed:volunteer:{user_id}"
    await client.delete(cache_key)


async def set_cached_feed(user_id: int, tasks: List[TaskBriefResponse]) -> None:
    """Сохраняет ленту в кэш с заданным TTL."""
    client = get_redis()
    cache_key = f"feed:volunteer:{user_id}"
    tasks_dicts = [task.model_dump(mode='json') for task in tasks]
    await client.set(cache_key, json.dumps(tasks_dicts), ex=settings.FEED_CACHE_TTL)


async def invalidate_all_cached_feeds() -> None:
    """Удаляет все кэши лент волонтёров."""
    client = get_redis()
    # Удалить все ключи с префиксом feed:volunteer:*
    keys = await client.keys("feed:volunteer:*")
    if keys:
        await client.delete(*keys)
