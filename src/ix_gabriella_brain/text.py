from __future__ import annotations

import re
import unicodedata

_WORD_RE = re.compile(r"[a-z0-9']+")


def normalize_text(text: str) -> str:
    collapsed = " ".join(text.strip().split())
    normalized = unicodedata.normalize("NFKC", collapsed)
    return normalized


def lower_ascii(text: str) -> str:
    return normalize_text(text).casefold()


def tokens(text: str) -> tuple[str, ...]:
    return tuple(_WORD_RE.findall(lower_ascii(text)))


def token_overlap(a: str, b: str) -> float:
    left = set(tokens(a))
    right = set(tokens(b))
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def clip01(value: float) -> float:
    return max(0.0, min(1.0, value))
