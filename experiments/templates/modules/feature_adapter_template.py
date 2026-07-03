"""Feature adapter template.

Use when the mechanism changes visual, text, or class-prototype features before
the existing scorer. The adapter must preserve feature compatibility with the
base scorer and must not alter class order or label mapping.
"""

from __future__ import annotations

import torch
import torch.nn as nn


class TrialFeatureAdapter(nn.Module):
    template_family = "feature_adapter"

    def __init__(self, dim: int, hidden_ratio: float = 0.25, enabled: bool = False):
        super().__init__()
        self.enabled = bool(enabled)
        hidden = max(1, int(dim * float(hidden_ratio)))
        self.adapter = nn.Sequential(
            nn.Linear(dim, hidden),
            nn.GELU(),
            nn.Linear(hidden, dim),
        )
        self.scale = nn.Parameter(torch.tensor(0.0))

    def forward(self, features: torch.Tensor) -> torch.Tensor:
        """Return features with shape unchanged, e.g. [B, D] or [C, D]."""
        if not self.enabled:
            return features
        delta = self.adapter(features)
        return features + torch.tanh(self.scale) * delta


def integration_note() -> str:
    return (
        "Attach after existing feature construction and before the scorer. "
        "Switch off must return the exact input tensor."
    )
