from __future__ import annotations

import json
from pathlib import Path


def test_llm_eval_dataset_has_required_cases() -> None:
    path = Path("evals/llm_behavior_eval.jsonl")
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    ids = {row["id"] for row in rows}
    assert "fast_lane_timer_skips_llm" in ids
    assert "complex_meeting_uses_brain_llm" in ids
    assert "unsafe_external_action_requires_approval" in ids
    assert all(row["expected_behavior"] for row in rows)
