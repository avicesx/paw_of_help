"""API роутеры."""
from app.api.auth import router as auth_router
from app.api.chats import router as chats_router
from app.api.notifications import router as notifications_router
from app.api.animal import router as animal_router
from app.api.organizations import router as organizations_router
from app.api.volunteer import router as volunteer_router
from app.api.tasks import router as tasks_router
from app.api.users import router as users_router
from app.api.reviews import router as reviews_router
from app.api.task_response import router as task_responses_router
from app.api.events import router as events_router
from app.api.knowledge_base import router as knowledge_base_router
from app.api.encyclopedia import router as encyclopedia_router


__all__ = [
    "auth_router",
    "chats_router",
    "notifications_router",
    "animal_router",
    "organizations_router",
    "volunteer_router",
    "tasks_router",
    "users_router",
    "reviews_router",
    "task_responses_router",
    "events_router",
    "knowledge_base_router",
    "encyclopedia_router",
]