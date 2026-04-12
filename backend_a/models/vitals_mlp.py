"""
vitals_mlp.py — RORY Hackathon, Backend A
==========================================
Vitals encoder: 3-layer MLP (64 hidden, dropout 0.3).
Handles None vitals via learned mean imputation (mask-augmented input).

Input features (10 dims = 5 vitals + 5 missingness indicators):
    [hr, rr, temp_f, spo2, cap_refill_s,
     hr_missing, rr_missing, temp_f_missing, spo2_missing, cap_refill_s_missing]

Output: 128-dim embedding.
"""

from __future__ import annotations

import torch
import torch.nn as nn


VITAL_KEYS = ["hr", "rr", "temp_f", "spo2", "cap_refill_s"]

# Population-level means for imputation (derived from PECARN / normal cohort).
# These are approximate midpoints; the trainer will override with cohort means.
DEFAULT_MEANS: dict[str, float] = {
    "hr":           110.0,
    "rr":            26.0,
    "temp_f":        98.6,
    "spo2":          98.0,
    "cap_refill_s":   1.8,
}

# Population-level stds for z-score normalization
DEFAULT_STDS: dict[str, float] = {
    "hr":           30.0,
    "rr":           10.0,
    "temp_f":        1.5,
    "spo2":          3.0,
    "cap_refill_s":  0.8,
}


class VitalsMLP(nn.Module):
    """
    Mask-augmented MLP for pediatric vital signs.

    Architecture:
        Input(10) → Linear(64) → ReLU → Dropout(0.3)
                  → Linear(64) → ReLU → Dropout(0.3)
                  → Linear(128) → ReLU
    """

    def __init__(
        self,
        hidden_dim: int = 64,
        out_dim: int = 128,
        dropout: float = 0.3,
        means: dict[str, float] | None = None,
        stds: dict[str, float] | None = None,
    ) -> None:
        super().__init__()

        self.vital_keys = VITAL_KEYS
        n_vitals = len(VITAL_KEYS)
        in_dim = n_vitals * 2  # vitals + missingness mask

        # Register imputation stats as buffers so they save with state_dict
        means_ = means or DEFAULT_MEANS
        stds_  = stds  or DEFAULT_STDS

        self.register_buffer(
            "means",
            torch.tensor([means_[k] for k in VITAL_KEYS], dtype=torch.float32),
        )
        self.register_buffer(
            "stds",
            torch.tensor([stds_[k]  for k in VITAL_KEYS], dtype=torch.float32),
        )

        self.net = nn.Sequential(
            nn.Linear(in_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, out_dim),
            nn.ReLU(),
        )

    # ------------------------------------------------------------------
    # Input preparation
    # ------------------------------------------------------------------

    def prepare_input(self, vitals_batch: list[dict]) -> torch.Tensor:
        """
        Convert a list of vital-sign dicts (with possible None values)
        into a float tensor of shape (B, 10).

        Missingness mask: 1.0 if the value was None (imputed), 0.0 if observed.
        Imputed values are replaced with population mean before z-scoring.
        """
        rows = []
        for vd in vitals_batch:
            vals = []
            mask = []
            for k in VITAL_KEYS:
                v = vd.get(k)
                if v is None:
                    vals.append(0.0)   # placeholder; will use mean after z-score
                    mask.append(1.0)
                else:
                    vals.append(float(v))
                    mask.append(0.0)
            rows.append(vals + mask)

        x = torch.tensor(rows, dtype=torch.float32).to(self.means.device)
        # x[:, :n_vitals] = raw values (0 where missing)
        # Replace missing with mean, then z-score
        n = len(VITAL_KEYS)
        missing = x[:, n:] == 1.0                          # (B, n)
        x[:, :n] = torch.where(missing, self.means.unsqueeze(0), x[:, :n])
        x[:, :n] = (x[:, :n] - self.means) / (self.stds + 1e-6)

        return x  # (B, 10)

    # ------------------------------------------------------------------
    # Forward
    # ------------------------------------------------------------------

    def forward(self, vitals_batch: list[dict] | torch.Tensor) -> torch.Tensor:
        """
        Args:
            vitals_batch: Either a list of vital-sign dicts OR a pre-built
                          float tensor of shape (B, 10).
        Returns:
            Tensor of shape (B, 128).
        """
        if isinstance(vitals_batch, torch.Tensor):
            x = vitals_batch
        else:
            x = self.prepare_input(vitals_batch)

        return self.net(x)

    # ------------------------------------------------------------------
    # Utility: compute cohort means/stds for imputation calibration
    # ------------------------------------------------------------------

    @staticmethod
    def compute_cohort_stats(cases: list[dict]) -> tuple[dict, dict]:
        """
        Given a list of training case dicts (each with a 'vitals' sub-dict),
        compute per-vital mean and std from observed (non-None) values.
        Returns (means_dict, stds_dict).
        """
        from collections import defaultdict
        import statistics

        buckets: dict[str, list[float]] = defaultdict(list)
        for case in cases:
            for k in VITAL_KEYS:
                v = case.get("vitals", {}).get(k)
                if v is not None:
                    buckets[k].append(float(v))

        means = {k: statistics.mean(v) if v else DEFAULT_MEANS[k] for k, v in buckets.items()}
        stds  = {k: statistics.stdev(v) if len(v) > 1 else DEFAULT_STDS[k] for k, v in buckets.items()}
        return means, stds