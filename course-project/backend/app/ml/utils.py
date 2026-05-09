import re
from typing import Optional


def safe_lower(value: Optional[str]) -> str:
    return (value or "").strip().lower()


def tokenize(text: Optional[str]) -> list[str]:
    text = safe_lower(text)
    return re.findall(r"[a-zA-Zа-яА-ЯёЁ0-9]+", text)


def text_contains(text: Optional[str], pattern: str) -> bool:
    return pattern.lower() in safe_lower(text)


def bool_to_num(value) -> int:
    return 1 if value else 0