"""
tests/test_outlier.py
=====================
Tests for DBSCAN outlier detection (dbscan_flag.py).
"""

import numpy as np
import pytest
from inference.dbscan_flag import fit, is_outlier


def _make_cluster(center: np.ndarray, n: int = 20, scale: float = 0.01, seed: int = 0) -> np.ndarray:
    """Make a tight cluster of unit-normalized vectors near `center`."""
    rng = np.random.default_rng(seed)
    pts = center + rng.normal(scale=scale, size=(n, len(center))).astype(np.float32)
    norms = np.linalg.norm(pts, axis=1, keepdims=True) + 1e-8
    return pts / norms


@pytest.fixture(autouse=True)
def fit_dbscan(tmp_path, monkeypatch):
    """Fit DBSCAN on two well-separated unit-sphere clusters."""
    import inference.dbscan_flag as dbf
    monkeypatch.setattr(dbf, "DBSCAN_PATH", tmp_path / "dbscan.pkl")
    monkeypatch.setattr(dbf, "_dbscan", None)
    center_a = np.zeros(256, dtype=np.float32); center_a[0] = 1.0
    center_b = np.zeros(256, dtype=np.float32); center_b[1] = 1.0
    embeddings = np.vstack([
        _make_cluster(center_a, seed=0),
        _make_cluster(center_b, seed=1),
    ])
    fit(embeddings, eps=0.05, min_samples=3)


def test_inlier_not_flagged():
    """A point near cluster A centroid should not be an outlier."""
    inlier = np.zeros(256, dtype=np.float32)
    inlier[0] = 1.0
    assert is_outlier(inlier) is False


def test_outlier_flagged():
    """A point far from both clusters should be flagged as an outlier."""
    outlier = np.zeros(256, dtype=np.float32)
    outlier[2] = 1.0
    assert is_outlier(outlier) is True


def test_returns_bool():
    """is_outlier must always return a plain Python bool."""
    emb = np.zeros(256, dtype=np.float32)
    emb[0] = 1.0
    result = is_outlier(emb)
    assert isinstance(result, bool)


def test_graceful_before_fit(tmp_path, monkeypatch):
    """If dbscan.pkl does not exist, is_outlier returns False (no crash)."""
    import inference.dbscan_flag as dbf
    monkeypatch.setattr(dbf, "_dbscan", None)
    monkeypatch.setattr(dbf, "DBSCAN_PATH", tmp_path / "missing.pkl")
    result = dbf.is_outlier(np.zeros(256, dtype=np.float32))
    assert result is False
