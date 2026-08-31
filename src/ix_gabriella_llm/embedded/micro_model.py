from __future__ import annotations

import json
import math
from dataclasses import dataclass
from importlib import resources
from typing import Any

from .tokenizer import tokenize

_MODEL_RESOURCE = "ix_gabriella_micro_lm.json"
_SAFE_DEFAULT = (
    "I can help, but I will keep the plan reviewable and wait for approval before any consequential action."
)


@dataclass(frozen=True, slots=True)
class CandidateScore:
    response: str
    score: float
    tags: tuple[str, ...]
    requested_tool: str
    risk: str
    requires_user_approval: bool
    memory_write_requested: bool


@dataclass(slots=True)
class EmbeddedGabriellaMicroLM:
    artifact: dict[str, Any]

    @classmethod
    def load(cls) -> "EmbeddedGabriellaMicroLM":
        data = resources.files("ix_gabriella_llm.data").joinpath(_MODEL_RESOURCE).read_text(encoding="utf-8")
        artifact = json.loads(data)
        if not isinstance(artifact, dict) or artifact.get("name") != "IX-Gabriella-LLM-Micro":
            raise ValueError("embedded Gabriella model artifact is invalid")
        return cls(artifact=artifact)

    @property
    def model_id(self) -> str:
        return str(self.artifact["model_id"])

    @property
    def model_sha256(self) -> str:
        return str(self.artifact["artifact_sha256"])

    @property
    def vocabulary_size(self) -> int:
        return int(self.artifact["metadata"]["vocabulary_size"])

    def select_response(self, *, user_text: str, route: str, status: str, missing_slots: tuple[str, ...]) -> CandidateScore:
        context_tokens = tokenize(f"{user_text} {route} {status} {' '.join(missing_slots)}")
        candidates = self.artifact["candidate_bank"]
        scored: list[CandidateScore] = []
        for candidate in candidates:
            response = str(candidate["assistant_response"])
            tags = tuple(str(tag) for tag in candidate.get("tags", ()))
            response_tokens = tokenize(response)
            lm_score = self._sequence_score(response_tokens)
            context_score = self._context_affinity(context_tokens, tags, response_tokens)
            route_score = self._route_bias(route=route, status=status, tags=tags, missing_slots=missing_slots)
            length_penalty = abs(len(response_tokens) - 24) * 0.015
            total = lm_score + context_score + route_score - length_penalty
            scored.append(
                CandidateScore(
                    response=response,
                    score=total,
                    tags=tags,
                    requested_tool=str(candidate.get("requested_tool") or "draft_response"),
                    risk=str(candidate.get("risk") or "medium"),
                    requires_user_approval=bool(candidate.get("requires_user_approval", False)),
                    memory_write_requested=bool(candidate.get("memory_write_requested", False)),
                )
            )
        if not scored:
            return CandidateScore(_SAFE_DEFAULT, -999.0, (), "draft_response", "medium", True, False)
        return max(scored, key=lambda item: item.score)

    def _sequence_score(self, tokens: tuple[str, ...]) -> float:
        if not tokens:
            return -999.0
        unigram = self.artifact["unigram_logprob"]
        bigram = self.artifact["bigram_logprob"]
        trigram = self.artifact["trigram_logprob"]
        unknown = float(self.artifact["metadata"]["unknown_logprob"])
        total = 0.0
        padded = ("<s>", "<s>", *tokens, "</s>")
        for index in range(2, len(padded)):
            a, b, c = padded[index - 2], padded[index - 1], padded[index]
            tri = trigram.get(f"{a}\t{b}\t{c}", unknown)
            bi = bigram.get(f"{b}\t{c}", unknown)
            uni = unigram.get(c, unknown)
            total += (0.58 * float(tri)) + (0.30 * float(bi)) + (0.12 * float(uni))
        return total / max(1, len(tokens))

    @staticmethod
    def _context_affinity(context_tokens: tuple[str, ...], tags: tuple[str, ...], response_tokens: tuple[str, ...]) -> float:
        context = set(context_tokens)
        tag_score = sum(0.42 for tag in tags if tag in context)
        response_overlap = len(context.intersection(response_tokens)) * 0.035
        return min(2.4, tag_score + response_overlap)

    @staticmethod
    def _route_bias(*, route: str, status: str, tags: tuple[str, ...], missing_slots: tuple[str, ...]) -> float:
        score = 0.0
        if route == "brain_lane" and "plan" in tags:
            score += 1.15
        if route == "approval_lane" and "approval" in tags:
            score += 1.25
        if route == "fast_lane" and "fast" in tags:
            score += 1.1
        if status == "needs_clarification" and "clarify" in tags:
            score += 1.35
        if status == "needs_approval" and "approval" in tags:
            score += 1.35
        if missing_slots and "clarify" in tags:
            score += 0.8
        if "memory" in tags and ("remember" in tags or status == "memory_candidate"):
            score += 0.2
        return score
