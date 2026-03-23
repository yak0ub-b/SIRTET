"""
scores.py — Persistent top-N high score management (synchronous JSON).
Compatible with pygbag (Emscripten virtual FS maps open() calls).
"""
import json
import os
from constants import SCORES_FILE, TOP_N_SCORES


def load_scores() -> list:
    """Return sorted list (high→low) of up to TOP_N_SCORES integers."""
    try:
        with open(SCORES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        scores = [int(x) for x in data if isinstance(x, (int, float))]
        return sorted(scores, reverse=True)[:TOP_N_SCORES]
    except Exception:
        return []


def save_score(new_score: int):
    """
    Add new_score to the list if it enters the top-N.
    Returns (updated_scores: list[int], is_new_best: bool).
    """
    scores = load_scores()
    scores.append(new_score)
    scores = sorted(scores, reverse=True)[:TOP_N_SCORES]
    try:
        with open(SCORES_FILE, "w", encoding="utf-8") as f:
            json.dump(scores, f)
    except Exception:
        pass
    is_new_best = bool(scores) and scores[0] == new_score
    return scores, is_new_best


def is_high_score(score: int) -> bool:
    """Return True if score would enter the top-N list."""
    scores = load_scores()
    if len(scores) < TOP_N_SCORES:
        return True
    return score > scores[-1]
