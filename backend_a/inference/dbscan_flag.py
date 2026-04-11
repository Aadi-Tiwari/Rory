# inference/dbscan_flag.py
"""
Outlier detection using DBSCAN fit on the training embedding space.
Flags cases whose embeddings fall outside all known clusters.
"""

from __future__ import annotations

import pickle
from pathlib import Path

import numpy as np
from sklearn.cluster import DBSCAN

DBSCAN_PATH = Path(__file__).parent.parent / "models" / "weights" / "dbscan.pkl"

_dbscan: DBSCAN | None = None


def _load() -> DBSCAN:
    global _dbscan
    if _dbscan is None:
        if DBSCAN_PATH.exists():
            with open(DBSCAN_PATH, "rb") as f:
                _dbscan = pickle.load(f)
        else:
            # Fallback: return None and flag everything as non-outlier
            # until fit() is called after first training run
            return None
    return _dbscan


def fit(embeddings: np.ndarray, eps: float = 0.5, min_samples: int = 5) -> None:
    """
    Fit DBSCAN on training embeddings and persist to disk.
    Call this once after training, before serving inference.
    """
    global _dbscan
    _dbscan = DBSCAN(eps=eps, min_samples=min_samples, metric="cosine")
    _dbscan.fit(embeddings)
    DBSCAN_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(DBSCAN_PATH, "wb") as f:
        pickle.dump(_dbscan, f)


def is_outlier(embedding: np.ndarray) -> bool:
    """
    Returns True if the embedding falls outside all training clusters.
    DBSCAN labels noise points as -1.
    """
    db = _load()
    if db is None:
        return False

    # Predict cluster membership for a single new point
    # by finding its nearest core sample
    core_samples = db.components_
    if len(core_samples) == 0:
        return False

    from sklearn.metrics.pairwise import cosine_distances
    dists = cosine_distances(embedding.reshape(1, -1), core_samples)
    min_dist = float(dists.min())

    # Use the fitted eps as the threshold
    return min_dist > db.eps