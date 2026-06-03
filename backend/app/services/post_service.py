from sqlalchemy.ext.asyncio import AsyncSession
from app.models.blog import Post
from app.schemas.blog import PostCreate, PostUpdate


async def create_post_record(
    db: AsyncSession,
    *,
    payload: PostCreate,
    author_user_id: int,
    organization_id: int | None,
) -> Post:
    post = Post(
        organization_id=organization_id,
        author_user_id=author_user_id,
        title=payload.title,
        content=payload.content,
        attachments=payload.attachments,
        tags=[],
        is_published=False,
        published_at=None,
        is_hidden=False,
        moderation_status="pending",
        moderation_reason=None,
    )
    db.add(post)
    await db.commit()
    await db.refresh(post)
    return post


async def update_post_record(
    db: AsyncSession,
    post: Post,
    payload: PostUpdate,
) -> tuple[Post, bool]:
    """Возвращает (post, нужна_ли_фоновая_обработка)"""
    data = payload.model_dump(exclude_unset=True)
    content_changed = "title" in data or "content" in data

    if content_changed:
        data["tags"] = []
        data["moderation_status"] = "pending"
        data["moderation_reason"] = None

    for key, value in data.items():
        setattr(post, key, value)

    await db.commit()
    await db.refresh(post)
    return post, content_changed