from sqlalchemy.ext.asyncio import AsyncSession
from app.models.misc import PlatformSetting

KEY_POST_AUTO_PUBLISH = "post_auto_publish"
KEY_ARTICLE_AUTO_PUBLISH = "article_auto_publish"

DEFAULTS: dict[str, bool] = {
    KEY_POST_AUTO_PUBLISH: False,
    KEY_ARTICLE_AUTO_PUBLISH: False,
}


async def seed_moderation_settings_if_missing(db: AsyncSession) -> None:
    for key, value in DEFAULTS.items():
        existing = await db.get(PlatformSetting, key)
        if existing is None:
            db.add(PlatformSetting(key=key, value=value))
    await db.commit()


async def _get_bool(db: AsyncSession, key: str) -> bool:
    row = await db.get(PlatformSetting, key)
    if row is None:
        return DEFAULTS[key]
    return bool(row.value)


async def get_post_auto_publish(db: AsyncSession) -> bool:
    return await _get_bool(db, KEY_POST_AUTO_PUBLISH)


async def get_article_auto_publish(db: AsyncSession) -> bool:
    return await _get_bool(db, KEY_ARTICLE_AUTO_PUBLISH)


async def get_moderation_settings(db: AsyncSession) -> dict[str, bool]:
    return {
        "post_auto_publish": await get_post_auto_publish(db),
        "article_auto_publish": await get_article_auto_publish(db),
    }


async def update_moderation_settings(
    db: AsyncSession,
    *,
    post_auto_publish: bool | None = None,
    article_auto_publish: bool | None = None,
) -> dict[str, bool]:
    updates: list[tuple[str, bool]] = []
    if post_auto_publish is not None:
        updates.append((KEY_POST_AUTO_PUBLISH, post_auto_publish))
    if article_auto_publish is not None:
        updates.append((KEY_ARTICLE_AUTO_PUBLISH, article_auto_publish))

    for key, value in updates:
        row = await db.get(PlatformSetting, key)
        if row is None:
            db.add(PlatformSetting(key=key, value=value))
        else:
            row.value = value

    await db.commit()
    return await get_moderation_settings(db)
