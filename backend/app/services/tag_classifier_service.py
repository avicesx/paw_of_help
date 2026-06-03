import logging
import httpx
from app.core import settings
from app.core.content_tags import PROMPT_TEMPLATE, TAGS

logger = logging.getLogger(__name__)


def validate_tags(tags: list[str], allowed_names: list[str] | None = None) -> list[str]:
    allowed = allowed_names if allowed_names is not None else TAGS
    allowed_set = set(allowed)
    return [t for t in tags if t in allowed_set][:10]


async def classify_text(text: str, *, allowed_names: list[str] | None = None) -> list[str]:
    """Аналог run_model(model, text) из скрипта, модель — gemma2:9b"""
    pool = allowed_names if allowed_names is not None else TAGS
    tags_str = ", ".join(pool)
    prompt = PROMPT_TEMPLATE.format(tags_list=tags_str, text=text[:1500])

    try:
        async with httpx.AsyncClient(timeout=settings.OLLAMA_TIMEOUT_SECONDS) as client:
            response = await client.post(
                f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/chat",
                json={
                    "model": settings.OLLAMA_TAG_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "options": {"temperature": 0.2},
                    "stream": False,
                },
            )
            response.raise_for_status()
            content = response.json()["message"]["content"]

        raw_tags = [t.strip() for t in content.split(",")]
        return validate_tags(raw_tags, allowed_names=pool)
    except Exception as e:
        logger.warning("Классификатор тегов: %s", e)
        return []
