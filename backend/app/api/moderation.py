from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import get_current_user, get_db
from app.models.user import User
from app.schemas.moderation import (
    ArticleModerationItem,
    ResolveArticleRequest,
    ReportModerationItem,
    ResolveReportRequest,
)
from app.services.moderation_service import (
    get_articles_on_moderation,
    resolve_article,
    get_reports_for_moderation,
    resolve_report,
)

router = APIRouter(prefix="/moderation", tags=["moderation"])


def _require_moderator(current_user: User):
    if current_user.role not in ["admin", "moderator"]:
        raise HTTPException(status_code=403, detail="Недостаточно прав")


@router.get("/articles", response_model=List[ArticleModerationItem])
async def list_articles_on_moderation(
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    _require_moderator(current_user)
    articles = await get_articles_on_moderation(db)
    return [
        ArticleModerationItem(
            id=a.id,
            title=a.title,
            author_id=a.author_id,
            content_preview=(a.content[:100] + "...") if len(a.content) > 100 else a.content,
            created_at=a.created_at
        )
        for a in articles
    ]


@router.post("/articles/{article_id}/resolve")
async def moderate_article(
    article_id: int,
    resolution: ResolveArticleRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    _require_moderator(current_user)
    await resolve_article(db, article_id, resolution, current_user.id)
    return {"detail": "Статья обработана"}


@router.get("/reports", response_model=List[ReportModerationItem])
async def list_reports_for_moderation(
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    _require_moderator(current_user)
    reports = await get_reports_for_moderation(db)
    return [ReportModerationItem.model_validate(r) for r in reports]


@router.post("/reports/{report_id}/resolve")
async def moderate_report(
    report_id: int,
    resolution: ResolveReportRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    _require_moderator(current_user)
    await resolve_report(db, report_id, resolution, current_user.id)
    return {"detail": "Жалоба обработана"}