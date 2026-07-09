"""Feature adapter（特征适配）模板。

当机制要在既有 scorer 之前改变 visual/text/class-prototype feature 时使用。
adapter 必须保持与 base scorer 的特征兼容性，且不能改变 class order 或 label mapping。
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
        """返回 shape 不变的 features，例如 [B（图片/样本数量）, D（特征维度）] 或 [C（类别数量）, D（特征维度）]。"""
        if not self.enabled:
            return features
        delta = self.adapter(features)
        return features + torch.tanh(self.scale) * delta


def integration_note() -> str:
    return (
        "接在既有 feature 构造之后、scorer 之前。"
        "关闭开关时必须原样返回输入 tensor。"
    )
