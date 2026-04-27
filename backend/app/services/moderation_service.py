from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.blog import KnowledgeBaseArticle
from app.models.misc import Report
from app.schemas.moderation import ResolveArticleRequest, ResolveReportRequest
from app.services.notification_service import create_notification
from fastapi import HTTPException, status


async def get_articles_on_moderation(db: AsyncSession) -> list[KnowledgeBaseArticle]:
    result = await db.scalars(
        select(KnowledgeBaseArticle).where(KnowledgeBaseArticle.status == "on_moderation")
    )
    return result.all()


async def resolve_article(
    db: AsyncSession, article_id: int, resolution: ResolveArticleRequest, moderator_id: int
) -> KnowledgeBaseArticle:
    article = await db.get(KnowledgeBaseArticle, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Статья не найдена")

    if resolution.action == "publish":
        article.status = "published"
        article.published = True
        await create_notification(
            db,
            user_id=article.author_id,
            type="article_published",
            title="Статья опубликована",
            body=f'Ваша статья "{article.title}" успешно опубликована.',
        )
    elif resolution.action == "reject":
        article.status = "rejected"
        if resolution.rejection_reason:
            article.rejection_reason = resolution.rejection_reason
        await create_notification(
            db,
            user_id=article.author_id,
            type="article_rejected",
            title="Статья отклонена",
            body=f'Ваша статья "{article.title}" была отклонена модератором. Причина: {resolution.rejection_reason or "не указана."}',
        )
    else:
        raise HTTPException(status_code=400, detail="Недопустимое действие")

    article.moderated_at = datetime.utcnow()
    article.moderated_by = moderator_id

    await db.commit()
    await db.refresh(article)
    return article


async def get_reports_for_moderation(db: AsyncSession) -> list[Report]:
    result = await db.scalars(
        select(Report).where(Report.status == "pending")
    )
    return result.all()


async def resolve_report(
    db: AsyncSession, report_id: int, resolution: ResolveReportRequest, moderator_id: int
) -> Report:
    report = await db.get(Report, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Жалоба не найдена")

    if resolution.action == "approve":
        report.status = "approved"
    elif resolution.action == "reject":
        report.status = "rejected"
        await create_notification(
            db,
            user_id=report.reporter_id,
            type="complaint_rejected",
            title="Жалоба отклонена",
            body=f'Ваша жалоба на {report.target_type} была отклонена модератором.',
        )
    else:
        raise HTTPException(status_code=400, detail="Недопустимое действие")

    report.moderator_id = moderator_id

    await db.commit()
    await db.refresh(report)
    return report