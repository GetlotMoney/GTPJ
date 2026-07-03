"""Composite module template.

Use when a paper mechanism is inseparable across two or more module families,
for example feature_adapter + fusion_gate. The training entry must see one
standard composite slot instead of scattered edits across old code.

Protected semantics:
- all components default to disabled
- all-disabled behavior must match the selected base_version
- feature/logit tensor shapes must stay unchanged unless the trial is marked
  as a high-risk architecture change
- split, label map, class order, and U/S/H/ZS semantics are read-only
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

import torch
import torch.nn as nn


ALLOWED_COMPONENT_FAMILIES = {
    "feature_adapter",
    "fusion_gate",
    "auxiliary_loss",
    "sampler_or_data_view",
}

ALLOWED_COMPOSITION_MODES = {
    "sequential",
    "parallel",
    "gated",
    "residual",
}

STANDARD_TRIAL_OUTPUT_KEYS = {"features", "logits", "losses", "debug"}


@dataclass(frozen=True)
class CompositeComponentSpec:
    name: str
    template_family: str
    attachment_point: str
    enabled_key: str
    source_ref: str = ""


@dataclass(frozen=True)
class CompositePlan:
    """Trial-local plan for a composite innovation."""

    components: tuple[CompositeComponentSpec, ...]
    composition_mode: str
    baseline_off_explanation: str
    risk: str = "high"


def assert_composite_plan(plan: CompositePlan) -> None:
    if len(plan.components) < 2:
        raise ValueError("composite trials require at least two component specs")
    if plan.composition_mode not in ALLOWED_COMPOSITION_MODES:
        raise ValueError(f"unsupported composition_mode: {plan.composition_mode}")
    for component in plan.components:
        if component.template_family not in ALLOWED_COMPONENT_FAMILIES:
            raise ValueError(f"unsupported component family: {component.template_family}")
        if not component.attachment_point:
            raise ValueError(f"component {component.name} missing attachment_point")
        if not component.enabled_key:
            raise ValueError(f"component {component.name} missing enabled_key")
    if not plan.baseline_off_explanation:
        raise ValueError("composite trials must explain all-disabled baseline equivalence")


class TrialCompositeModule(nn.Module):
    """One standard slot that owns multiple trial components."""

    template_family = "composite"

    def __init__(
        self,
        components: Mapping[str, nn.Module],
        composition_mode: str,
        enabled: bool = False,
    ):
        super().__init__()
        if composition_mode not in ALLOWED_COMPOSITION_MODES:
            raise ValueError(f"unsupported composition_mode: {composition_mode}")
        self.enabled = bool(enabled)
        self.composition_mode = composition_mode
        self.components = nn.ModuleDict(dict(components))

    def all_components_disabled(self) -> bool:
        if not self.enabled:
            return True
        return all(not bool(getattr(component, "enabled", True)) for component in self.components.values())

    def has_enabled_family(self, template_family: str) -> bool:
        if self.all_components_disabled():
            return False
        return any(
            getattr(component, "template_family", "") == template_family
            and bool(getattr(component, "enabled", True))
            for component in self.components.values()
        )

    @staticmethod
    def assert_same_shape(name: str, before: torch.Tensor, after: torch.Tensor) -> None:
        if tuple(before.shape) != tuple(after.shape):
            raise ValueError(f"{name} changed shape from {tuple(before.shape)} to {tuple(after.shape)}")

    def apply_feature_components(self, features: torch.Tensor) -> torch.Tensor:
        """Apply feature-level components while preserving feature shape."""
        if self.all_components_disabled():
            return features
        current = features
        for name, component in self.components.items():
            if getattr(component, "template_family", "") != "feature_adapter":
                continue
            next_value = component(current)
            self.assert_same_shape(name, current, next_value)
            current = next_value
        return current

    def apply_score_components(
        self,
        base_score: torch.Tensor,
        candidate_scores: Mapping[str, torch.Tensor],
        sample_feature: torch.Tensor | None = None,
    ) -> torch.Tensor:
        """Fuse score-level components and keep logits shape [B, C]."""
        if self.all_components_disabled():
            return base_score
        current = base_score
        for name, component in self.components.items():
            if getattr(component, "template_family", "") != "fusion_gate":
                continue
            if name not in candidate_scores:
                raise ValueError(f"missing candidate score for fusion component: {name}")
            if sample_feature is None:
                raise ValueError("fusion components require sample_feature for gate input")
            next_value = component(current, candidate_scores[name], sample_feature)
            self.assert_same_shape(name, current, next_value)
            current = next_value
        return current

    def auxiliary_losses(self, context: Mapping[str, torch.Tensor]) -> dict[str, torch.Tensor]:
        """Collect auxiliary losses without changing the base total when weights are zero."""
        if self.all_components_disabled():
            return {}
        loss_pack: dict[str, torch.Tensor] = {}
        for name, component in self.components.items():
            if getattr(component, "template_family", "") != "auxiliary_loss":
                continue
            anchor = context.get(f"{name}.anchor")
            positive = context.get(f"{name}.positive")
            if anchor is None or positive is None:
                raise ValueError(f"missing auxiliary context for component: {name}")
            for key, value in component(anchor, positive).items():
                loss_pack[f"{name}.{key}"] = value
        return loss_pack

    def forward(
        self,
        features: torch.Tensor,
        logits: torch.Tensor | None = None,
        context: Mapping[str, Any] | None = None,
        candidate_scores: Mapping[str, torch.Tensor] | None = None,
    ) -> dict[str, object]:
        """Standard composite slot visible to the training framework.

        The caller should only consume `features`, `logits`, `losses`, and
        `debug`, regardless of how many components are active internally.
        """
        ctx: Mapping[str, Any] = context or {}
        debug: dict[str, object] = {
            "module_scope": "composite",
            "composition_mode": self.composition_mode,
            "all_components_disabled": self.all_components_disabled(),
        }

        adapted_features = self.apply_feature_components(features)
        debug["feature_components_enabled"] = self.has_enabled_family("feature_adapter")

        final_logits = logits
        if final_logits is None and self.has_enabled_family("fusion_gate"):
            raise ValueError("fusion components require base logits")
        if final_logits is not None:
            score_candidates = candidate_scores or ctx.get("candidate_scores", {})
            if not isinstance(score_candidates, Mapping):
                raise ValueError("candidate_scores must be a mapping")
            sample_feature = ctx.get("sample_feature")
            if sample_feature is None:
                sample_feature = adapted_features
            final_logits = self.apply_score_components(
                final_logits,
                score_candidates,
                sample_feature=sample_feature,
            )
        debug["fusion_components_enabled"] = self.has_enabled_family("fusion_gate")

        tensor_context = {key: value for key, value in ctx.items() if isinstance(value, torch.Tensor)}
        losses = self.auxiliary_losses(tensor_context)
        debug["auxiliary_components_enabled"] = self.has_enabled_family("auxiliary_loss")

        output: dict[str, object] = {
            "features": adapted_features,
            "logits": final_logits,
            "losses": losses,
            "debug": debug,
        }
        assert_standard_trial_output(output)
        return output


def assert_standard_trial_output(output: Mapping[str, object]) -> None:
    missing = STANDARD_TRIAL_OUTPUT_KEYS.difference(output.keys())
    if missing:
        raise ValueError(f"trial output missing standard keys: {sorted(missing)}")
    if output["losses"] is not None and not isinstance(output["losses"], Mapping):
        raise ValueError("trial output losses must be a mapping")
    if output["debug"] is not None and not isinstance(output["debug"], Mapping):
        raise ValueError("trial output debug must be a mapping")


def composition_note() -> str:
    return (
        "Use composite only when the mechanism cannot be split into separate trials. "
        "The main training code should call one composite slot returning features, "
        "logits, losses, and debug, and component switches must make the all-off "
        "path equivalent to the recorded base_version."
    )
