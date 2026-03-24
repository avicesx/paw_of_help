"""Точка входа FastAPI: маршруты приложения."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from backend.app.api.auth import router as auth_router
from backend.app.core.config import settings
from backend.app.core.rate_limit import limiter


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

1. **Регистрация / вход:** `POST /auth/register`, `POST /auth/login` — в JSON ответа поле `access_token`.
2. **Остальные защищённые методы:** заголовок `Authorization: Bearer <access_token>`.
3. **Текущий пользователь:** `GET /auth/me`.

Ограничение частоты запросов к `/auth/register` и `/auth/login` задаётся переменной `AUTH_RATE_LIMIT` (по умолчанию `10/minute` на IP).
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


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    openapi_schema.setdefault("components", {}).setdefault("securitySchemes", {})[
        "BearerAuth"
    ] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
        "description": "Токен из `access_token` в ответе POST /auth/login или /auth/register",
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


@app.get("/")
async def root():
    """Служебная проверка доступности сервиса."""
    return {"message": "Paw of Help API is running"}
