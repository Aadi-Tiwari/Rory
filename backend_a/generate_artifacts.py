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
from inference.dbscan_flag import fit as dbscan_fit
from inference.cluster_drift import save_centroid

VITAL_KEYS = ["hr", "rr", "temp_f", "spo2", "cap_refill_s"]

# ── Load cohort ────────────────────────────────────────────────────────────────
with open("data/hero_cohort.json") as f:
    cohort = json.load(f)

print(f"Cohort size: {len(cohort)} cases")

# ── Load train stats ───────────────────────────────────────────────────────────
with open("models/weights/train_stats.json") as f:
    raw_stats = json.load(f)

meta = raw_stats["meta"]  # means, stds live under "meta"

# Patch imputation module so it uses the correct stats structure
import inference.imputation as _imp
_imp._stats = meta

from inference.imputation import impute

# ── Build model (must match train.py architecture exactly) ─────────────────────
# train.py: VitalsMLP(hidden_dim=64, out_dim=128)
#           TextEncoder(out_dim=128)
#           FusionModel(vitals_dim=128, text_dim=128, hidden_dim=256)
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {device}")

vitals_mlp   = VitalsMLP(hidden_dim=64, out_dim=128, dropout=0.3)
text_encoder = TextEncoder(out_dim=128, dropout=0.3, device=device)
fusion       = FusionModel(vitals_dim=128, text_dim=128, hidden_dim=256, dropout=0.3)
model        = RoryModel(vitals_mlp, text_encoder, fusion)

model.load_state_dict(torch.load("models/weights/best_model.pt", map_location=device))
model.to(device)
model.eval()

print("Model loaded.")

# ── Collect embeddings ─────────────────────────────────────────────────────────
all_embeddings    = []
sepsis_embeddings = []

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
        ).to(device)

        # Forward pass
        out = model(vitals_tensor, [case["complaint_text"]])
        emb = out["fused_emb"].squeeze(0).cpu().numpy()  # back to CPU for numpy

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

print("\nDone. All artifacts in models/weights/ — download and drop locally.")