"""V5 实验专属的低置信度局部增强包装。

母版仍负责生成全局分数、局部分数和全部辅助损失输入；本文件只重算
``final_logits``、``logits`` 与 ``clip_S_pp``，不修改正式母版源码。
"""

from __future__ import annotations

import math
from pathlib import Path
import sys

import torch
import torch.nn as nn
import torch.nn.functional as F


ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from model.MyModel import GTPJ  # noqa: E402


class ConfidenceLocalGateGTPJ(GTPJ):
    """只在全局分类置信度低时增强局部分支的 V5 包装。"""

    GATE_BETA = 0.05
    GATE_BIAS_INIT = -1.0
    GATE_SLOPE_INIT = 1.0

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        expected = {
            "gate_beta": self.GATE_BETA,
            "gate_bias_init": self.GATE_BIAS_INIT,
            "gate_slope_init": self.GATE_SLOPE_INIT,
        }
        for name, value in expected.items():
            configured = float(getattr(self.config, name, value))
            if configured != value:
                raise ValueError(f"本创新固定 {name}={value}，实际为 {configured}。")

        self.gate_beta = self.GATE_BETA
        self.gate_bias = nn.Parameter(torch.tensor(self.GATE_BIAS_INIT))
        raw_slope = math.log(math.expm1(self.GATE_SLOPE_INIT))
        self.gate_slope_raw = nn.Parameter(torch.tensor(raw_slope))

    def _compute_confidence_gate(self, global_logits, *, is_train):
        """返回 gate 与已脱离全局分支梯度的 top1-top2 margin。"""

        if global_logits.dim() != 2:
            raise ValueError("global_logits 必须是 [B, C]。")
        if is_train:
            confidence_logits = global_logits[
                :, self.seenclass.to(global_logits.device)
            ]
        else:
            confidence_logits = global_logits
        if confidence_logits.size(1) < 2:
            raise ValueError("置信度 margin 至少需要两个候选类别。")

        top_two = torch.topk(confidence_logits, k=2, dim=1).values
        margin = (top_two[:, 0] - top_two[:, 1]).detach()
        positive_slope = F.softplus(self.gate_slope_raw)
        gate = torch.sigmoid(self.gate_bias - positive_slope * margin)
        return gate, margin

    def forward(self, clip_features, is_train=False):
        base_output = super().forward(clip_features, is_train=is_train)
        global_logits = base_output["global_logits"]
        local_logits = base_output["local_logits"]
        gate, margin = self._compute_confidence_gate(
            global_logits, is_train=is_train
        )
        logit_scale = torch.clamp(self.logit_scale.exp(), max=100.0)
        final_logits = (
            global_logits
            + self.gate_beta
            * logit_scale
            * gate.unsqueeze(-1)
            * local_logits
        )
        logits = (
            final_logits[:, self.seenclass.to(final_logits.device)]
            if is_train
            else final_logits
        )

        output = dict(base_output)
        output.update(
            {
                "final_logits": final_logits,
                "logits": logits,
                "clip_S_pp": logits,
                "gate": gate,
                "gate_margin": margin,
                "gate_mean": gate.mean(),
                "gate_min": gate.min(),
                "gate_max": gate.max(),
            }
        )
        return output
