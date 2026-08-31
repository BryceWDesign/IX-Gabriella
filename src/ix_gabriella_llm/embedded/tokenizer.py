from __future__ import annotations

import re

_TOKEN_RE = re.compile(r"[A-Za-z0-9_]+|[^\w\s]", re.UNICODE)


def tokenize(text: str) -> tuple[str, ...]:
    return tuple(match.group(0).lower() for match in _TOKEN_RE.finditer(text.strip()))


def detokenize(tokens: tuple[str, ...] | list[str]) -> str:
    text = " ".join(tokens)
    for old, new in ((" ,", ","), (" .", "."), (" ?", "?"), (" !", "!"), (" :", ":"), (" ;", ";"), (" ' ", "'")):
        text = text.replace(old, new)
    return text.strip()
