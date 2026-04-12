# inference/cluster_drift.py
"""
Sepsis trajectory detection via cosine distance to the sepsis centroid.
Fires drift_alert if the last 3+ embeddings in the ring buffer are
monotonically approaching the sepsis cluster.
"""

from __future__ import annotations

import pickle
from pathlib import Path

import numpy as np

CENTROID_PATH = Path(__file__).parent.parent / "models" / "weights" / "sepsis_centroid.npy"

_centroid: np.ndarray | None = None


def _load_centroid() -> np.ndarray | None:
    global _centroid
    if _centroid is None and CENTROID_PATH.exists():
        _centroid = np.load(CENTROID_PATH)
    return _centroid


def save_centroid(sepsis_embeddings: np.ndarray) -> None:
    """
    Compute and persist the sepsis centroid from training embeddings.
    Call once after training alongside dbscan_flag.fit().
    """
    centroid = sepsis_embeddings.mean(axis=0)
    centroid = centroid / (np.linalg.norm(centroid) + 1e-8)
    CENTROID_PATH.parent.mkdir(parents=True, exist_ok=True)
    np.save(CENTROID_PATH, centroid)
    global _centroid
    _centroid = centroid


def cosine_distance_to_sepsis(embedding: np.ndarray) -> float:
    """
    Returns cosine distance from embedding to sepsis centroid.
    0.0 = identical to centroid, 2.0 = maximally opposite.
    """
    centroid = _load_centroid()
    if centroid is None:
        return 1.0  # neutral fallback

    e = embedding / (np.linalg.norm(embedding) + 1e-8)
    c = centroid  / (np.linalg.norm(centroid)  + 1e-8)
    return float(1.0 - np.dot(e, c))


def compute_drift(ring_buffer_embeddings: list[np.ndarray]) -> tuple[bool, float, list[float]]:
    """
    Given the last N embeddings from a patient's ring buffer:
      - Computes cosine distance to sepsis centroid for each
      - drift_alert = True if last 3+ distances are monotonically decreasing
        (patient embedding approaching sepsis cluster)
      - Returns (drift_alert, latest_cluster_drift, sepsis_confidence_trend)

    sepsis_confidence_trend: distance converted to similarity (1 - dist),
    so higher = more sepsis-like. Used directly in PredictResponse.
    """
    if not ring_buffer_embeddings:
        return False, 1.0, []

    distances = [cosine_distance_to_sepsis(e) for e in ring_buffer_embeddings]
    trend     = [round(1.0 - d, 4) for d in distances]  # similarity, not distance
    latest    = distances[-1]

    # Drift alert: last 3 consecutive embeddings getting closer to sepsis centroid
    drift_alert = False
    if len(distances) >= 3:
        last3 = distances[-3:]
        drift_alert = last3[0] > last3[1] > last3[2]

    return drift_alert, round(latest, 4), trend