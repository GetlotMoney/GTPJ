"""Auxiliary loss template.

Use when the paper mechanism only adds an auxiliary objective. The total loss
must be unchanged when lambda_trial_loss is zero.
"""

from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F


class TrialAuxiliaryLoss(nn.Module):
    template_family = "auxiliary_loss"

    def __init__(self, weight: float = 0.0):
        super().__init__()
        self.weight = float(weight)

    def forward(self, anchor: torch.Tensor, positive: torch.Tensor) -> dict[str, torch.Tensor]:
        """Return a weighted auxiliary loss without changing existing losses."""
        raw = 1.0 - F.cosine_similarity(anchor, positive.detach(), dim=-1).mean()
        weighted = anchor.new_tensor(self.weight) * raw
        return {
            "loss_trial_aux_raw": raw,
            "loss_trial_aux": weighted,
        }


def add_to_total_loss(total_loss: torch.Tensor, loss_pack: dict[str, torch.Tensor]) -> torch.Tensor:
    return total_loss + loss_pack["loss_trial_aux"]
