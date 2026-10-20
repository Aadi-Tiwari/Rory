from __future__ import annotations

import math
from statistics import NormalDist

import numpy as np
from sklearn.metrics import average_precision_score, roc_auc_score


def rate(numerator: int, denominator: int) -> dict:
    if not denominator:
        return {"value": None, "numerator": numerator, "denominator": 0, "ci95": None}
    p = numerator / denominator
    z = NormalDist().inv_cdf(0.975)
    scale = 1 + z * z / denominator
    center = (p + z * z / (2 * denominator)) / scale
    width = z * math.sqrt(p * (1 - p) / denominator + z * z / (4 * denominator**2)) / scale
    return {
        "value": p, "numerator": numerator, "denominator": denominator,
        "ci95": [max(0.0, center - width), min(1.0, center + width)],
    }


def discrimination(labels: np.ndarray, scores: np.ndarray, resamples: int, seed: int) -> dict:
    if len(np.unique(labels)) < 2:
        return {"auroc": None, "average_precision": None, "ci95": None,
                "reason": "Both outcome classes are required."}
    rng = np.random.default_rng(seed)
    draws = []
    for _ in range(resamples):
        indices = rng.integers(0, len(labels), len(labels))
        y, s = labels[indices], scores[indices]
        if len(np.unique(y)) == 2:
            draws.append([roc_auc_score(y, s), average_precision_score(y, s)])
    intervals = np.quantile(draws, [0.025, 0.975], axis=0).T.tolist() if len(draws) >= 1000 else None
    confidence = None
    notes = []
    if intervals is None:
        notes.append("Fewer than 1000 valid bootstrap draws; intervals suppressed.")
    else:
        confidence = {}
        for name, bounds in zip(("auroc", "average_precision"), intervals):
            confidence[name] = bounds if bounds[0] < bounds[1] else None
            if confidence[name] is None:
                notes.append(f"{name}: degenerate bootstrap interval suppressed; empirical separation does not establish certainty.")
    return {
        "auroc": float(roc_auc_score(labels, scores)),
        "average_precision": float(average_precision_score(labels, scores)),
        "ci95": confidence,
        "bootstrap_requested": resamples, "bootstrap_valid": len(draws),
        "bootstrap_seed": seed,
        "interval_note": " ".join(notes) or None,
        "bootstrap_method": "Patient percentile bootstrap; one record per patient.",
    }


def summarize(labels: list[int], scores: list[float], threshold: float,
              resamples: int = 2000, seed: int = 42) -> dict:
    y, s = np.asarray(labels), np.asarray(scores, dtype=float)
    if not len(y) or y.shape != s.shape or y.ndim != 1:
        raise ValueError("Expected nonempty, aligned one-dimensional labels and scores.")
    if not np.isin(y, [0, 1]).all() or not np.isfinite(s).all():
        raise ValueError("Labels must be binary and scores must be finite.")
    if not ((s >= 0) & (s <= 1)).all() or not 0 <= threshold <= 1:
        raise ValueError("Scores and threshold must be in [0, 1].")
    if resamples < 1:
        raise ValueError("At least one bootstrap resample is required.")
    alarm = s >= threshold
    tp = int(np.sum((y == 1) & alarm))
    fn = int(np.sum((y == 1) & ~alarm))
    fp = int(np.sum((y == 0) & alarm))
    tn = int(np.sum((y == 0) & ~alarm))
    return {
        "n": len(y), "events": int(y.sum()), "threshold": threshold,
        "rate_interval_method": "Wilson score, 95%; descriptive intervals without multiplicity adjustment.",
        "confusion": {"tp": tp, "fn": fn, "fp": fp, "tn": tn},
        "sensitivity": rate(tp, tp + fn), "specificity": rate(tn, tn + fp),
        "ppv": rate(tp, tp + fp), "npv": rate(tn, tn + fn),
        "missed_case_rate": rate(fn, tp + fn),
        "false_positive_rate": rate(fp, tn + fp),
        "false_discovery_rate": rate(fp, tp + fp),
        "alert_rate": rate(tp + fp, len(y)),
        **discrimination(y, s, resamples, seed),
    }
