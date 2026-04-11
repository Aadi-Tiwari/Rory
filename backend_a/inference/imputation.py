
"""
Mean imputation for missing vitals using per-feature stats
computed at training time and saved in models/weights/train_stats.json.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

STATS_PATH = Path(__file__).parent.parent / "models" / "weights" / "train_stats.json"

_stats: dict | None = None

def _load() -> dict:
    global _stats
    if _stats is None:
        with open(STATS_PATH) as f:
            _stats = json.load(f)
    return _stats


VITAL_KEYS = ["hr", "rr", "temp_f", "spo2", "cap_refill_s"]


def impute(vitals: dict) -> tuple[dict, float]:
    """
    Fill None vitals with training-set means.
    Returns (imputed_vitals, completeness) where completeness is 0.0–1.0.

    completeness = fraction of vitals that were present on arrival.
    """
    stats    = _load()
    means    = stats["means"]        # {"hr": float, "rr": float, ...}
    out      = dict(vitals)
    present  = 0

    for key in VITAL_KEYS:
        if out.get(key) is None:
            out[key] = means[key]
        else:
            present += 1

    completeness = present / len(VITAL_KEYS)
    return out, completeness