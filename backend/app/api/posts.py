from __future__ import annotations
from datetime import datetime, timezone
from typing import Annotated, Optional
from zoneinfo import ZoneInfo
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core import get_current_user, get_db, get_optional_user, settings
from app.models import BlogComment, OrganizationUser, Post, PostReaction, User
from app.models.organization import Organization
from app.schemas.blog import CommentReactionRequest, PostCreate, PostResponse, PostUpdate
from app.services.content_background_service import process_post_in_background
from app.services.post_service import create_post_record, update_post_record


router = APIRouter(prefix="/posts", tags=["posts"])

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


def _day_range_utc(now_utc: datetime) -> tuple[datetime, datetime]:
    """
    Границы календарного дня в UTC, считая день по APP_TIMEZONE.
    """
    tz = ZoneInfo(settings.APP_TIMEZONE)
    local_now = now_utc.astimezone(tz)
    local_start = local_now.replace(hour=0, minute=0, second=0, microsecond=0)
    local_end = local_now.replace(hour=23, minute=59, second=59, microsecond=999999)
    return local_start.astimezone(timezone.utc), local_end.astimezone(timezone.utc)


async def _enrich_posts(
    db: AsyncSession,
    posts: list[Post],
    current_user_id: int | None = None,
) -> list[PostResponse]:
    """Обогащает список постов данными об организации и реакциях одним батчем запросов."""
    if not posts:
        return []

    post_ids = [p.id for p in posts]
    org_ids = list({p.organization_id for p in posts if p.organization_id is not None})

    # организации одним запросом
    orgs_map: dict[int, Organization] = {}
    if org_ids:
        orgs = (await db.scalars(select(Organization).where(Organization.id.in_(org_ids)))).all()
        orgs_map = {o.id: o for o in orgs}

    # лайки / дизлайки одним запросом
    likes_rows = (
        await db.execute(
            select(PostReaction.post_id, func.count().label("cnt"))
            .where(PostReaction.post_id.in_(post_ids), PostReaction.vote == 1)
            .group_by(PostReaction.post_id)
        )
    ).all()
    likes_map: dict[int, int] = {r.post_id: r.cnt for r in likes_rows}

    dislikes_rows = (
        await db.execute(
            select(PostReaction.post_id, func.count().label("cnt"))
            .where(PostReaction.post_id.in_(post_ids), PostReaction.vote == -1)
            .group_by(PostReaction.post_id)
        )
    ).all()
    dislikes_map: dict[int, int] = {r.post_id: r.cnt for r in dislikes_rows}

    comments_rows = (
        await db.execute(
            select(BlogComment.post_id, func.count().label("cnt"))
            .where(
                BlogComment.post_id.in_(post_ids),
                BlogComment.is_deleted.is_(False),
            )
            .group_by(BlogComment.post_id)
        )
    ).all()
    comments_map: dict[int, int] = {r.post_id: r.cnt for r in comments_rows}

    # голос текущего пользователя одним запросом
    my_votes_map: dict[int, int] = {}
    if current_user_id is not None:
        votes_rows = (
            await db.execute(
                select(PostReaction.post_id, PostReaction.vote).where(
                    PostReaction.post_id.in_(post_ids),
                    PostReaction.user_id == current_user_id,
                )
            )
        ).all()
        my_votes_map = {r.post_id: r.vote for r in votes_rows}

    result = []
    for p in posts:
        org = orgs_map.get(p.organization_id) if p.organization_id else None
        r = PostResponse.model_validate(p)
        r.organization_name = org.name if org else None
        r.organization_icon_url = org.logo_url if org else None
        r.likes_count = likes_map.get(p.id, 0)
        r.dislikes_count = dislikes_map.get(p.id, 0)
        r.comments_count = comments_map.get(p.id, 0)
        r.my_vote = my_votes_map.get(p.id)
        result.append(r)
    return result


@router.get("", response_model=list[PostResponse])
async def list_posts(
    organization_id: Optional[int] = None,
    current: Annotated[Optional[User], Depends(get_optional_user)] = None,
    db: AsyncSession = Depends(get_db),
):
    q = select(Post).where(Post.is_published.is_(True)).order_by(Post.id.desc())
    if organization_id is not None:
        q = q.where(Post.organization_id == organization_id)
    rows = (await db.scalars(q)).all()
    return await _enrich_posts(db, list(rows), current.id if current else None)


