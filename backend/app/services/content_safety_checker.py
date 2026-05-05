import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer
from typing import Dict, Any

class ContentSafetyChecker:
    """
    Ансамбль из двух моделей для проверки безопасности текста.
    Схема: 0 = безопасный / допустимый, 1 = нарушение / опасный контент
    """

    def __init__(
        self,
        base_model_path: str,
        tiny_model_path: str,
        base_weight: float = 0.3,
        tiny_weight: float = 0.7,
        threshold: float = 0.55,
        max_length: int = 256,
    ):
        assert abs(base_weight + tiny_weight - 1.0) < 1e-6, "Веса должны суммироваться в 1.0"

        self.max_length = max_length
        self.threshold = threshold
        self.base_weight = base_weight
        self.tiny_weight = tiny_weight

        self.base_tokenizer = AutoTokenizer.from_pretrained(base_model_path)
        self.base_model = AutoModelForSequenceClassification.from_pretrained(base_model_path)
        self.base_model.eval()

        self.tiny_tokenizer = AutoTokenizer.from_pretrained(tiny_model_path)
        self.tiny_model = AutoModelForSequenceClassification.from_pretrained(tiny_model_path)
        self.tiny_model.eval()

    @torch.no_grad()
    def _predict_single(self, text: str, model, tokenizer) -> float:
        inputs = tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            padding="max_length",
            max_length=self.max_length,
        )
        logits = model(**inputs).logits
        probs = torch.softmax(logits, dim=-1).squeeze()
        return probs[1].item()

    def predict(self, text: str) -> Dict[str, Any]:
        if not text or not text.strip():
            return {
                "label": "Безопасный",
                "confidence": 1.0,
                "details": {"ensemble_score": 0.0, "decision": "empty_text"},
            }

        try:
            base_prob = self._predict_single(text, self.base_model, self.base_tokenizer)
            tiny_prob = self._predict_single(text, self.tiny_model, self.tiny_tokenizer)

            ensemble_prob = (self.base_weight * base_prob) + (self.tiny_weight * tiny_prob)

            if ensemble_prob > self.threshold:
                label = "Нарушение"
                confidence = ensemble_prob
                decision = f"ensemble>{self.threshold}"
            else:
                label = "Безопасный"
                confidence = 1.0 - ensemble_prob
                decision = f"ensemble<={self.threshold}"

            return {
                "label": label,
                "confidence": round(confidence, 4),
                "details": {
                    "base_score": round(base_prob, 4),
                    "tiny_score": round(tiny_prob, 4),
                    "ensemble_score": round(ensemble_prob, 4),
                    "decision": decision,
                    "threshold": self.threshold,
                },
            }
        except Exception as e:
            return {
                "label": "Ошибка",
                "confidence": 0.0,
                "details": {"error": str(e)},
            }