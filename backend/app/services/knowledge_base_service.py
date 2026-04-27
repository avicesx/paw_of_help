from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from sqlalchemy import select, func
from app.models.blog import KnowledgeBaseArticle, Tag, ArticleTag, ArticleRating
from app.schemas.knowledge_base import ArticleCreateRequest, ArticleUpdateRequest
from fastapi import HTTPException, status


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
        tags=article_data.tags,
        status="on_moderation"
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

    for field, value in article_data.dict(exclude_unset=True).items():
        setattr(article, field, value)

    await db.commit()
    await db.refresh(article)
    return article


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


async def get_all_tags(db: AsyncSession) -> List[Tag]:
    result = await db.scalars(select(Tag))
    return result.all()


async def get_categories(db: AsyncSession):
    return [
        {"id": 1, "name": "Кошки"},
        {"id": 2, "name": "Собаки"},
        {"id": 3, "name": "Птицы"},
        {"id": 4, "name": "Грызуны"},
    ]


async def get_breeds_by_category(category_id: int):
    if category_id == 1:
        return [
            {"id": 101, "name": "Сиамская", "description": "Древняя порода с характерным окрасом."},
            {"id": 102, "name": "Мейн-кун", "description": "Один из самых крупных домашних котов."},
        ]
    elif category_id == 2:
        return [
            {"id": 201, "name": "Лабрадор", "description": "Дружелюбная и умная порода."},
            {"id": 202, "name": "Немецкая овчарка", "description": "Отличный сторож и компаньон."},
        ]
    return []


async def get_breed_detail(breed_id: int):
    breeds = {
        101: {"id": 101, "name": "Сиамская", "description": "Древняя порода с характерным окрасом.", "health_issues": ["астма", "заболевания глаз"], "feeding_tips": "Кормить 3 раза в день", "socialization": "Рано приучать к людям"},
        102: {"id": 102, "name": "Мейн-кун", "description": "Один из самых крупных домашних котов.", "health_issues": ["кардиомиопатия", "дисплазия бедра"], "feeding_tips": "Высококалорийный корм", "socialization": "Терпим к детям"},
    }
    return breeds.get(breed_id, None)