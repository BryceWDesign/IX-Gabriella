from __future__ import annotations

from dataclasses import dataclass

VOWELS = set("aeiou")
HARD_ANCHORS = set("bcdgkptvzr")


@dataclass(frozen=True, slots=True)
class WakeNameScore:
    phrase: str
    syllable_estimate: int
    consonant_anchor_count: int
    repeated_word_risk: bool
    score: float
    rationale: tuple[str, ...]


def score_wake_phrase(phrase: str) -> WakeNameScore:
    clean = " ".join(phrase.lower().strip().split())
    if not clean:
        raise ValueError("phrase must not be empty")
    syllables = _syllables(clean)
    anchors = sum(1 for char in clean if char in HARD_ANCHORS)
    repeated = len(clean.split()) != len(set(clean.split()))
    score = 5.0
    rationale: list[str] = []
    if 3 <= syllables <= 6:
        score += 2.0
        rationale.append("good-syllable-window")
    else:
        score -= 1.0
        rationale.append("outside-ideal-syllable-window")
    if anchors >= 4:
        score += 1.5
        rationale.append("strong-consonant-anchors")
    elif anchors >= 3:
        score += 1.0
        rationale.append("strong-consonant-anchors")
    if not repeated:
        score += 0.5
        rationale.append("no-repeated-words")
    score = max(0.0, min(10.0, score))
    return WakeNameScore(clean, syllables, anchors, repeated, round(score, 2), tuple(rationale))


def _syllables(text: str) -> int:
    count = 0
    last_was_vowel = False
    for char in text:
        is_vowel = char in VOWELS
        if is_vowel and not last_was_vowel:
            count += 1
        last_was_vowel = is_vowel
    return max(1, count)
