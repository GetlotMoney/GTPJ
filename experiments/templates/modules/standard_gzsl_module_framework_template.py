"""Standard GZSL module framework template for GTPJ trials.

Copy this file into a trial branch only after `module_source.md` and
`implementation.md` explain the source, base version, attachment point, and
GZSL risk.

Protected semantics:
- dataset split stays xlsa17 by default
- train uses seen classes only
- evaluation uses seen + unseen classes
- logits stay [B (image/sample count), C (class count)]
- metrics stay U, S, H, ZS
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
    """Base class for trial modules that must not alter GZSL semantics."""

    template_family = "base"

    def __init__(self, enabled: bool = False):
        super().__init__()
        self.enabled = bool(enabled)

    def baseline_off(self, value: torch.Tensor) -> torch.Tensor:
        """Return the unchanged baseline value when the module is disabled."""
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
    """Build protected state from the existing dataloader; do not hand-write class order."""
    return GZSLProtectedState(
        dataset_name=getattr(dataloader, "dataset", "CUB"),
        split_name="xlsa17/att_splits.mat",
        seen_classes=dataloader.seenclasses.long(),
        unseen_classes=dataloader.unseenclasses.long(),
        num_classes=int(dataloader.ntrain_class + dataloader.ntest_class),
    )
