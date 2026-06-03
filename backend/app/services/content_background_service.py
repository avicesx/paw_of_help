from __future__ import annotations
import logging
from datetime import datetime, timezone
from app.core.database import AsyncSessionLocal
from app.models.blog import KnowledgeBaseArticle, Post
from app.services.content_submit_service import process_submitted_content
from app.services.moderation_settings_service import get_article_auto_publish, get_post_auto_publish
from app.services.notification_service import create_notification
from app.services.tag_service import sync_article_tag_links

logger = logging.getLogger(__name__)


async def process_article_in_background(article_id: int) -> None:
    async with AsyncSessionLocal() as db:
        try:
            article = await db.get(KnowledgeBaseArticle, article_id)
            if article is None:
                return

            result = await process_submitted_content(
                db,
                title=article.title,
                content=article.content,
            )

            if result.blocked:
                article.status = "rejected"
                article.rejection_reason = result.rejection_reason
                article.moderated_at = datetime.now(timezone.utc)
                article.tags = []
                await sync_article_tag_links(db, article.id, [])
                if article.author_id:
                    await create_notification(
                        db,
                        user_id=article.author_id,
                        type="article_rejected",
                        title="Статья отклонена",
                        body=f'Статья "{article.title}" не прошла автоматическую модерацию',
                        commit=False,
                    )
            else:
                article.tags = result.tags
                await sync_article_tag_links(db, article.id, result.tags)
                auto_publish = await get_article_auto_publish(db)
                if auto_publish:
                    article.status = "published"
                    article.published = True
                    article.rejection_reason = None
                    article.moderated_at = datetime.now(timezone.utc)
                    if article.author_id:
                        await create_notification(
                            db,
                            user_id=article.author_id,
                            type="article_published",
                            title="Статья опубликована",
                            body=f'Ваша статья "{article.title}" опубликована',
                            commit=False,
                        )
                else:
                    article.status = "on_moderation"
                    article.published = False
                    article.rejection_reason = None
                    article.moderated_at = None

            await db.commit()
        except Exception:
            logger.exception("Фоновый процесс крашнулся для статьи %s", article_id)


async def process_post_in_background(post_id: int) -> None:
    async with AsyncSessionLocal() as db:
        try:
            post = await db.get(Post, post_id)
            if post is None:
                return

            result = await process_submitted_content(
                db,
                title=post.title,
                content=post.content or "",
            )

            if result.blocked:
                post.tags = []
                post.is_published = False
                post.is_hidden = True
                post.published_at = None
                post.moderation_status = "rejected"
                post.moderation_reason = result.rejection_reason
                post.moderated_at = datetime.now(timezone.utc)
            else:
                post.tags = result.tags
                post.moderation_reason = None
                post.is_hidden = False
                auto_publish = await get_post_auto_publish(db)
                if auto_publish:
                    post.moderation_status = "approved"
                    post.is_published = True
                    if post.published_at is None:
                        post.published_at = datetime.now(timezone.utc)
                else:
                    post.moderation_status = "pending"
                    post.is_published = False
                    post.published_at = None

            await db.commit()
        except Exception:
            logger.exception("Фоновый процесс крашнулся для поста %s", post_id)
