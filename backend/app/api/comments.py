from __future__ import annotations
from datetime import datetime, timedelta, timezone
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core import get_current_user, get_db
from app.models import BlogComment, BlogCommentReaction, OrganizationUser, Post, User
from app.schemas.blog import (
    BlogCommentCreate,
    BlogCommentResponse,
    BlogCommentUpdate,
    CommentReactionRequest,
)

router = APIRouter(prefix="/comments", tags=["comments"])


async def _get_post_or_404(db: AsyncSession, post_id: int) -> Post:
    post = await db.get(Post, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="Пост не найден")
    return post


async def _get_comment_or_404(db: AsyncSession, comment_id: int) -> BlogComment:
    c = await db.get(BlogComment, comment_id)
    if c is None:
        raise HTTPException(status_code=404, detail="Комментарий не найден")
    return c


async def _require_org_staff(db: AsyncSession, *, org_id: int, user_id: int) -> None:
    ou = await db.scalar(
        select(OrganizationUser).where(
            OrganizationUser.organization_id == org_id,
            OrganizationUser.user_id == user_id,
            OrganizationUser.invitation_status == "accepted",
            OrganizationUser.role.in_(["admin", "curator"]),
        )
    )
    if ou is None:
        raise HTTPException(status_code=403, detail="Недостаточно прав")


async def _anti_flood_limits(db: AsyncSession, *, post_id: int, user_id: int) -> None:
    """
    Антифлуд:
    - не чаще 1 комментария в 10 секунд под одним постом
    - не более 10 комментариев за 5 минут под одним постом
    """
    now = datetime.now(timezone.utc)
    last_dt = await db.scalar(
        select(func.max(BlogComment.created_at)).where(
            BlogComment.post_id == post_id,
            BlogComment.user_id == user_id,
        )
    )
    if last_dt is not None and (now - last_dt) < timedelta(seconds=10):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Слишком часто. Подождите немного перед следующим комментарием",
        )

    window_start = now - timedelta(minutes=5)
    cnt = await db.scalar(
        select(func.count(BlogComment.id)).where(
            BlogComment.post_id == post_id,
            BlogComment.user_id == user_id,
            BlogComment.created_at >= window_start,
        )
    )
    if int(cnt or 0) >= 10:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Слишком много комментариев за короткое время",
        )


async def _comment_reaction_stats(
    db: AsyncSession,
    *,
    comment_id: int,
    current_user_id: int | None,
) -> tuple[int, int, int | None]:
    likes = await db.scalar(
        select(func.count(BlogCommentReaction.user_id)).where(
            BlogCommentReaction.comment_id == comment_id,
            BlogCommentReaction.vote == 1,
        )
    )
    dislikes = await db.scalar(
        select(func.count(BlogCommentReaction.user_id)).where(
            BlogCommentReaction.comment_id == comment_id,
            BlogCommentReaction.vote == -1,
        )
    )
    my_vote = None
    if current_user_id is not None:
        my_vote = await db.scalar(
            select(BlogCommentReaction.vote).where(
                BlogCommentReaction.comment_id == comment_id,
                BlogCommentReaction.user_id == current_user_id,
            )
        )
    return int(likes or 0), int(dislikes or 0), my_vote


async def _to_response(
    db: AsyncSession,
    c: BlogComment,
    *,
    current_user_id: int | None,
) -> BlogCommentResponse:
    r = BlogCommentResponse.model_validate(c)
    if r.is_deleted:
        r.content = "Комментарий удалён"
    likes, dislikes, my_vote = await _comment_reaction_stats(
        db, comment_id=c.id, current_user_id=current_user_id
    )
    r.likes = likes
    r.dislikes = dislikes
    r.my_vote = my_vote
    return r


