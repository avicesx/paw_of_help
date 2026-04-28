from __future__ import annotations
from dataclasses import dataclass
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import ReportReason


@dataclass(frozen=True)
class ReasonSeed:
    target_type: str
    code: str
    title: str
    sort_order: int = 0


SEEDS: list[ReasonSeed] = [
    # user
    ReasonSeed("user", "spam", "Спам", 10),
    ReasonSeed("user", "abuse", "Оскорбления / токсичность", 20),
    ReasonSeed("user", "hate", "Хейт / дискриминация", 30),
    ReasonSeed("user", "scam", "Мошенничество", 40),
    ReasonSeed("user", "privacy", "Нарушение приватности (личные данные)", 50),
    ReasonSeed("user", "links", "Подозрительные ссылки / скам", 60),
    ReasonSeed("user", "other", "Другое", 999),
    # comment
    ReasonSeed("comment", "spam", "Спам", 10),
    ReasonSeed("comment", "abuse", "Оскорбления / токсичность", 20),
    ReasonSeed("comment", "obscene", "Мат / непристойности", 30),
    ReasonSeed("comment", "hate", "Хейт / дискриминация", 40),
    ReasonSeed("comment", "privacy", "Нарушение приватности (личные данные)", 50),
    ReasonSeed("comment", "offtopic", "Не по теме", 60),
    ReasonSeed("comment", "other", "Другое", 999),
    # article
    ReasonSeed("article", "misinfo", "Ложная информация", 10),
    ReasonSeed("article", "danger", "Опасные советы", 20),
    ReasonSeed("article", "spam", "Спам / реклама", 30),
    ReasonSeed("article", "abuse", "Оскорбительный контент", 40),
    ReasonSeed("article", "copyright", "Нарушение авторских прав", 50),
    ReasonSeed("article", "other", "Другое", 999),
    # organization
    ReasonSeed("organization", "scam", "Мошенничество / подозрительный сбор средств", 10),
    ReasonSeed("organization", "misinfo", "Недостоверная информация", 20),
    ReasonSeed("organization", "spam", "Спам / реклама", 30),
    ReasonSeed("organization", "rules", "Нарушение правил платформы", 40),
    ReasonSeed("organization", "other", "Другое", 999),
    # post
    ReasonSeed("post", "spam", "Спам", 10),
    ReasonSeed("post", "abuse", "Оскорбления / токсичность", 20),
    ReasonSeed("post", "hate", "Хейт / дискриминация", 30),
    ReasonSeed("post", "privacy", "Нарушение приватности (личные данные)", 40),
    ReasonSeed("post", "misinfo", "Ложная информация", 50),
    ReasonSeed("post", "other", "Другое", 999),
]


async def seed_report_reasons_if_empty(db: AsyncSession) -> int:
    """
    Автозаполнение справочника причин жалоб.
    Запускается безопасно: если таблица не пустая — ничего не вставляет.
    """
    existing_count = await db.scalar(select(func.count(ReportReason.id)))
    if int(existing_count or 0) > 0:
        return 0

    for seed in SEEDS:
        db.add(
            ReportReason(
                target_type=seed.target_type,
                code=seed.code,
                title=seed.title,
                is_active=True,
                sort_order=seed.sort_order,
            )
        )
    await db.commit()
    return len(SEEDS)