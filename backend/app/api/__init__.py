"""API роутеры."""
from app.api.auth import router as auth_router
from app.api.organizations import router as organizations_router

__all__ = ["auth_router", "organizations_router"]