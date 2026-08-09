"""Fusion gate（融合门控）模板。

当机制要改变既有 score 或 feature 的融合方式时使用。
gate 默认必须回到 base coefficient，并且必须保持 logits shape 不变。
"""

from __future__ import annotations

import torch
import torch.nn as nn


class TrialFusionGate(nn.Module):
    template_family = "fusion_gate"

    def __init__(self, dim: int, base_weight: float, enabled: bool = False):
        super().__init__()
        self.enabled = bool(enabled)
        self.register_buffer("base_weight", torch.tensor(float(base_weight)))
        self.gate = nn.Sequential(
            nn.Linear(dim, max(1, dim // 4)),
            nn.GELU(),
            nn.Linear(max(1, dim // 4), 1),
            nn.Sigmoid(),
        )

    def forward(
        self,
        base_score: torch.Tensor,
        new_score: torch.Tensor,
        sample_feature: torch.Tensor,
    ) -> torch.Tensor:
        """融合两个 shape 相同的 score tensor，shape 为 [B（图片/样本数量）, C（类别数量）]。"""
        if base_score.shape != new_score.shape:
            raise ValueError(f"score shapes must match, got {base_score.shape} and {new_score.shape}")
        if not self.enabled:
            weight = self.base_weight.to(base_score.device, base_score.dtype)
            return base_score + weight * new_score
        gate = self.gate(sample_feature).to(base_score.dtype)
        return base_score + gate * new_score
