from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from app.core.content_tags import TAGS as DEFAULT_TAG_NAMES
from app.models.blog import ArticleTag, Tag
from app.services.tag_classifier_service import classify_text


async def seed_initial_tags(db: AsyncSession) -> int:
    """Заполняет справочник из DEFAULT_TAG_NAMES, если таблица пустая"""
    existing = await db.scalar(select(Tag.id).limit(1))
    if existing is not None:
        return 0
    for name in DEFAULT_TAG_NAMES:
        db.add(Tag(name=name))
    await db.commit()
    return len(DEFAULT_TAG_NAMES)


async def list_tags(db: AsyncSession) -> list[Tag]:
    return list((await db.scalars(select(Tag).order_by(Tag.name))).all())


async def get_tag_names(db: AsyncSession) -> list[str]:
    tags = await list_tags(db)
    return [t.name for t in tags]


async def create_tag(db: AsyncSession, name: str) -> Tag:
    name = name.strip()
    if not name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Имя тега не может быть пустым")

    dup = await db.scalar(select(Tag).where(Tag.name == name))
    if dup is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Тег с таким именем уже есть")

    tag = Tag(name=name)
    db.add(tag)
    await db.commit()
    await db.refresh(tag)
    return tag


async def delete_tag(db: AsyncSession, tag_id: int) -> None:
    tag = await db.get(Tag, tag_id)
    if tag is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Тег не найден")
    await db.delete(tag)
    await db.commit()


async def sync_article_tag_links(
    db: AsyncSession,
    article_id: int,
    tag_names: list[str],
) -> None:
    """Синхронизирует JSON tags статьи со связями article_tags для фильтра по tag_ids"""
    await db.execute(delete(ArticleTag).where(ArticleTag.article_id == article_id))
    if not tag_names:
        return
    tags = (
        await db.scalars(select(Tag).where(Tag.name.in_(tag_names)))
    ).all()
    for tag in tags:
        db.add(ArticleTag(article_id=article_id, tag_id=tag.id))


async def generate_tags_for_content(
    db: AsyncSession,
    *,
    title: str,
    content: str,
) -> list[str]:
    allowed = await get_tag_names(db)
    if not allowed:
        allowed = list(DEFAULT_TAG_NAMES)
    text = f"{title}\n\n{content}"
    return await classify_text(text, allowed_names=allowed)