@router.get(
    "/post/{post_id}",
    response_model=list[BlogCommentResponse],
    summary="Комментарии к посту",
)
async def list_post_comments(
    post_id: int,
    include_deleted: bool = False,
    db: AsyncSession = Depends(get_db),
):
    await _get_post_or_404(db, post_id)
    q = select(BlogComment).where(BlogComment.post_id == post_id).order_by(BlogComment.id.asc())
    if not include_deleted:
        q = q.where(BlogComment.is_deleted.is_(False))
    rows = (await db.scalars(q)).all()
    return [await _to_response(db, r, current_user_id=None) for r in rows]


@router.post(
    "/post/{post_id}",
    response_model=BlogCommentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Добавить комментарий",
    openapi_extra={"security": [{"BearerAuth": []}]},
)
async def create_comment(
    post_id: int,
    payload: BlogCommentCreate,
    current: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    await _get_post_or_404(db, post_id)
    await _anti_flood_limits(db, post_id=post_id, user_id=current.id)

    if payload.parent_id is not None:
        parent = await _get_comment_or_404(db, payload.parent_id)
        if parent.post_id != post_id:
            raise HTTPException(status_code=400, detail="parent_id не относится к этому посту")

    org_id = payload.organization_id
    if org_id is not None:
        await _require_org_staff(db, org_id=org_id, user_id=current.id)

    c = BlogComment(
        post_id=post_id,
        user_id=current.id,
        parent_id=payload.parent_id,
        organization_id=org_id,
        content=payload.content,
        is_deleted=False,
    )
    db.add(c)
    await db.commit()
    await db.refresh(c)
    return await _to_response(db, c, current_user_id=current.id)


@router.patch(
    "/{comment_id}",
    response_model=BlogCommentResponse,
    summary="Редактировать комментарий",
    openapi_extra={"security": [{"BearerAuth": []}]},
)
async def update_comment(
    comment_id: int,
    payload: BlogCommentUpdate,
    current: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    c = await _get_comment_or_404(db, comment_id)
    if c.is_deleted:
        raise HTTPException(status_code=400, detail="Нельзя редактировать удалённый комментарий")

    if c.user_id != current.id:
        if c.organization_id is None:
            raise HTTPException(status_code=403, detail="Недостаточно прав")
        await _require_org_staff(db, org_id=c.organization_id, user_id=current.id)

    c.content = payload.content
    await db.commit()
    await db.refresh(c)
    return await _to_response(db, c, current_user_id=current.id)


@router.delete(
    "/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить комментарий",
    openapi_extra={"security": [{"BearerAuth": []}]},
)
async def delete_comment(
    comment_id: int,
    current: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    c = await _get_comment_or_404(db, comment_id)

    if c.user_id != current.id:
        if c.organization_id is None:
            raise HTTPException(status_code=403, detail="Недостаточно прав")
        await _require_org_staff(db, org_id=c.organization_id, user_id=current.id)

    if not c.is_deleted:
        c.is_deleted = True
        await db.commit()
    return None


@router.post(
    "/{comment_id}/react",
    response_model=BlogCommentResponse,
    summary="Поставить реакцию на комментарий",
    description="vote: 1 (лайк), -1 (дизлайк), 0 (снять реакцию)",
    openapi_extra={"security": [{"BearerAuth": []}]},
)
async def react(
    comment_id: int,
    payload: CommentReactionRequest,
    current: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    c = await _get_comment_or_404(db, comment_id)
    if c.is_deleted:
        raise HTTPException(status_code=400, detail="Нельзя реагировать на удалённый комментарий")

    if payload.vote not in (-1, 0, 1):
        raise HTTPException(status_code=400, detail="Неверное значение vote")

    existing = await db.get(
        BlogCommentReaction,
        {"comment_id": comment_id, "user_id": current.id},
    )

    if payload.vote == 0:
        if existing is not None:
            await db.delete(existing)
            await db.commit()
        return await _to_response(db, c, current_user_id=current.id)

    if existing is None:
        db.add(BlogCommentReaction(comment_id=comment_id, user_id=current.id, vote=payload.vote))
    else:
        existing.vote = payload.vote
    await db.commit()
    return await _to_response(db, c, current_user_id=current.id)

