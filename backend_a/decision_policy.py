"""Historical prototype policy, shared by inference and research evaluation."""

import math

LABELS = ("HOME", "ED", "911")
POLICY_VERSION = "weighted-risk-0.35-0.70-v1"
SYNTHETIC_LABELS = {
    "sepsis": "911", "appendicitis": "911", "strep": "ED",
    "gastroenteritis": "ED", "kawasaki": "ED", "uti": "ED",
    "viral_syndrome": "HOME", "influenza": "HOME", "otitis_media": "HOME",
}


def risk_from_probabilities(probabilities):
    if len(probabilities) != len(LABELS) or any(
        isinstance(p, bool) or not isinstance(p, (int, float)) or not math.isfinite(p) or not 0 <= p <= 1
        for p in probabilities
    ) or not math.isclose(sum(probabilities), 1.0, abs_tol=1e-6):
        raise ValueError("Expected normalized probabilities ordered HOME, ED, 911")
    return (probabilities[1] * 0.5 + probabilities[2]) / sum(probabilities)


def recommendation_from_risk(risk):
    if not math.isfinite(risk) or not 0 <= risk <= 1:
        raise ValueError("Risk must be finite and between zero and one")
    return "911" if risk >= 0.70 else "ED" if risk >= 0.35 else "HOME"


def synthetic_label(diagnosis):
    if diagnosis not in SYNTHETIC_LABELS:
        raise ValueError("Unknown synthetic diagnosis label")
    return SYNTHETIC_LABELS[diagnosis]
