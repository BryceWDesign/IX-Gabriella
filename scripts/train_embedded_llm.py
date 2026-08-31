from __future__ import annotations

import hashlib
import json
import math
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SEED_FILES = [
    ROOT / "models" / "training_data" / "gabriella_alignment_seed.jsonl",
    ROOT / "models" / "training_data" / "gabriella_embedded_lm_corpus.jsonl",
]
OUT = ROOT / "src" / "ix_gabriella_llm" / "data" / "ix_gabriella_micro_lm.json"


def tokenize(text: str) -> list[str]:
    import re

    return [match.group(0).lower() for match in re.finditer(r"[A-Za-z0-9_]+|[^\w\s]", text.strip())]


def load_records() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in SEED_FILES:
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            payload = json.loads(line)
            if "messages" in payload:
                user = ""
                assistant = ""
                for message in payload["messages"]:
                    if message.get("role") == "user":
                        user = str(message.get("content", ""))
                    if message.get("role") == "assistant":
                        raw = str(message.get("content", ""))
                        try:
                            assistant = str(json.loads(raw).get("assistant_response", raw))
                        except json.JSONDecodeError:
                            assistant = raw
                records.append({"user": user, "assistant": assistant, "tags": infer_tags(user, assistant)})
            else:
                records.append(payload)
    return records


def infer_tags(user: str, assistant: str) -> list[str]:
    joined = f"{user} {assistant}".lower()
    tags: list[str] = []
    mapping = {
        "timer": "timer",
        "list": "list",
        "note": "note",
        "remind": "reminder",
        "approval": "approval",
        "approve": "approval",
        "memory": "memory",
        "remember": "memory",
        "plan": "plan",
        "meeting": "meeting",
        "private": "privacy",
        "receipt": "receipt",
        "correction": "correction",
    }
    for needle, tag in mapping.items():
        if needle in joined and tag not in tags:
            tags.append(tag)
    return tags or ["general"]


def logprob_table(counter: Counter[str], denominator: int, vocab: int) -> dict[str, float]:
    return {key: round(math.log((count + 1) / (denominator + vocab)), 6) for key, count in counter.items()}


def main() -> int:
    records = load_records()
    unigram: Counter[str] = Counter()
    bigram: Counter[str] = Counter()
    trigram: Counter[str] = Counter()
    bigram_context: Counter[str] = Counter()
    trigram_context: Counter[str] = Counter()
    candidate_bank = []
    training_blob = ""
    for record in records:
        user = str(record["user"])
        assistant = str(record["assistant"])
        training_blob += json.dumps(record, sort_keys=True) + "\n"
        tokens = ["<s>", "<s>", *tokenize(assistant), "</s>"]
        for index in range(2, len(tokens)):
            a, b, c = tokens[index - 2], tokens[index - 1], tokens[index]
            unigram[c] += 1
            bigram[f"{b}\t{c}"] += 1
            trigram[f"{a}\t{b}\t{c}"] += 1
            bigram_context[b] += 1
            trigram_context[f"{a}\t{b}"] += 1
        tags = list(dict.fromkeys(str(tag).lower() for tag in record.get("tags", []) if str(tag).strip()))
        candidate_bank.append(
            {
                "assistant_response": assistant,
                "tags": tags or infer_tags(user, assistant),
                "requested_tool": requested_tool_for(tags, assistant),
                "risk": risk_for(tags, assistant),
                "requires_user_approval": approval_for(tags, assistant),
                "memory_write_requested": "memory" in tags and "approval" in tags,
            }
        )
    vocab = len(unigram) + 1
    unigram_total = sum(unigram.values())
    bigram_log = {
        key: round(math.log((count + 1) / (bigram_context[key.split("\t")[0]] + vocab)), 6)
        for key, count in bigram.items()
    }
    trigram_log = {
        key: round(math.log((count + 1) / (trigram_context["\t".join(key.split("\t")[:2])] + vocab)), 6)
        for key, count in trigram.items()
    }
    artifact = {
        "name": "IX-Gabriella-LLM-Micro",
        "model_id": "ix-gabriella-llm-micro-v0.1.0",
        "version": "0.1.0",
        "author": "Bryce Lovell",
        "license": "Source-Available Noncommercial Evaluation License v1.0",
        "trained_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "training_examples": len(records),
        "training_sha256": hashlib.sha256(training_blob.encode("utf-8")).hexdigest(),
        "metadata": {
            "architecture": "interpolated_trigram_response_selection_language_model",
            "vocabulary_size": vocab,
            "unknown_logprob": round(math.log(1 / (unigram_total + vocab)), 6),
            "capability_boundary": "actual embedded language model artifact; not a frontier-scale LLM",
        },
        "candidate_bank": candidate_bank,
        "unigram_logprob": logprob_table(unigram, unigram_total, vocab),
        "bigram_logprob": bigram_log,
        "trigram_logprob": trigram_log,
    }
    unsigned = json.dumps(artifact, sort_keys=True, separators=(",", ":")).encode("utf-8")
    artifact["artifact_sha256"] = hashlib.sha256(unsigned).hexdigest()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(artifact, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"wrote": str(OUT.relative_to(ROOT)), "examples": len(records), "sha256": artifact["artifact_sha256"]}, indent=2))
    return 0


def requested_tool_for(tags: list[str], assistant: str) -> str:
    if "plan" in tags:
        return "propose_plan"
    if "approval" in tags or "memory" in tags:
        return "stage_action_preview"
    return "draft_response"


def risk_for(tags: list[str], assistant: str) -> str:
    text = " ".join(tags) + " " + assistant.lower()
    if "destructive" in text or "spending" in text or "private" in text:
        return "high"
    if "approval" in text or "memory" in text or "plan" in text:
        return "medium"
    return "low"


def approval_for(tags: list[str], assistant: str) -> bool:
    text = " ".join(tags) + " " + assistant.lower()
    return any(term in text for term in ("approval", "approve", "private", "send", "spending", "booking", "memory"))


if __name__ == "__main__":
    raise SystemExit(main())
