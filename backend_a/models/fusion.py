"""
fusion.py — RORY Hackathon, Backend A
======================================
Late-fusion model: concatenates vitals + text embeddings → 3-class triage.

Architecture:
    vitals_emb (128) + text_emb (128)
    → concat (256)
    → Linear(256, 128) → ReLU → Dropout(0.3)
    → Linear(128, 64)  → ReLU → Dropout(0.3)
    → Linear(64, 3)
    → Softmax → {HOME, ED, 911}

Class indices:
    0 = HOME
    1 = ED
    2 = 911
"""

from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F

LABEL_TO_IDX: dict[str, int] = {"HOME": 0, "ED": 1, "911": 2}
IDX_TO_LABEL: dict[int, str] = {v: k for k, v in LABEL_TO_IDX.items()}


class FusionModel(nn.Module):
    """
    Concat-fusion classifier combining vitals and text embeddings.

    Parameters
    ----------
    vitals_dim : int   Dimensionality of vitals embedding (default 128).
    text_dim   : int   Dimensionality of text embedding (default 128).
    hidden_dim : int   Hidden width of fusion MLP (default 128).
    n_classes  : int   Number of triage classes (default 3: HOME/ED/911).
    dropout    : float Dropout rate (default 0.3).
    """

    def __init__(
        self,
        vitals_dim: int = 128,
        text_dim: int = 128,
        hidden_dim: int = 128,
        n_classes: int = 3,
        dropout: float = 0.3,
    ) -> None:
        super().__init__()

        in_dim = vitals_dim + text_dim  # 256

        self.classifier = nn.Sequential(
            nn.Linear(in_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, hidden_dim // 2),   # 64
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, n_classes),
        )

        self.label_to_idx = LABEL_TO_IDX
        self.idx_to_label = IDX_TO_LABEL

    # ------------------------------------------------------------------
    # Forward
    # ------------------------------------------------------------------

    def forward(
        self,
        vitals_emb: torch.Tensor,
        text_emb: torch.Tensor,
    ) -> torch.Tensor:
        """
        Args:
            vitals_emb: (B, 128) float tensor from VitalsMLP
            text_emb:   (B, 128) float tensor from TextEncoder
        Returns:
            logits: (B, 3) — apply softmax externally for probabilities
        """
        x = torch.cat([vitals_emb, text_emb], dim=1)   # (B, 256)
        return self.classifier(x)

    # ------------------------------------------------------------------
    # Predict convenience
    # ------------------------------------------------------------------

    def predict_proba(
        self,
        vitals_emb: torch.Tensor,
        text_emb: torch.Tensor,
    ) -> torch.Tensor:
        """Returns softmax probabilities of shape (B, 3)."""
        logits = self.forward(vitals_emb, text_emb)
        return F.softmax(logits, dim=1)

    def predict(
        self,
        vitals_emb: torch.Tensor,
        text_emb: torch.Tensor,
    ) -> list[str]:
        """Returns list of label strings: ['HOME', 'ED', '911', ...]."""
        proba = self.predict_proba(vitals_emb, text_emb)
        indices = proba.argmax(dim=1).tolist()
        return [self.idx_to_label[i] for i in indices]

    # ------------------------------------------------------------------
    # Embedding convenience: concat embeddings (for DBSCAN)
    # ------------------------------------------------------------------

    @staticmethod
    def fuse_embeddings(
        vitals_emb: torch.Tensor,
        text_emb: torch.Tensor,
    ) -> torch.Tensor:
        """Returns the raw 256-dim fused embedding before classification."""
        return torch.cat([vitals_emb, text_emb], dim=1)


# ---------------------------------------------------------------------------
# Full pipeline wrapper (used by inference/predict.py)
# ---------------------------------------------------------------------------

class RoryModel(nn.Module):
    """
    End-to-end wrapper: VitalsMLP + TextEncoder + FusionModel.

    Holds all three sub-modules so a single state_dict covers everything.
    TextEncoder.bert stays frozen; only head + VitalsMLP + FusionModel train.
    """

    def __init__(self, vitals_mlp, text_encoder, fusion) -> None:
        super().__init__()
        self.vitals_mlp   = vitals_mlp
        self.text_encoder = text_encoder
        self.fusion       = fusion

    def forward(
        self,
        vitals_batch: list[dict] | torch.Tensor,
        texts: list[str] | torch.Tensor,
    ) -> dict[str, torch.Tensor]:
        """
        Args:
            vitals_batch : list of vital dicts (or pre-built (B,10) tensor)
            texts        : list of complaint strings (or pre-built (B,768) tensor)
        Returns:
            dict with keys:
                'logits'      : (B, 3)
                'proba'       : (B, 3)
                'vitals_emb'  : (B, 128)
                'text_emb'    : (B, 128)
                'fused_emb'   : (B, 256)
        """
        v_emb = self.vitals_mlp(vitals_batch)         # (B, 128)
        t_emb = self.text_encoder(texts)              # (B, 128)
        logits = self.fusion(v_emb, t_emb)            # (B, 3)
        proba  = F.softmax(logits, dim=1)             # (B, 3)
        fused  = FusionModel.fuse_embeddings(v_emb, t_emb)  # (B, 256)

        return {
            "logits":     logits,
            "proba":      proba,
            "vitals_emb": v_emb,
            "text_emb":   t_emb,
            "fused_emb":  fused,
        }