"""
generate_artifacts.py — run once on Dev Cloud after training.
Generates dbscan.pkl and sepsis_centroid.npy in models/weights/.

Run from inside backend_a/:
    export PYTHONPATH=/workspace/rory/backend_a
    python generate_artifacts.py
"""

import json
import numpy as np
import torch

from models.vitals_mlp import VitalsMLP
from models.text_encoder import TextEncoder
from models.fusion import FusionModel, RoryModel
from inference.imputation import impute
from inference.dbscan_flag import fit as dbscan_fit
from inference.cluster_drift import save_centroid

# ── Load cohort ────────────────────────────────────────────────────────────────
with open("data/hero_cohort.json") as f:
    cohort = json.load(f)

print(f"Cohort size: {len(cohort)} cases")

# ── Build model (same architecture as train.py) ────────────────────────────────
vitals_mlp   = VitalsMLP()
text_encoder = TextEncoder()
fusion       = FusionModel()
model        = RoryModel(vitals_mlp, text_encoder, fusion)

model.load_state_dict(torch.load("models/weights/best_model.pt", map_location="cpu"))
model.eval()

print("Model loaded.")

# ── Collect embeddings ─────────────────────────────────────────────────────────
all_embeddings    = []
sepsis_embeddings = []

VITAL_KEYS = ["hr", "rr", "temp_f", "spo2", "cap_refill_s"]

with torch.no_grad():
    for case in cohort:
        # Build mask BEFORE imputation (1 = missing, 0 = present)
        mask = [1.0 if case["vitals"].get(k) is None else 0.0 for k in VITAL_KEYS]

        # Impute missing vitals
        imputed, completeness = impute(case["vitals"])

        # Build 10-dim tensor: [5 vitals | 5 mask flags]
        vitals_tensor = torch.tensor(
            [[imputed[k] for k in VITAL_KEYS] + mask],
            dtype=torch.float32,
        )

        # Forward pass through RoryModel
        out = model(vitals_tensor, [case["complaint_text"]])

        emb = out["fused_emb"].squeeze(0).numpy()

        all_embeddings.append(emb)
        if case["ground_truth"] == "sepsis":
            sepsis_embeddings.append(emb)

all_embeddings    = np.array(all_embeddings)
sepsis_embeddings = np.array(sepsis_embeddings)

print(f"Total embeddings:  {len(all_embeddings)}")
print(f"Sepsis embeddings: {len(sepsis_embeddings)}")

# ── Fit DBSCAN ─────────────────────────────────────────────────────────────────
dbscan_fit(all_embeddings, eps=0.5, min_samples=5)
print("dbscan.pkl saved.")

# ── Save sepsis centroid ───────────────────────────────────────────────────────
save_centroid(sepsis_embeddings)
print("sepsis_centroid.npy saved.")

print("\nDone. Both artifacts in models/weights/ — download and drop locally.")