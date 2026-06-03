import logging
import os
from typing import Optional
from .content_moderation_agent import ContentModerationAgent

logger = logging.getLogger(__name__)

_moderation_agent: Optional[ContentModerationAgent] = None


def init_moderation_agent():
    global _moderation_agent
    if _moderation_agent is not None:
        return

    base_path = os.getenv(
        "CONTENT_MODEL_BASE",
        "weeqeen/rubert-base-cased-finetuned-moderation",
    )
    tiny_path = os.getenv(
        "CONTENT_MODEL_TINY",
        "weeqeen/rubert-tiny2-moderation",
    )
    threshold = float(os.getenv("CONTENT_THRESHOLD", "0.55"))
    base_weight = float(os.getenv("CONTENT_BASE_WEIGHT", "0.3"))
    tiny_weight = float(os.getenv("CONTENT_TINY_WEIGHT", "0.7"))

    try:
        _moderation_agent = ContentModerationAgent(
            base_model_path=base_path,
            tiny_model_path=tiny_path,
            threshold=threshold,
            base_weight=base_weight,
            tiny_weight=tiny_weight,
        )
        logger.info("Агент модерации контента загружен")
    except Exception as e:
        logger.error("Не удалось загрузить агент модерации: %s", e)
        _moderation_agent = None

def get_moderation_agent() -> Optional[ContentModerationAgent]:
    return _moderation_agent