"""Transferable Evidence-Calibrated PSE without sentence self-attention."""

from __future__ import annotations

import math
from collections.abc import Sequence

import torch
import torch.nn as nn
import torch.nn.functional as F


class TransferableEvidencePSE(nn.Module):
    """Add bounded, role-wise rival evidence to a frozen CLIP global score.

    Sentence embeddings are frozen.  For every class and evidence role, the
    strongest text-space rival is selected from the same role.  The resulting
    target-minus-rival vectors are weighted by semantic distinctiveness.  A
    single shared scalar controls their contribution for every seen and unseen
    class, so each role remains an exact additive term in the final logit.
    """

    def __init__(
        self,
        sentence_embeds: torch.Tensor,
        evidence_role_indices: Sequence[int],
        *,
        temperature: float,
        evidence_cap: float,
        evidence_init: float,
    ) -> None:
        super().__init__()
        if sentence_embeds.ndim != 3:
            raise ValueError("sentence_embeds must have shape [classes, roles, dim].")
        class_count, role_count, feature_dim = sentence_embeds.shape
        if class_count < 2 or role_count < 2 or feature_dim < 2:
            raise ValueError("sentence_embeds needs at least 2 classes, roles, and dims.")
        if not torch.isfinite(sentence_embeds).all():
            raise ValueError("sentence_embeds contains a non-finite value.")
        role_indices = tuple(int(index) for index in evidence_role_indices)
        if not role_indices or len(set(role_indices)) != len(role_indices):
            raise ValueError("evidence_role_indices must be non-empty and unique.")
        if min(role_indices) < 0 or max(role_indices) >= role_count:
            raise ValueError("evidence_role_indices contains an out-of-range role.")
        if float(temperature) <= 0.0:
            raise ValueError("temperature must be positive.")
        if not 0.0 < float(evidence_init) < float(evidence_cap) <= 1.0:
            raise ValueError("require 0 < evidence_init < evidence_cap <= 1.")

        normalized = F.normalize(sentence_embeds.detach().float(), dim=-1)
        role_index_tensor = torch.tensor(role_indices, dtype=torch.long)
        evidence_text = normalized.index_select(1, role_index_tensor)

        similarities = torch.einsum("crd,jrd->crj", evidence_text, evidence_text)
        class_ids = torch.arange(class_count)
        similarities[class_ids, :, class_ids] = -torch.inf
        rival_class_ids = similarities.argmax(dim=-1)
        role_ids = torch.arange(len(role_indices)).view(1, -1).expand(class_count, -1)
        rival_text = evidence_text[rival_class_ids, role_ids]
        rival_cosine = similarities.gather(2, rival_class_ids.unsqueeze(-1)).squeeze(-1)

        distinctiveness = ((1.0 - rival_cosine) / 2.0).clamp(0.0, 1.0)
        denominator = distinctiveness.sum(dim=1, keepdim=True)
        uniform = torch.full_like(distinctiveness, 1.0 / len(role_indices))
        role_weights = torch.where(
            denominator > 1e-12,
            distinctiveness / denominator.clamp_min(1e-12),
            uniform,
        )
        role_evidence_vectors = (
            0.5 * role_weights.unsqueeze(-1) * (evidence_text - rival_text)
        )
        evidence_vectors = role_evidence_vectors.sum(dim=1)
        evidence_coherence = evidence_vectors.norm(dim=-1)
        base_prototypes = F.normalize(normalized.mean(dim=1), dim=-1)

        self.register_buffer("sentence_embeds", normalized, persistent=True)
        self.register_buffer("base_prototypes", base_prototypes, persistent=True)
        self.register_buffer("evidence_role_indices", role_index_tensor, persistent=True)
        self.register_buffer("rival_class_ids", rival_class_ids, persistent=True)
        self.register_buffer("rival_cosine", rival_cosine, persistent=True)
        self.register_buffer("role_weights", role_weights, persistent=True)
        self.register_buffer(
            "role_evidence_vectors", role_evidence_vectors, persistent=True
        )
        self.register_buffer("evidence_vectors", evidence_vectors, persistent=True)
        self.register_buffer(
            "evidence_coherence", evidence_coherence, persistent=True
        )

        initial_ratio = float(evidence_init) / float(evidence_cap)
        initial_logit = math.log(initial_ratio / (1.0 - initial_ratio))
        self.evidence_logit = nn.Parameter(torch.tensor(initial_logit))
        self.temperature = float(temperature)
        self.evidence_cap = float(evidence_cap)

    @property
    def evidence_strength(self) -> torch.Tensor:
        """One positive scalar shared by every class and every role."""

        return self.evidence_cap * torch.sigmoid(self.evidence_logit)

    def _selected(self, tensor: torch.Tensor, class_ids: torch.Tensor | None):
        if class_ids is None:
            return tensor
        class_ids = class_ids.to(device=tensor.device, dtype=torch.long)
        if class_ids.ndim != 1:
            raise ValueError("class_ids must be one-dimensional.")
        if class_ids.numel() and (
            int(class_ids.min()) < 0 or int(class_ids.max()) >= tensor.shape[0]
        ):
            raise ValueError("class_ids contains an out-of-range class.")
        return tensor.index_select(0, class_ids)

    def score_components(
        self, image_features: torch.Tensor, class_ids: torch.Tensor | None = None
    ) -> dict[str, torch.Tensor]:
        """Return base, per-role, and final logits with exact additivity."""

        if image_features.ndim != 2 or image_features.shape[1] != self.base_prototypes.shape[1]:
            raise ValueError("image_features must have shape [batch, text_dim].")
        if not torch.isfinite(image_features).all():
            raise ValueError("image_features contains a non-finite value.")
        images = F.normalize(image_features.float(), dim=-1)
        base = self._selected(self.base_prototypes, class_ids)
        role_vectors = self._selected(self.role_evidence_vectors, class_ids)
        base_logits = images @ base.T / self.temperature
        role_contributions = (
            self.evidence_strength
            * torch.einsum("bd,crd->bcr", images, role_vectors)
            / self.temperature
        )
        final_logits = base_logits + role_contributions.sum(dim=-1)
        return {
            "base_logits": base_logits,
            "role_contributions": role_contributions,
            "final_logits": final_logits,
        }

    def logits(
        self, image_features: torch.Tensor, class_ids: torch.Tensor | None = None
    ) -> torch.Tensor:
        return self.score_components(image_features, class_ids)["final_logits"]

    def explanation(
        self, image_features: torch.Tensor, class_ids: torch.Tensor | None = None
    ) -> dict[str, torch.Tensor]:
        """Return the exact score terms and their frozen semantic identities."""

        components = self.score_components(image_features, class_ids)
        return {
            **components,
            "role_weights": self._selected(self.role_weights, class_ids),
            "rival_class_ids": self._selected(self.rival_class_ids, class_ids),
            "rival_cosine": self._selected(self.rival_cosine, class_ids),
            "evidence_coherence": self._selected(
                self.evidence_coherence, class_ids
            ),
            "evidence_strength": self.evidence_strength,
        }

    def effective_class_vectors(self) -> torch.Tensor:
        """Equivalent unnormalized vectors used by the additive score."""

        return self.base_prototypes + self.evidence_strength * self.evidence_vectors
