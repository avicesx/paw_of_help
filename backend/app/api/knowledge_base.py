from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core import get_current_user, get_db
from app.models.user import User
from app.models.blog import KnowledgeBaseArticle, Tag, ArticleTag, ArticleRating
from app.schemas.knowledge_base import (
    ArticleListResponse,
    ArticleDetailResponse,
    ArticleCreateRequest,
    ArticleUpdateRequest,
    TagResponse,
)
from app.services.knowledge_base_service import (
    get_articles_list,
    get_article_detail,
    create_article,
    update_article,
    delete_article,
    toggle_like_article,
    get_all_tags,
)

router = APIRouter(prefix="/knowledge-base", tags=["knowledge-base"])


@router.get("/articles", response_model=List[ArticleListResponse])
async def list_articles(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, le=100),
    sort_by: str = Query("created_at", pattern="^(created_at|popular)$"),
    tag_ids: List[int] = Query([]),
    db: AsyncSession = Depends(get_db),
):
    articles = await get_articles_list(db, skip=skip, limit=limit, sort_by=sort_by, tag_ids=tag_ids)

    user_ids = [a.author_id for a in articles if a.author_id]
    users_map: dict[int, str] = {}
    if user_ids:
        users = (await db.scalars(select(User).where(User.id.in_(user_ids)))).all()
        users_map = {u.id: u.name or u.username for u in users}

    return [
        ArticleListResponse(
            id=a.id,
            title=a.title,
            author_name=users_map.get(a.author_id, "Неизвестный"),
            created_at=a.created_at,
            views=a.views,
            likes_count=a.likes_count,
            dislikes_count=a.dislikes_count,
            tags=a.tags,
        )
        for a in articles
    ]


@router.get("/articles/{article_id}", response_model=ArticleDetailResponse)
async def get_article(
    article_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    article = await get_article_detail(db, article_id, current_user.id)

    rating = await db.get(ArticleRating, (article_id, current_user.id))
    liked = rating.vote if rating else None

    author_name = (await db.get(User, article.author_id)).name or "Неизвестный"

    return ArticleDetailResponse(
        id=article.id,
        title=article.title,
        content=article.content,
        author_name=author_name,
        created_at=article.created_at,
        updated_at=article.updated_at,
        views=article.views,
        tags=article.tags,
        liked_by_user=liked == 1 if liked is not None else None,
    )


@router.post("/articles", response_model=ArticleListResponse, status_code=status.HTTP_201_CREATED)
async def create_new_article(
    payload: ArticleCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    article = await create_article(db, payload, current_user.id)
    author_name = current_user.name or current_user.username
    return ArticleListResponse(
        id=article.id,
        title=article.title,
        author_name=author_name,
        created_at=article.created_at,
        views=article.views,
        likes_count=article.likes_count,
        dislikes_count=article.dislikes_count,
        tags=article.tags,
    )


@router.put("/articles/{article_id}", response_model=ArticleDetailResponse)
async def edit_article(
    article_id: int,
    payload: ArticleUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    article = await update_article(db, article_id, payload, current_user.id)
    author_name = current_user.name or current_user.username
    return ArticleDetailResponse(
        id=article.id,
        title=article.title,
        content=article.content,
        author_name=author_name,
        created_at=article.created_at,
        updated_at=article.updated_at,
        views=article.views,
        tags=article.tags,
    )


@router.delete("/articles/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_article(
    article_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    await delete_article(db, article_id, current_user.id)


@router.post("/articles/{article_id}/like")
async def like_article(
    article_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    vote: int = Query(..., ge=-1, le=1),
    db: AsyncSession = Depends(get_db),
):
    if vote == 0:
        vote = 1
    await toggle_like_article(db, article_id, current_user.id, vote)
    return {"detail": "Голос учтён"}


@router.get("/tags", response_model=List[TagResponse])
async def list_tags(
    db: AsyncSession = Depends(get_db),
):
    tags = await get_all_tags(db)
    return [TagResponse(id=t.id, name=t.name) for t in tags]