@router.get("/{post_id}", response_model=PostResponse)
async def get_post(
    post_id: int,
    current: Annotated[Optional[User], Depends(get_optional_user)] = None,
    db: AsyncSession = Depends(get_db),
):
    post = await db.get(Post, post_id)
    if post is None or post.is_hidden:
        raise HTTPException(status_code=404, detail="Пост не найден")
    if not post.is_published:
        if current is None or (
            post.author_user_id != current.id
            and not (
                post.organization_id
                and await db.scalar(
                    select(OrganizationUser).where(
                        OrganizationUser.organization_id == post.organization_id,
                        OrganizationUser.user_id == current.id,
                        OrganizationUser.invitation_status == "accepted",
                        OrganizationUser.role.in_(["admin", "curator"]),
                    )
                )
            )
        ):
            raise HTTPException(status_code=404, detail="Пост не найден")
    enriched = await _enrich_posts(db, [post], current.id if current else None)
    return enriched[0]


@router.post(
    "",
    response_model=PostResponse,
    status_code=status.HTTP_201_CREATED,
    openapi_extra={"security": [{"BearerAuth": []}]},
)
async def create_post(
    payload: PostCreate,
    background_tasks: BackgroundTasks,
    current: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    now = datetime.now(timezone.utc)
    start, end = _day_range_utc(now)

    count = await db.scalar(
        select(func.count(Post.id)).where(
            Post.author_user_id == current.id,
            Post.created_at >= start,
            Post.created_at <= end,
        )
    )
    if int(count or 0) >= 20:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Лимит постов на сегодня исчерпан",
        )

    org_id = payload.organization_id
    if org_id is not None:
        await _require_org_staff(db, org_id=org_id, user_id=current.id)

    post = await create_post_record(
        db,
        payload=payload,
        author_user_id=current.id,
        organization_id=org_id,
    )
    background_tasks.add_task(process_post_in_background, post.id)
    enriched = await _enrich_posts(db, [post], current.id)
    return enriched[0]


@router.patch(
    "/{post_id}",
    response_model=PostResponse,
    openapi_extra={"security": [{"BearerAuth": []}]},
)
async def update_post(
    post_id: int,
    payload: PostUpdate,
    background_tasks: BackgroundTasks,
    current: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    post = await db.get(Post, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="Пост не найден")

    if post.author_user_id != current.id:
        if post.organization_id is None:
            raise HTTPException(status_code=403, detail="Недостаточно прав")
        await _require_org_staff(db, org_id=post.organization_id, user_id=current.id)

    post, reprocess = await update_post_record(db, post, payload)
    if reprocess:
        background_tasks.add_task(process_post_in_background, post.id)
    enriched = await _enrich_posts(db, [post], current.id)
    return enriched[0]


@router.delete(
    "/{post_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    openapi_extra={"security": [{"BearerAuth": []}]},
)
async def delete_post(
    post_id: int,
    current: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    post = await db.get(Post, post_id)
    if post is None:
        return None

    if post.author_user_id != current.id:
        if post.organization_id is None:
            raise HTTPException(status_code=403, detail="Недостаточно прав")
        await _require_org_staff(db, org_id=post.organization_id, user_id=current.id)

    await db.delete(post)
    await db.commit()
    return None


@router.post(
    "/{post_id}/vote",
    response_model=PostResponse,
    summary="Проголосовать за пост",
    description="vote: 1 (лайк), -1 (дизлайк), 0 — снять реакцию",
    openapi_extra={"security": [{"BearerAuth": []}]},
)
async def vote_post(
    post_id: int,
    payload: CommentReactionRequest,
    current: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    post = await db.get(Post, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="Пост не найден")

    if payload.vote not in (-1, 0, 1):
        raise HTTPException(status_code=400, detail="Неверное значение vote")

    existing = await db.get(PostReaction, {"post_id": post_id, "user_id": current.id})

    if payload.vote == 0:
        if existing is not None:
            await db.delete(existing)
            await db.commit()
    elif existing is None:
        db.add(PostReaction(post_id=post_id, user_id=current.id, vote=payload.vote))
        await db.commit()
    else:
        existing.vote = payload.vote
        await db.commit()

    enriched = await _enrich_posts(db, [post], current.id)
    return enriched[0]
