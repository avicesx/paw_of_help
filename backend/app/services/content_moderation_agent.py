from typing import Dict, Any
from .content_safety_checker import ContentSafetyChecker
import logging

logger = logging.getLogger(__name__)


class ContentModerationAgent:
    """
    Агент для модерации текстового контента (отзывы, статьи, сообщения).
    Использует ансамбль моделей для оценки риска нарушения правил платформы.
    """

    def __init__(
        self,
        base_model_path: str,
        tiny_model_path: str,
        threshold: float = 0.55,
        base_weight: float = 0.3,
        tiny_weight: float = 0.7,
    ):
        self.checker = ContentSafetyChecker(
            base_model_path=base_model_path,
            tiny_model_path=tiny_model_path,
            base_weight=base_weight,
            tiny_weight=tiny_weight,
            threshold=threshold,
        )
        logger.info("ContentModerationAgent инициализирован")

    def evaluate(self, text: str) -> Dict[str, Any]:
        """
        Оценивает текст на соответствие правилам платформы.

        Returns:
            dict: {
                "verdict": "ALLOW" | "BLOCK" | "ERROR",
                "confidence": float,
                "details": dict,
                "preview": str
            }
        """
        try:
            raw = self.checker.predict(text)
            verdict = "BLOCK" if raw["label"] == "Нарушение" else "ALLOW"

            return {
                "verdict": verdict,
                "confidence": raw["confidence"],
                "details": raw["details"],
                "preview": (text[:100] + "...") if len(text) > 100 else text,
            }
        except Exception as e:
            logger.error("Ошибка при анализе текста: %s", e)
            return {
                "verdict": "ERROR",
                "confidence": 0.0,
                "details": {"error": str(e)},
                "preview": text[:100],
            }

    def is_safe(self, text: str) -> bool:
        """Возвращает True, если текст безопасный ( ALLOW )"""
        return self.evaluate(text)["verdict"] == "ALLOW"    