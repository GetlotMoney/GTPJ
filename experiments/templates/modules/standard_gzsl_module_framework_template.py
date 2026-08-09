"""GTPJ trial 的标准 GZSL module framework 模板。

只有在 `module_source.md` 和 `implementation.md` 已经解释来源、base version、
attachment point 和 GZSL 风险之后，才能把本文件复制进 trial 分支。

受保护语义：
- dataset split 默认保持 xlsa17；
- train 只使用 seen classes；
- evaluation 使用 seen + unseen classes；
- logits 保持 [B（图片/样本数量）, C（类别数量）]；
- metrics 保持 U、S、H、ZS。
"""

from __future__ import annotations

from dataclasses import dataclass

import torch
import torch.nn as nn


@dataclass(frozen=True)
class GZSLProtectedState:
    dataset_name: str
    split_name: str
    seen_classes: torch.Tensor
    unseen_classes: torch.Tensor
    num_classes: int
    metric_semantics: str = "standard_gzsl_u_s_h_zs"


class GZSLModuleBase(nn.Module):
    """trial module 的基类；不得改变 GZSL 语义。"""

    template_family = "base"

    def __init__(self, enabled: bool = False):
        super().__init__()
        self.enabled = bool(enabled)

    def baseline_off(self, value: torch.Tensor) -> torch.Tensor:
        """模块关闭时返回未改变的 baseline value。"""
        return value

    @staticmethod
    def assert_logits_shape(logits: torch.Tensor, batch_size: int, class_count: int) -> None:
        expected = (int(batch_size), int(class_count))
        actual = tuple(logits.shape)
        if actual != expected:
            raise ValueError(
                f"logits must be [B (image/sample count), C (class count)]={expected}, got {actual}"
            )

    @staticmethod
    def assert_protected_state(state: GZSLProtectedState) -> None:
        if state.metric_semantics != "standard_gzsl_u_s_h_zs":
            raise ValueError("metric semantics changed; this is not a normal module trial")
        if state.seen_classes.ndim != 1 or state.unseen_classes.ndim != 1:
            raise ValueError("seen/unseen class tensors must be 1-D class-index lists")
        if int(state.num_classes) <= int(state.seen_classes.numel()):
            raise ValueError("GZSL requires seen + unseen classes at evaluation")


def build_protected_state(dataloader) -> GZSLProtectedState:
    """从既有 dataloader 构造 protected state；不要手写 class order。"""
    return GZSLProtectedState(
        dataset_name=getattr(dataloader, "dataset", "CUB"),
        split_name="xlsa17/att_splits.mat",
        seen_classes=dataloader.seenclasses.long(),
        unseen_classes=dataloader.unseenclasses.long(),
        num_classes=int(dataloader.ntrain_class + dataloader.ntest_class),
    )
