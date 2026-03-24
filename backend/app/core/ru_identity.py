"""Правила для ФИО на кириллице и нормализация российских мобильных номеров."""

import re

RU_PERSON_NAME_RE = re.compile(
    r"^(?:[А-ЯЁ][а-яё]+(?:-[А-ЯЁ][а-яё]+)?)"
    r"(?: [А-ЯЁ][а-яё]+(?:-[А-ЯЁ][а-яё]+)?)*$"
)


def validate_ru_person_name(value: str) -> str:
    """
    Проверяет имя (одно или несколько слов): кириллица, заглавная буква в начале каждого слова,
    допустим дефис (например «Анна-Мария»). Возвращает строку с нормализованными пробелами.
    """
    name = " ".join(str(value).strip().split())
    if len(name) < 2:
        raise ValueError("Имя слишком короткое")
    if not RU_PERSON_NAME_RE.fullmatch(name):
        raise ValueError(
            "Укажите настоящее имя кириллицей: с заглавной буквы в каждом слове "
            "(например: Иван или Мария Иванова)"
        )
    return name


def normalize_ru_mobile(value: str) -> str:
    """
    Приводит ввод к виду E.164 для РФ мобильного: ``+79XXXXXXXXX`` (10 цифр после кода страны, первая — 9).
    Допускаются варианты ввода: ``+7…``, ``8…``, ``9…`` (10 цифр без кода страны).
    """
    if not value or not str(value).strip():
        raise ValueError("Укажите номер телефона")
    digits = re.sub(r"\D", "", value)
    if len(digits) == 11 and digits[0] == "8":
        digits = "7" + digits[1:]
    elif len(digits) == 10 and digits[0] == "9":
        digits = "7" + digits
    if not re.fullmatch(r"7(?:9\d{9})", digits):
        raise ValueError(
            "Неверный российский мобильный номер (+7 9XX …). "
            "Пример: +7 912 345-67-89 или 89123456789"
        )
    return f"+{digits}"
