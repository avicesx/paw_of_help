from __future__ import annotations
import asyncio
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.ml_guard import get_moderation_agent
from app.services.tag_service import generate_tags_for_content


@dataclass
class ContentSubmitResult:
    tags: list[str]
    ml_verdict: str
    blocked: bool
    rejection_reason: str | None


def _ml_evaluate_sync(text: str) -> dict:
    agent = get_moderation_agent()
    if agent is None:
        return {"verdict": "ALLOW"}
    return agent.evaluate(text)


async def process_submitted_content(
    db: AsyncSession,
    *,
    title: str,
    content: str,
) -> ContentSubmitResult:
    """
    1) Проверка дообученной моделью модерации
    2) Если ок — автоматические теги из справочника через LLM
    """
    text = f"{title}\n\n{content}".strip()
    ml = await asyncio.to_thread(_ml_evaluate_sync, text)
    verdict = ml.get("verdict", "ERROR")

    if verdict == "BLOCK":
        return ContentSubmitResult(
            tags=[],
            ml_verdict=verdict,
            blocked=True,
            rejection_reason="Контент не прошёл автоматическую модерацию",
        )

    tags = await generate_tags_for_content(db, title=title, content=content)
    return ContentSubmitResult(
        tags=tags,
        ml_verdict=verdict,
        blocked=False,
        rejection_reason=None,
    )
