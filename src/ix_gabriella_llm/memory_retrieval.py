from __future__ import annotations

import re
from dataclasses import dataclass

_TOKEN_RE = re.compile(r"[a-z0-9']+")


@dataclass(frozen=True, slots=True)
class MemoryHit:
    text: str
    score: float


def lexical_memory_hits(query: str, memories: tuple[str, ...], *, limit: int = 5) -> tuple[MemoryHit, ...]:
    query_terms = set(_TOKEN_RE.findall(query.lower()))
    if not query_terms:
        return ()
    hits: list[MemoryHit] = []
    for memory in memories:
        terms = set(_TOKEN_RE.findall(memory.lower()))
        if not terms:
            continue
        overlap = query_terms & terms
        score = len(overlap) / max(1, len(query_terms | terms))
        if score > 0:
            hits.append(MemoryHit(text=memory, score=round(score, 4)))
    hits.sort(key=lambda item: item.score, reverse=True)
    return tuple(hits[:limit])
