"""Sampler or data-view template.

Use only for high-risk mechanisms that change batch composition, patch/view
selection, or cache view choice. This template must not change xlsa17 splits,
labels, class order, or evaluation loaders.
"""

from __future__ import annotations

import torch


class TrialViewSelector:
    template_family = "sampler_or_data_view"

    def __init__(self, enabled: bool = False, mode: str = "baseline"):
        self.enabled = bool(enabled)
        self.mode = str(mode)

    def select_training_view(self, features: torch.Tensor, labels: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        """Return tensors with unchanged sample-label alignment."""
        if not self.enabled or self.mode == "baseline":
            return features, labels
        if features.size(0) != labels.size(0):
            raise ValueError("features and labels must keep the same sample count")
        # Replace this line with the trial-specific view choice. Do not alter labels.
        selected = features
        return selected, labels


def protected_split_note() -> str:
    return "Do not modify trainval_loc, test_seen_loc, test_unseen_loc, labels, or allclasses_names."
