"""
train.py — RORY Hackathon, Backend A
======================================
Training loop for the RORY triage model.

Usage (from repo root, venv activated):
    python backend_a/models/train.py

Outputs:
    backend_a/models/weights/best_model.pt   — best val-loss checkpoint
    backend_a/models/weights/final_model.pt  — end-of-training weights
    backend_a/models/weights/train_stats.json

Notes
-----
- Runs on AMD ROCm via PyTorch (torch.cuda → ROCm backend transparent)
- Bio_ClinicalBERT frozen; only VitalsMLP + TextEncoder.head + FusionModel train
- Class-weighted CrossEntropy to handle imbalance (60 sepsis : 140 mimic)
- Cosine LR schedule with warm restarts
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset

# Local imports — run from repo root or with backend_a on PYTHONPATH
from models.vitals_mlp import VitalsMLP
from models.text_encoder import TextEncoder
from models.fusion import FusionModel, RoryModel, LABEL_TO_IDX

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT   = Path(__file__).parent.parent
DATA_DIR    = REPO_ROOT / "data"
WEIGHTS_DIR = Path(__file__).parent / "weights"
WEIGHTS_DIR.mkdir(exist_ok=True)

HERO_COHORT_PATH = DATA_DIR / "hero_cohort.json"

# ---------------------------------------------------------------------------
# Hyperparameters
# ---------------------------------------------------------------------------
BATCH_SIZE    = 16
EPOCHS        = 40
LR            = 3e-4
WEIGHT_DECAY  = 1e-4
VAL_FRACTION  = 0.10      # 10% of 180 = 18 validation cases
DROPOUT       = 0.3
HIDDEN_DIM    = 64
EMBED_DIM     = 128

# Ground-truth → triage label mapping
GT_TO_TRIAGE: dict[str, str] = {
    "sepsis":         "911",
    "appendicitis":   "911",
    "strep":          "ED",
    "gastroenteritis":"ED",
    "kawasaki":       "ED",
    "uti":            "ED",
    "viral_syndrome": "HOME",
    "influenza":      "HOME",
    "otitis_media":   "HOME",
}


# ---------------------------------------------------------------------------
# Dataset
# ---------------------------------------------------------------------------

class TriageDataset(Dataset):
    """
    Wraps a list of case dicts into a PyTorch Dataset.

    Each item returns:
        vitals_dict  : dict[str, float|None]
        complaint    : str
        label_idx    : int  (0=HOME, 1=ED, 2=911)
    """

    def __init__(self, cases: list[dict]) -> None:
        self.cases = cases

    def __len__(self) -> int:
        return len(self.cases)

    def __getitem__(self, idx: int) -> tuple[dict, str, int]:
        case = self.cases[idx]
        vitals = case["vitals"]
        text   = case["complaint_text"]
        gt     = case["ground_truth"]
        triage = GT_TO_TRIAGE.get(gt, "ED")
        label  = LABEL_TO_IDX[triage]
        return vitals, text, label


def collate_fn(batch):
    vitals_list = [item[0] for item in batch]
    texts       = [item[1] for item in batch]
    labels      = torch.tensor([item[2] for item in batch], dtype=torch.long)
    return vitals_list, texts, labels


# ---------------------------------------------------------------------------
# Device
# ---------------------------------------------------------------------------

def get_device() -> torch.device:
    if torch.cuda.is_available():
        dev = torch.device("cuda")
        name = torch.cuda.get_device_name(0)
        print(f"  GPU: {name}")
    else:
        dev = torch.device("cpu")
        print("  GPU: not available, using CPU")
    return dev


# ---------------------------------------------------------------------------
# Class weights
# ---------------------------------------------------------------------------

def compute_class_weights(cases: list[dict], device: torch.device) -> torch.Tensor:
    """Inverse-frequency weighting for HOME / ED / 911."""
    counts = [0, 0, 0]
    for case in cases:
        triage = GT_TO_TRIAGE.get(case["ground_truth"], "ED")
        counts[LABEL_TO_IDX[triage]] += 1

    total = sum(counts)
    weights = [total / (3 * max(c, 1)) for c in counts]
    print(f"  Class counts  HOME={counts[0]}  ED={counts[1]}  911={counts[2]}")
    print(f"  Class weights HOME={weights[0]:.2f}  ED={weights[1]:.2f}  911={weights[2]:.2f}")
    return torch.tensor(weights, dtype=torch.float32, device=device)


# ---------------------------------------------------------------------------
# Train / eval step
# ---------------------------------------------------------------------------

def run_epoch(
    model: RoryModel,
    loader: DataLoader,
    criterion: nn.CrossEntropyLoss,
    optimizer: optim.Optimizer | None,
    device: torch.device,
    training: bool,
) -> tuple[float, float]:
    """Returns (avg_loss, accuracy)."""
    model.train(training)
    total_loss = 0.0
    correct = 0
    n = 0

    with torch.set_grad_enabled(training):
        for vitals_list, texts, labels in loader:
            labels = labels.to(device)

            out    = model(vitals_list, texts)
            logits = out["logits"]
            loss   = criterion(logits, labels)

            if training:
                optimizer.zero_grad()
                loss.backward()
                nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
                optimizer.step()

            total_loss += loss.item() * len(labels)
            correct    += (logits.argmax(1) == labels).sum().item()
            n          += len(labels)

    return total_loss / max(n, 1), correct / max(n, 1)


# ---------------------------------------------------------------------------
# Main training loop
# ---------------------------------------------------------------------------

def train() -> None:
    print("=" * 60)
    print("  RORY — Model Training")
    print("=" * 60)

    device = get_device()

    # --- Load cohort ---
    with open(HERO_COHORT_PATH, encoding="utf-8") as f:
        all_cases: list[dict] = json.load(f)
    print(f"\n  Loaded {len(all_cases)} training cases from {HERO_COHORT_PATH.name}")

    # --- Train / val split (last 10% as val, deterministic) ---
    n_val   = max(1, int(len(all_cases) * VAL_FRACTION))
    n_train = len(all_cases) - n_val
    # Shuffle deterministically
    rng = np.random.default_rng(42)
    shuffled = rng.permutation(len(all_cases)).tolist()
    train_cases = [all_cases[i] for i in shuffled[:n_train]]
    val_cases   = [all_cases[i] for i in shuffled[n_train:]]
    print(f"  Train: {len(train_cases)}  Val: {len(val_cases)}")

    # --- Class weights ---
    class_weights = compute_class_weights(train_cases, device)

    # --- Datasets & loaders ---
    train_ds = TriageDataset(train_cases)
    val_ds   = TriageDataset(val_cases)
    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True,
                              collate_fn=collate_fn, drop_last=False)
    val_loader   = DataLoader(val_ds,   batch_size=BATCH_SIZE, shuffle=False,
                              collate_fn=collate_fn)

    # --- Compute imputation stats from training data ---
    means, stds = VitalsMLP.compute_cohort_stats(train_cases)
    print(f"\n  Cohort vital means: {means}")

    # --- Model ---
    vitals_mlp   = VitalsMLP(hidden_dim=HIDDEN_DIM, out_dim=EMBED_DIM,
                              dropout=DROPOUT, means=means, stds=stds)
    text_encoder = TextEncoder(out_dim=EMBED_DIM, dropout=DROPOUT,
                                device=str(device))
    fusion       = FusionModel(vitals_dim=EMBED_DIM, text_dim=EMBED_DIM,
                                hidden_dim=EMBED_DIM * 2, dropout=DROPOUT)
    model = RoryModel(vitals_mlp, text_encoder, fusion).to(device)

    # Trainable param count
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total     = sum(p.numel() for p in model.parameters())
    print(f"\n  Parameters: {trainable:,} trainable / {total:,} total "
          f"(BERT frozen)")

    # --- Optimizer & scheduler ---
    # Only pass params that require grad
    params = [p for p in model.parameters() if p.requires_grad]
    optimizer = optim.AdamW(params, lr=LR, weight_decay=WEIGHT_DECAY)
    scheduler = optim.lr_scheduler.CosineAnnealingWarmRestarts(
        optimizer, T_0=10, T_mult=2, eta_min=1e-6
    )

    criterion = nn.CrossEntropyLoss(weight=class_weights)

    # --- Training ---
    print(f"\n  Training for {EPOCHS} epochs...\n")
    best_val_loss = float("inf")
    stats: list[dict] = []

    for epoch in range(1, EPOCHS + 1):
        t0 = time.time()

        train_loss, train_acc = run_epoch(
            model, train_loader, criterion, optimizer, device, training=True
        )
        val_loss, val_acc = run_epoch(
            model, val_loader, criterion, None, device, training=False
        )

        scheduler.step()
        elapsed = time.time() - t0

        is_best = val_loss < best_val_loss
        if is_best:
            best_val_loss = val_loss
            torch.save(model.state_dict(), WEIGHTS_DIR / "best_model.pt")
            best_marker = " ← best"
        else:
            best_marker = ""

        print(
            f"  Ep {epoch:3d}/{EPOCHS}  "
            f"train_loss={train_loss:.4f}  train_acc={train_acc:.3f}  "
            f"val_loss={val_loss:.4f}  val_acc={val_acc:.3f}  "
            f"lr={scheduler.get_last_lr()[0]:.2e}  "
            f"({elapsed:.1f}s){best_marker}"
        )

        stats.append({
            "epoch": epoch,
            "train_loss": round(train_loss, 5),
            "train_acc":  round(train_acc, 4),
            "val_loss":   round(val_loss, 5),
            "val_acc":    round(val_acc, 4),
        })

    # --- Save final weights ---
    torch.save(model.state_dict(), WEIGHTS_DIR / "final_model.pt")

    # --- Save imputation stats alongside weights (needed at inference time) ---
    meta = {
        "means": means,
        "stds":  stds,
        "label_to_idx": LABEL_TO_IDX,
        "best_val_loss": round(best_val_loss, 5),
        "epochs": EPOCHS,
        "train_size": len(train_cases),
        "val_size":   len(val_cases),
    }
    with open(WEIGHTS_DIR / "train_stats.json", "w") as f:
        json.dump({"meta": meta, "history": stats}, f, indent=2)

    print(f"\n  Best val loss: {best_val_loss:.4f}")
    print(f"  Weights saved → {WEIGHTS_DIR}")
    print("  Done.\n")


if __name__ == "__main__":
    train()