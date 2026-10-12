"""
inference/predict.py
====================
Main inference entrypoint. Wires imputation, model forward pass,
DBSCAN outlier detection, ring buffer, cluster drift, and reasoning
into a single PredictResponse.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional, TYPE_CHECKING

import numpy as np
from inference.imputation import impute
from inference.ring_buffer import push_embedding
from inference.dbscan_flag import is_outlier
from inference.cluster_drift import cosine_distance_to_sepsis, compute_drift
from inference.reasoning import generate_reasoning

if TYPE_CHECKING:
    import torch
    from models.fusion import RoryModel

WEIGHTS_DIR = Path(__file__).parent.parent / "models" / "weights"
MODEL_PATH  = WEIGHTS_DIR / "best_model.pt"
STATS_PATH  = WEIGHTS_DIR / "train_stats.json"

_model: RoryModel | None = None
_stats: dict | None = None


def _load_stats() -> dict:
    global _stats
    if _stats is None:
        with open(STATS_PATH) as f:
            raw = json.load(f)
        _stats = raw.get("meta", raw)
    return _stats


def _load_model() -> RoryModel:
    global _model
    if _model is None:
        if not MODEL_PATH.is_file():
            raise FileNotFoundError("Model checkpoint is unavailable. Install best_model.pt before running predictions.")
        import torch
        from models.fusion import FusionModel, RoryModel
        from models.vitals_mlp import VitalsMLP
        from models.text_encoder import TextEncoder

        vitals_mlp   = VitalsMLP(hidden_dim=64, out_dim=128, dropout=0.3)
        text_encoder = TextEncoder(out_dim=128, dropout=0.3, device="cpu")
        fusion       = FusionModel(vitals_dim=128, text_dim=128, hidden_dim=256, dropout=0.3)
        model        = RoryModel(vitals_mlp, text_encoder, fusion)
        model.load_state_dict(torch.load(MODEL_PATH, map_location="cpu", weights_only=True))
        model.eval()
        _model = model
    return _model


def _risk_from_proba(proba: torch.Tensor) -> float:
    """
    proba is (1, 3) softmax — classes [HOME, ED, 911].
    Risk = weighted sum: HOME=0.0, ED=0.5, 911=1.0
    """
    import torch

    weights = torch.tensor([0.0, 0.5, 1.0])
    return float((proba.squeeze() * weights).sum())


def _risk_to_recommendation(risk: float) -> str:
    if risk >= 0.70:
        return "911"
    if risk >= 0.35:
        return "ED"
    return "HOME"


def _model_version() -> str:
    return _load_stats().get("model_version", "rory-v3")


def predict(
    patient_id: str,
    age_months: int,
    sex: str,
    weight_kg: float,
    complaint_text: str,
    vitals_raw: dict,
    vitals_t30: Optional[dict] = None,
) -> dict:
    """
    Returns a dict matching PredictResponse schema.
    """
    model = _load_model()
    import torch

    # ── completeness score (impute() for scoring only) ─────────────────────────
    _, completeness = impute(vitals_raw)

    # ── forward pass — VitalsMLP handles imputation/normalization internally ───
    with torch.no_grad():
        out = model([vitals_raw], [complaint_text])

    proba        = out["proba"]                              # (1, 3)
    embedding_np = out["fused_emb"].squeeze(0).cpu().numpy()  # (256,)

    risk = _risk_from_proba(proba)

    # ── ring buffer + drift ────────────────────────────────────────────────────
    buf                               = push_embedding(patient_id, embedding_np)
    drift_alert, cluster_drift, trend = compute_drift(buf.get())

    # ── outlier flag ───────────────────────────────────────────────────────────
    outlier_flag = is_outlier(embedding_np)

    # ── confidence ────────────────────────────────────────────────────────────
    confidence = risk * completeness
    if outlier_flag:
        confidence *= 0.80
    confidence = round(min(1.0, confidence), 4)

    # ── recommendation ─────────────────────────────────────────────────────────
    recommendation = _risk_to_recommendation(risk)

    # ── reasoning ─────────────────────────────────────────────────────────────
    reasoning = generate_reasoning(
        age_months=age_months,
        vitals=vitals_raw,
        vitals_t30=vitals_t30,
        risk=risk,
        complaint_text=complaint_text,
    )

    return {
        "recommendation":          recommendation,
        "risk":                    round(risk, 4),
        "confidence":              confidence,
        "completeness":            round(completeness, 4),
        "outlier_flag":            outlier_flag,
        "drift_alert":             drift_alert,
        "cluster_drift":           round(cluster_drift, 4),
        "sepsis_confidence_trend": trend,
        "reasoning":               reasoning,
        "model_version":           _model_version(),
    }
