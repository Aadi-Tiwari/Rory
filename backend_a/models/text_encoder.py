"""
text_encoder.py — RORY Hackathon, Backend A
============================================
Complaint text encoder: Bio_ClinicalBERT (frozen) + 2-layer trainable MLP head.

Bio_ClinicalBERT (emilyalsentzer/Bio_ClinicalBERT) was trained on MIMIC-III
clinical notes. Suitability for pediatric complaints requires evaluation.

Architecture:
    BERT [CLS] pooling (768-dim, frozen)
    → Linear(768, 256) → ReLU → Dropout(0.3)
    → Linear(256, 128) → ReLU
    → 128-dim embedding

Only the MLP head trains; BERT weights stay frozen to prevent overfitting on
our small 180-case cohort and to keep training fast on ROCm.
"""

from __future__ import annotations

import torch
import torch.nn as nn

# Lazy import to avoid hard dep at import time when running tests
_transformers_available: bool | None = None


def _check_transformers() -> None:
    global _transformers_available
    if _transformers_available is None:
        try:
            import transformers  # noqa: F401
            _transformers_available = True
        except ImportError:
            _transformers_available = False
    if not _transformers_available:
        raise ImportError(
            "transformers package required: pip install transformers"
        )


MODEL_NAME = "emilyalsentzer/Bio_ClinicalBERT"
MODEL_REVISION = "d5892b39a4adaed74b92212a44081509db72f87b"
BERT_DIM   = 768


class TextEncoder(nn.Module):
    """
    Bio_ClinicalBERT (frozen) + trainable 2-layer projection head.

    Parameters
    ----------
    hidden_dim : int
        Intermediate projection dimension (default 256).
    out_dim : int
        Output embedding dimension — must match vitals encoder output (128).
    dropout : float
        Dropout rate for MLP head (default 0.3).
    max_length : int
        Max tokenizer length (default 128 tokens — adequate for short complaints).
    device : str | None
        If None, auto-detects cuda/mps/cpu.
    """

    def __init__(
        self,
        hidden_dim: int = 256,
        out_dim: int = 128,
        dropout: float = 0.3,
        max_length: int = 128,
        device: str | None = None,
        revision: str = MODEL_REVISION,
    ) -> None:
        super().__init__()
        _check_transformers()

        from transformers import AutoModel, AutoTokenizer

        self.max_length = max_length
        self._device = device or _auto_device()

        # Load tokenizer and BERT
        self.tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, revision=revision)
        self.bert = AutoModel.from_pretrained(MODEL_NAME, revision=revision)

        # Freeze all BERT parameters
        for param in self.bert.parameters():
            param.requires_grad = False

        # Trainable MLP head
        self.head = nn.Sequential(
            nn.Linear(BERT_DIM, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, out_dim),
            nn.ReLU(),
        )

    # ------------------------------------------------------------------
    # Forward
    # ------------------------------------------------------------------

    def forward(self, texts: list[str] | torch.Tensor) -> torch.Tensor:
        """
        Args:
            texts: List of complaint strings OR a pre-computed BERT
                   [CLS] tensor of shape (B, 768).
        Returns:
            Tensor of shape (B, 128).
        """
        if isinstance(texts, torch.Tensor):
            cls_emb = texts
        else:
            cls_emb = self._encode_texts(texts)

        return self.head(cls_emb)

    # ------------------------------------------------------------------
    # Text → [CLS] embedding (no grad, BERT is frozen)
    # ------------------------------------------------------------------

    @torch.no_grad()
    def _encode_texts(self, texts: list[str]) -> torch.Tensor:
        """Tokenize and run through frozen BERT, return [CLS] embeddings."""
        enc = self.tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=self.max_length,
            return_tensors="pt",
        )
        # Move to device
        enc = {k: v.to(self._device) for k, v in enc.items()}
        self.bert.to(self._device)

        out = self.bert(**enc)
        # [CLS] token = first token of last hidden state
        cls_emb = out.last_hidden_state[:, 0, :]   # (B, 768)
        return cls_emb

    # ------------------------------------------------------------------
    # Convenience: encode without head (for DBSCAN / drift features)
    # ------------------------------------------------------------------

    def encode_raw(self, texts: list[str]) -> torch.Tensor:
        """Return raw 768-dim [CLS] embeddings (no MLP head)."""
        return self._encode_texts(texts)

    # ------------------------------------------------------------------
    # Device helper
    # ------------------------------------------------------------------

    def to(self, device, *args, **kwargs):
        self._device = str(device)
        self.bert.to(device)
        return super().to(device, *args, **kwargs)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _auto_device() -> str:
    if torch.cuda.is_available():
        return "cuda"
    # ROCm exposes as CUDA
    try:
        if torch.backends.mps.is_available():
            return "mps"
    except AttributeError:
        pass
    return "cpu"
