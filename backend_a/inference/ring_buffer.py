
"""
Per-patient ring buffer storing the last N embedding vectors.
Used by cluster_drift.py to detect sepsis trajectory over time.
"""

from __future__ import annotations

from collections import deque
from typing import Optional

import numpy as np

BUFFER_SIZE = 5


class RingBuffer:
    def __init__(self, maxlen: int = BUFFER_SIZE):
        self._buf: deque[np.ndarray] = deque(maxlen=maxlen)

    def push(self, embedding: np.ndarray) -> None:
        self._buf.append(embedding.copy())

    def get(self) -> list[np.ndarray]:
        return list(self._buf)

    def __len__(self) -> int:
        return len(self._buf)


# Global registry: patient_id -> RingBuffer
_registry: dict[str, RingBuffer] = {}


def get_buffer(patient_id: str) -> RingBuffer:
    if patient_id not in _registry:
        _registry[patient_id] = RingBuffer()
    return _registry[patient_id]


def push_embedding(patient_id: str, embedding: np.ndarray) -> RingBuffer:
    buf = get_buffer(patient_id)
    buf.push(embedding)
    return buf