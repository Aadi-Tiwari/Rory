# inference/predict.py
"""
Main inference entrypoint. Wires imputation, model forward pass,
DBSCAN outlier detection, ring buffer, cluster drift, and reasoning
into a single PredictResponse.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import numpy as np
import torch

from models.fusion import FusionModel
from models.vitals_mlp import VitalsMLP
from models.text_encoder import TextEncoder
from inference.imputation import impute
from inference.ring_buffer import push_embedding
from inference.dbscan_flag import is_outlier
from inference.cluster_drift import cosine_distance_to_sepsis, compute_drift
from inference.reasoning import generate_reasoning

WEIGHTS_DIR  = Path(__file__).parent.parent / "models" / "weights"
MODEL_PATH   = WEIGHTS_DIR / "best_model.pt"
STATS_PATH   = WEIGHTS_DIR / "train_stats.json"

_model: FusionModel | None = None
_stats: dict | None = None


def _load_stats() -> dict:
    global _stats
    if _stats is None:
        with open(STATS_PATH) as f:
            _stats = json.load(f)
    return _stats


def _load_model() -> FusionModel:
    global _model
    if _model is None:
        stats = _load_stats()
        _model = FusionModel()
        _model.load_state_dict(torch.load(MODEL_PATH, map_location="cpu"))
        _model.eval()
    return _model


def _risk_to_recommendation(risk: float) -> str:
    if risk >= 0.70:
        return "911"
    if risk >= 0.35:
        return "ED"
    return "HOME"


def _model_version() -> str:
    stats = _load_stats()
    return stats.get("model_version", "rory-v3")


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
    stats = _load_stats()

    # ── imputation ────────────────────────────────────────────────────────────
    vitals_imputed, completeness = impute(vitals_raw)

    # ── build vitals tensor ───────────────────────────────────────────────────
    vital_keys = ["hr", "rr", "temp_f", "spo2", "cap_refill_s"]
    means      = np.array([stats["means"][k]  for k in vital_keys], dtype=np.float32)
    stds       = np.array([stats["stds"][k]   for k in vital_keys], dtype=np.float32)
    raw_vals   = np.array([vitals_imputed[k]  for k in vital_keys], dtype=np.float32)
    normed     = (raw_vals - means) / (stds + 1e-8)

    age_norm   = np.array([(age_months - stats["age_mean"]) / (stats["age_std"] + 1e-8)],
                           dtype=np.float32)
    wt_norm    = np.array([(weight_kg  - stats["weight_mean"]) / (stats["weight_std"] + 1e-8)],
                           dtype=np.float32)
    sex_enc    = np.array([1.0 if sex == "M" else 0.0], dtype=np.float32)

    vitals_tensor = torch.tensor(
        np.concatenate([normed, age_norm, wt_norm, sex_enc]),
        dtype=torch.float32,
    ).unsqueeze(0)

    # ── forward pass ─────────────────────────────────────────────────────────
    with torch.no_grad():
        risk_logit, embedding = model(vitals_tensor, complaint_text)
        risk = float(torch.sigmoid(risk_logit).squeeze())

    embedding_np = embedding.squeeze().cpu().numpy()

    # ── ring buffer + drift ───────────────────────────────────────────────────
    buf              = push_embedding(patient_id, embedding_np)
    embeddings       = buf.get()
    drift_alert, cluster_drift, trend = compute_drift(embeddings)

    # ── outlier flag ──────────────────────────────────────────────────────────
    outlier_flag = is_outlier(embedding_np)

    # ── confidence: penalise for low completeness + outlier ───────────────────
    confidence = risk * completeness
    if outlier_flag:
        confidence *= 0.80
    confidence = round(min(1.0, confidence), 4)

    # ── recommendation ────────────────────────────────────────────────────────
    recommendation = _risk_to_recommendation(risk)

    # ── reasoning ────────────────────────────────────────────────────────────
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