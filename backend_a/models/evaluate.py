"""
evaluate.py — RORY Hackathon, Backend A
=========================================
Evaluates the trained model on held_out.json.

Outputs a report including:
  - Overall accuracy, macro F1
  - Per-class precision / recall / F1
  - Confusion matrix
  - Rory Staunton case spotlight (must be 911, drift_alert True)

Usage (from repo root):
    python backend_a/models/evaluate.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import torch

from models.vitals_mlp import VitalsMLP
from models.text_encoder import TextEncoder
from models.fusion import FusionModel, RoryModel, LABEL_TO_IDX, IDX_TO_LABEL

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT    = Path(__file__).parent.parent
DATA_DIR     = REPO_ROOT / "data"
WEIGHTS_DIR  = Path(__file__).parent / "weights"

HELD_OUT_PATH    = DATA_DIR / "held_out.json"
BEST_MODEL_PATH  = WEIGHTS_DIR / "best_model.pt"
TRAIN_STATS_PATH = WEIGHTS_DIR / "train_stats.json"

GT_TO_TRIAGE: dict[str, str] = {
    "sepsis":          "911",
    "appendicitis":    "911",
    "strep":           "ED",
    "gastroenteritis": "ED",
    "kawasaki":        "ED",
    "uti":             "ED",
    "viral_syndrome":  "HOME",
    "influenza":       "HOME",
    "otitis_media":    "HOME",
}


# ---------------------------------------------------------------------------
# Metric helpers
# ---------------------------------------------------------------------------

def precision_recall_f1(
    y_true: list[int], y_pred: list[int], n_classes: int = 3
) -> tuple[list[float], list[float], list[float]]:
    prec, rec, f1 = [], [], []
    for c in range(n_classes):
        tp = sum(1 for t, p in zip(y_true, y_pred) if t == c and p == c)
        fp = sum(1 for t, p in zip(y_true, y_pred) if t != c and p == c)
        fn = sum(1 for t, p in zip(y_true, y_pred) if t == c and p != c)
        p = tp / max(tp + fp, 1)
        r = tp / max(tp + fn, 1)
        f = 2 * p * r / max(p + r, 1e-8)
        prec.append(round(p, 4))
        rec.append(round(r, 4))
        f1.append(round(f, 4))
    return prec, rec, f1


def confusion_matrix(
    y_true: list[int], y_pred: list[int], n_classes: int = 3
) -> list[list[int]]:
    cm = [[0] * n_classes for _ in range(n_classes)]
    for t, p in zip(y_true, y_pred):
        cm[t][p] += 1
    return cm


def print_confusion_matrix(cm: list[list[int]], labels: list[str]) -> None:
    header = "         " + "  ".join(f"{l:>6}" for l in labels)
    print(header)
    for i, row in enumerate(cm):
        row_str = "  ".join(f"{v:>6}" for v in row)
        print(f"  {labels[i]:>6}  {row_str}")


# ---------------------------------------------------------------------------
# Model loader
# ---------------------------------------------------------------------------

def load_model(device: torch.device) -> RoryModel:
    with open(TRAIN_STATS_PATH) as f:
        train_stats = json.load(f)
    meta = train_stats["meta"]

    means = meta["means"]
    stds  = meta["stds"]

    vitals_mlp   = VitalsMLP(hidden_dim=64, out_dim=128, dropout=0.0,
                              means=means, stds=stds)
    text_encoder = TextEncoder(out_dim=128, dropout=0.0, device=str(device))
    fusion       = FusionModel(vitals_dim=128, text_dim=128,
                                hidden_dim=256, dropout=0.0)
    model = RoryModel(vitals_mlp, text_encoder, fusion)

    state = torch.load(BEST_MODEL_PATH, map_location=device)
    model.load_state_dict(state)
    model.to(device)
    model.eval()
    return model


# ---------------------------------------------------------------------------
# Evaluate
# ---------------------------------------------------------------------------

def evaluate() -> None:
    print("=" * 60)
    print("  RORY — Held-Out Evaluation")
    print("=" * 60)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"\n  Device: {device}")

    # Load held-out set
    with open(HELD_OUT_PATH, encoding="utf-8") as f:
        held_cases: list[dict] = json.load(f)
    print(f"  Held-out cases: {len(held_cases)}")

    # Separate Rory from standard evaluation
    rory_cases    = [c for c in held_cases if c["patient_id"] == "RORY-2012-0330"]
    standard_cases = [c for c in held_cases if c["patient_id"] != "RORY-2012-0330"]
    print(f"  Standard cases: {len(standard_cases)}  |  Rory: {len(rory_cases)}")

    # Load model
    print("\n  Loading model...")
    model = load_model(device)

    # --- Standard evaluation ---
    y_true: list[int] = []
    y_pred: list[int] = []
    probas: list[list[float]] = []

    with torch.no_grad():
        for case in standard_cases:
            gt     = case["ground_truth"]
            triage = GT_TO_TRIAGE.get(gt, "ED")
            true_idx = LABEL_TO_IDX[triage]

            out   = model([case["vitals"]], [case["complaint_text"]])
            proba = out["proba"][0].cpu().tolist()          # [p_HOME, p_ED, p_911]
            pred  = int(out["proba"].argmax(1).item())

            y_true.append(true_idx)
            y_pred.append(pred)
            probas.append(proba)

    # Metrics
    accuracy = sum(1 for t, p in zip(y_true, y_pred) if t == p) / max(len(y_true), 1)
    prec, rec, f1 = precision_recall_f1(y_true, y_pred)
    macro_f1 = sum(f1) / len(f1)
    cm = confusion_matrix(y_true, y_pred)

    labels = ["HOME", "ED", "911"]

    print(f"\n  ─── Standard Held-Out Results ({len(standard_cases)} cases) ───")
    print(f"  Accuracy  : {accuracy:.4f}")
    print(f"  Macro F1  : {macro_f1:.4f}\n")
    print(f"  {'Class':<10}  {'Precision':>10}  {'Recall':>8}  {'F1':>8}")
    print(f"  {'─'*42}")
    for i, label in enumerate(labels):
        support = sum(1 for t in y_true if t == i)
        print(f"  {label:<10}  {prec[i]:>10.4f}  {rec[i]:>8.4f}  {f1[i]:>8.4f}  (n={support})")

    print(f"\n  Confusion matrix (rows=true, cols=pred):")
    print_confusion_matrix(cm, labels)

    # Misclassified 911 cases (safety-critical)
    missed_911 = [
        (i, standard_cases[i])
        for i in range(len(standard_cases))
        if y_true[i] == LABEL_TO_IDX["911"] and y_pred[i] != LABEL_TO_IDX["911"]
    ]
    if missed_911:
        print(f"\n  ⚠  MISSED 911 CASES ({len(missed_911)}) — safety-critical misses:")
        for idx, case in missed_911:
            pred_label = IDX_TO_LABEL[y_pred[idx]]
            print(f"     patient={case['patient_id']}  gt={case['ground_truth']}  pred={pred_label}  "
                  f"p_911={probas[idx][2]:.3f}")
    else:
        print(f"\n  ✓  No 911 cases missed (0 false negatives for 911)")

    # --- Rory Staunton spotlight ---
    print(f"\n  ─── Rory Staunton Case Spotlight ───")
    if not rory_cases:
        print("  ✗  Rory case not found in held-out set")
        return

    rory = rory_cases[0]
    with torch.no_grad():
        out   = model([rory["vitals"]], [rory["complaint_text"]])
        proba = out["proba"][0].cpu().tolist()
        pred  = IDX_TO_LABEL[int(out["proba"].argmax(1).item())]

    print(f"  patient_id    : {rory['patient_id']}")
    print(f"  age_months    : {rory['age_months']} (12 years)")
    print(f"  ground_truth  : {rory['ground_truth']}")
    print(f"  prediction    : {pred}")
    print(f"  p(HOME)       : {proba[0]:.4f}")
    print(f"  p(ED)         : {proba[1]:.4f}")
    print(f"  p(911)        : {proba[2]:.4f}")

    if pred == "911":
        print("  ✓  Rory correctly classified as 911")
    else:
        print(f"  ✗  Rory MISCLASSIFIED as {pred}  — model needs retraining")
        print("     Consider: more sepsis examples in Rory's age band,")
        print("     lower decision threshold for 911 class, or focal loss.")


if __name__ == "__main__":
    evaluate()