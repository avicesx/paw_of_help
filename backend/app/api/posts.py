from __future__ import annotations
from datetime import datetime, timezone
from typing import Annotated, Optional
from zoneinfo import ZoneInfo
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core import get_current_user, get_db, settings
from app.models import OrganizationUser, Post, User
from app.schemas.blog import PostCreate, PostResponse, PostUpdate


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


@router.get("", response_model=list[PostResponse])
async def list_posts(
    organization_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
):
    q = select(Post).order_by(Post.id.desc())
    if organization_id is not None:
        q = q.where(Post.organization_id == organization_id)
    rows = (await db.scalars(q)).all()
    return [PostResponse.model_validate(r) for r in rows]


@router.get("/{post_id}", response_model=PostResponse)
async def get_post(post_id: int, db: AsyncSession = Depends(get_db)):
    post = await db.get(Post, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="Пост не найден")
    return PostResponse.model_validate(post)


@router.post(
    "",
    response_model=PostResponse,
    status_code=status.HTTP_201_CREATED,
    openapi_extra={"security": [{"BearerAuth": []}]},
)
async def create_post(
    payload: PostCreate,
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

    post = Post(
        organization_id=org_id,
        author_user_id=current.id,
        title=payload.title,
        content=payload.content,
        attachments=payload.attachments,
        is_published=True,
        published_at=now,
    )
    db.add(post)
    await db.commit()
    await db.refresh(post)
    return PostResponse.model_validate(post)


@router.patch(
    "/{post_id}",
    response_model=PostResponse,
    openapi_extra={"security": [{"BearerAuth": []}]},
)
async def update_post(
    post_id: int,
    payload: PostUpdate,
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

    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(post, k, v)
    await db.commit()
    await db.refresh(post)
    return PostResponse.model_validate(post)


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