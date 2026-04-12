"""Точка входа FastAPI: маршруты приложения."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api import (
    auth_router,
    notifications_router,
    organizations_router,
    tasks_router,
    volunteer_router,
    animal_router,
)
from app.core import settings, limiter


def _cors_allow_credentials() -> bool:
    raw = settings.CORS_ORIGINS.strip()
    return bool(raw and raw != "*")


def _cors_origins() -> list[str]:
    raw = settings.CORS_ORIGINS.strip()
    if not raw or raw == "*":
        return ["*"]
    return [o.strip() for o in raw.split(",") if o.strip()] or ["*"]


API_DESCRIPTION = """
## Авторизация (ЕУЗ)

1. **Регистрация / вход:** `POST /auth/register` (только username и password), `POST /auth/login` (login: username, email или phone) — в JSON ответа поле `access_token`.
2. **Остальные защищённые методы:** заголовок `Authorization: Bearer <access_token>`.
3. **Текущий пользователь:** `GET /auth/me`.

Ограничение частоты запросов к `/auth/register` и `/auth/login` задаётся переменной `AUTH_RATE_LIMIT` (по умолчанию `10/minute` на IP).

## Профиль волонтёра

- **Профиль:** `GET /volunteer/profile` — получить профиль с статистикой, `PATCH /volunteer/profile` — обновить, `DELETE /volunteer/profile` — деактивировать.
- **Навыки:** `GET /volunteer/skills` — список всех навыков, `GET /volunteer/my-skills` — мои навыки, `POST /volunteer/my-skills` — установить навыки, `DELETE /volunteer/my-skills/{skill_id}` — удалить навык.
- **Задачи:** `GET /volunteer/tasks?status=active|completed` — задачи волонтёра (активные или завершённые).
""".strip()

app = FastAPI(
    title="Paw of Help API",
    description=API_DESCRIPTION,
    version="0.1.0",
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

_origins = _cors_origins()
_credentials = _cors_allow_credentials()
if _origins == ["*"]:
    _credentials = False
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(notifications_router)
app.include_router(organizations_router)
app.include_router(tasks_router)
app.include_router(volunteer_router)
app.include_router(animal_router)


@app.get("/")
async def root():
    """Служебная проверка доступности сервиса."""
    return {"message": "Paw of Help API is running"}