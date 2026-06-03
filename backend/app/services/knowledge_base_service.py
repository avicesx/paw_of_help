from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from sqlalchemy import select
from app.models.blog import KnowledgeBaseArticle, ArticleTag, ArticleRating
from app.schemas.knowledge_base import ArticleCreateRequest, ArticleUpdateRequest
from fastapi import HTTPException


async def get_articles_list(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 20,
    sort_by: str = "created_at",
    tag_ids: Optional[List[int]] = None,
) -> List[KnowledgeBaseArticle]:
    query = select(KnowledgeBaseArticle).where(KnowledgeBaseArticle.status == "published")

    if tag_ids:
        query = query.join(ArticleTag).where(ArticleTag.tag_id.in_(tag_ids))

    if sort_by == "popular":
        query = query.order_by(KnowledgeBaseArticle.views.desc(), KnowledgeBaseArticle.likes_count.desc())
    else:
        query = query.order_by(KnowledgeBaseArticle.created_at.desc())

    query = query.offset(skip).limit(limit)

    result = await db.scalars(query)
    return result.all()


async def get_article_detail(
    db: AsyncSession,
    article_id: int,
    current_user_id: Optional[int] = None
) -> KnowledgeBaseArticle:
    article = await db.get(KnowledgeBaseArticle, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Статья не найдена")

    if article.status != "published":
        raise HTTPException(status_code=404, detail="Статья не опубликована")

    article.views += 1
    await db.commit()

    return article


async def create_article(
    db: AsyncSession,
    article_data: ArticleCreateRequest,
    author_id: int
) -> KnowledgeBaseArticle:
    article = KnowledgeBaseArticle(
        title=article_data.title,
        content=article_data.content,
        author_id=author_id,
        tags=[],
        status="on_moderation",
    )
    db.add(article)
    await db.commit()
    await db.refresh(article)
    return article


async def update_article(
    db: AsyncSession,
    article_id: int,
    article_data: ArticleUpdateRequest,
    current_user_id: int
) -> KnowledgeBaseArticle:
    article = await db.get(KnowledgeBaseArticle, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Статья не найдена")

    if article.author_id != current_user_id:
        raise HTTPException(status_code=403, detail="Нет прав на редактирование")

    data = article_data.model_dump(exclude_unset=True)
    content_changed = "title" in data or "content" in data

    if content_changed:
        data["tags"] = []
        if article.status != "published":
            data["status"] = "on_moderation"
            data["rejection_reason"] = None
            data["moderated_at"] = None

    for field, value in data.items():
        setattr(article, field, value)

    await db.commit()
    await db.refresh(article)
    return article, content_changed


async def delete_article(
    db: AsyncSession,
    article_id: int,
    current_user_id: int
) -> None:
    article = await db.get(KnowledgeBaseArticle, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Статья не найдена")

    if article.author_id != current_user_id:
        raise HTTPException(status_code=403, detail="Нет прав на удаление")

    await db.delete(article)
    await db.commit()


async def toggle_like_article(
    db: AsyncSession,
    article_id: int,
    user_id: int,
    vote: int
) -> None:
    article = await db.get(KnowledgeBaseArticle, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Статья не найдена")

    rating = await db.get(ArticleRating, (article_id, user_id))
    if rating:
        if rating.vote == vote:
            await db.delete(rating)
            if vote == 1:
                article.likes_count -= 1
            else:
                article.dislikes_count -= 1
        else:
            if rating.vote == 1:
                article.likes_count -= 1
                article.dislikes_count += 1
            else:
                article.dislikes_count -= 1
                article.likes_count += 1
            rating.vote = vote
    else:
        new_rating = ArticleRating(article_id=article_id, user_id=user_id, vote=vote)
        db.add(new_rating)
        if vote == 1:
            article.likes_count += 1
        else:
            article.dislikes_count += 1

    await db.commit()