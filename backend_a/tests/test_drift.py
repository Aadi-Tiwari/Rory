"""
tests/test_drift.py
===================
Tests for cluster drift detection (cluster_drift.py + ring_buffer.py).
"""

import numpy as np
import pytest
from inference.cluster_drift import save_centroid, cosine_distance_to_sepsis, compute_drift
from inference.ring_buffer import get_buffer, push_embedding


@pytest.fixture(autouse=True)
def reset_registry():
    import inference.ring_buffer as rb
    rb._registry.clear()


@pytest.fixture(autouse=True)
def set_centroid(tmp_path, monkeypatch):
    """Save a unit-vector centroid along dim-0."""
    import inference.cluster_drift as drift
    monkeypatch.setattr(drift, "CENTROID_PATH", tmp_path / "sepsis_centroid.npy")
    monkeypatch.setattr(drift, "_centroid", None)
    centroid = np.zeros(256, dtype=np.float32)
    centroid[0] = 1.0
    # save_centroid normalizes, so pass it already normalized
    save_centroid(np.stack([centroid]))


def test_identical_to_centroid_is_zero():
    emb = np.zeros(256, dtype=np.float32)
    emb[0] = 1.0
    assert cosine_distance_to_sepsis(emb) == pytest.approx(0.0, abs=1e-5)


def test_orthogonal_to_centroid_is_one():
    emb = np.zeros(256, dtype=np.float32)
    emb[1] = 1.0
    assert cosine_distance_to_sepsis(emb) == pytest.approx(1.0, abs=1e-5)


def test_no_embeddings_returns_no_alert():
    alert, dist, trend = compute_drift([])
    assert alert is False
    assert dist == 1.0
    assert trend == []


def test_monotonic_approach_triggers_alert():
    """Three embeddings with strictly increasing similarity to centroid."""
    # Centroid is along dim-0. Make embeddings progressively more aligned to it.
    # Use normalized vectors so cosine distance is well-defined.
    def make_emb(dim0_weight):
        e = np.zeros(256, dtype=np.float32)
        e[0] = dim0_weight
        e[1] = 1.0 - dim0_weight  # orthogonal component decreases
        return e / (np.linalg.norm(e) + 1e-8)

    e1 = make_emb(0.1)  # far from centroid
    e2 = make_emb(0.5)  # closer
    e3 = make_emb(0.9)  # closest
    alert, _, _ = compute_drift([e1, e2, e3])
    assert alert is True


def test_non_monotonic_no_alert():
    def make_emb(dim0_weight):
        e = np.zeros(256, dtype=np.float32)
        e[0] = dim0_weight
        e[1] = 1.0 - dim0_weight
        return e / (np.linalg.norm(e) + 1e-8)

    e1 = make_emb(0.9)
    e2 = make_emb(0.1)
    e3 = make_emb(0.5)
    alert, _, _ = compute_drift([e1, e2, e3])
    assert alert is False


def test_trend_length_matches_input():
    embeddings = []
    for i in range(4):
        e = np.zeros(256, dtype=np.float32)
        e[i % 256] = 1.0
        embeddings.append(e)
    _, _, trend = compute_drift(embeddings)
    assert len(trend) == 4


def test_ring_buffer_caps_at_five():
    pid = "TEST-001"
    for i in range(7):
        push_embedding(pid, np.full(256, float(i), dtype=np.float32))
    assert len(get_buffer(pid)) == 5


def test_ring_buffer_separate_per_patient():
    push_embedding("P1", np.ones(256, dtype=np.float32))
    push_embedding("P2", np.zeros(256, dtype=np.float32))
    assert len(get_buffer("P1")) == 1
    assert len(get_buffer("P2")) == 1
