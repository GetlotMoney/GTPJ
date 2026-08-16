"""VCER: visibility-aware counterfactual evidence routing on frozen X2."""

from __future__ import annotations

import math
from collections.abc import Sequence

import torch
import torch.nn as nn
import torch.nn.functional as F


class VisibilityAwareCounterfactualEvidenceRouter(nn.Module):
    """Rerank frozen X2 scores with rival-relative local patch evidence.

    The frozen inputs follow the CUB ``6 local + 1 global + 1 unique`` text
    contract.  VCER has one shared low-rank projector and no class-specific,
    seen-specific, or unseen-specific parameter.  The X2-off path never reads
    patch features and returns the frozen cosine logits directly.
    """

    def __init__(
        self,
        sentence_embeds: torch.Tensor,
        x2_prototypes: torch.Tensor,
        x2_scale: float | torch.Tensor,
        *,
        local_role_indices: Sequence[int] = (0, 1, 2, 3, 4, 5),
        global_role_index: int = 6,
        unique_role_index: int = 7,
        rank: int = 16,
    ) -> None:
        super().__init__()
        sentences = torch.as_tensor(sentence_embeds).detach().float()
        prototype_input = torch.as_tensor(x2_prototypes).detach()
        if prototype_input.dtype != torch.float32:
            raise ValueError("x2_prototypes must be the final float32 X2 prototypes.")
        prototypes = prototype_input.clone()
        if sentences.ndim != 3:
            raise ValueError("sentence_embeds must have shape [classes, 8, dim].")
        class_count, role_count, feature_dim = sentences.shape
        if role_count != 8 or class_count < 2 or feature_dim < 2:
            raise ValueError("VCER requires [classes>=2, 8, dim>=2] sentence embeddings.")
        if tuple(prototypes.shape) != (class_count, feature_dim):
            raise ValueError("x2_prototypes must have shape [classes, dim].")
        if not torch.isfinite(sentences).all() or not torch.isfinite(prototypes).all():
            raise ValueError("frozen VCER inputs contain a non-finite value.")
        prototype_norms = prototypes.norm(dim=-1)
        if not torch.allclose(
            prototype_norms,
            torch.ones_like(prototype_norms),
            atol=1e-4,
            rtol=1e-4,
        ):
            raise ValueError("x2_prototypes must already be unit-normalized.")

        local_roles = tuple(int(index) for index in local_role_indices)
        global_role = int(global_role_index)
        unique_role = int(unique_role_index)
        if len(local_roles) != 6 or len(set(local_roles)) != 6:
            raise ValueError("local_role_indices must contain six unique roles.")
        all_roles = (*local_roles, global_role, unique_role)
        if set(all_roles) != set(range(8)) or len(set(all_roles)) != 8:
            raise ValueError("the 6 local, global, and unique roles must partition 0..7.")
        if not 1 <= int(rank) <= feature_dim:
            raise ValueError("rank must be in [1, feature_dim].")
        scale = float(torch.as_tensor(x2_scale).detach().cpu())
        if not torch.isfinite(torch.tensor(scale)) or scale <= 0.0:
            raise ValueError("x2_scale must be finite and positive.")

        self.register_buffer(
            "sentence_embeds", F.normalize(sentences, dim=-1), persistent=True
        )
        self.register_buffer("x2_prototypes", prototypes, persistent=True)
        self.register_buffer("x2_scale", torch.tensor(scale), persistent=True)
        self.register_buffer(
            "local_role_indices",
            torch.tensor(local_roles, dtype=torch.long),
            persistent=True,
        )
        self.global_role_index = global_role
        self.unique_role_index = unique_role

        self.down = nn.Linear(feature_dim, int(rank), bias=False)
        self.up = nn.Linear(int(rank), feature_dim, bias=False)
        nn.init.zeros_(self.up.weight)

    @property
    def class_count(self) -> int:
        return int(self.sentence_embeds.shape[0])

    @property
    def feature_dim(self) -> int:
        return int(self.sentence_embeds.shape[-1])

    def _project(self, values: torch.Tensor) -> torch.Tensor:
        residual = self.up(F.gelu(self.down(values)))
        return F.normalize(values + residual, dim=-1)

    def _candidate_classes(self, class_ids: torch.Tensor | None) -> torch.Tensor:
        if class_ids is None:
            return torch.arange(self.class_count, device=self.x2_prototypes.device)
        classes = torch.as_tensor(
            class_ids, device=self.x2_prototypes.device, dtype=torch.long
        )
        if classes.ndim != 1 or classes.numel() < 2:
            raise ValueError("class_ids must contain at least two classes.")
        if classes.unique().numel() != classes.numel():
            raise ValueError("class_ids must be unique.")
        if int(classes.min()) < 0 or int(classes.max()) >= self.class_count:
            raise ValueError("class_ids contains an out-of-range class.")
        return classes

    def _normalized_images(self, image_features: torch.Tensor) -> torch.Tensor:
        if (
            image_features.ndim != 2
            or image_features.shape[-1] != self.feature_dim
        ):
            raise ValueError("image_features must have shape [batch, dim].")
        if not torch.isfinite(image_features).all():
            raise ValueError("image_features contains a non-finite value.")
        return F.normalize(image_features.detach().float(), dim=-1)

    def _normalized_patches(
        self, patch_features: torch.Tensor, batch_size: int
    ) -> torch.Tensor:
        if (
            patch_features.ndim != 3
            or patch_features.shape[0] != batch_size
            or patch_features.shape[-1] != self.feature_dim
            or patch_features.shape[1] < 1
        ):
            raise ValueError("patch_features must have shape [batch, patches>=1, dim].")
        if not torch.isfinite(patch_features).all():
            raise ValueError("patch_features contains a non-finite value.")
        return F.normalize(patch_features.detach().float(), dim=-1)

    def _role_evidence_order(
        self,
        role_evidence_permutation: torch.Tensor | None,
        *,
        device: torch.device,
    ) -> torch.Tensor:
        role_count = int(self.local_role_indices.numel())
        if role_evidence_permutation is None:
            return torch.arange(role_count, device=device)
        order = torch.as_tensor(
            role_evidence_permutation, device=device, dtype=torch.long
        )
        if tuple(order.shape) != (role_count,):
            raise ValueError(
                "role_evidence_permutation must have one entry per local role."
            )
        if not torch.equal(
            order.sort().values, torch.arange(role_count, device=device)
        ):
            raise ValueError("role_evidence_permutation must permute 0..5.")
        return order

    def base_logits(
        self, image_features: torch.Tensor, class_ids: torch.Tensor | None = None
    ) -> torch.Tensor:
        """Return the exact frozen-X2 cosine classifier path."""

        images = self._normalized_images(image_features)
        classes = self._candidate_classes(class_ids)
        prototypes = self.x2_prototypes.index_select(0, classes)
        return images @ prototypes.T * self.x2_scale

    @staticmethod
    def _rival_positions(base_cosine: torch.Tensor) -> torch.Tensor:
        if base_cosine.shape[1] < 2:
            raise ValueError("rival selection requires at least two candidates.")
        top_two = base_cosine.topk(k=2, dim=1).indices
        candidate_positions = torch.arange(
            base_cosine.shape[1], device=base_cosine.device
        ).view(1, -1)
        top_one = top_two[:, :1]
        return torch.where(
            candidate_positions == top_one,
            top_two[:, 1:2],
            top_one,
        ).expand_as(base_cosine)

    def score_components(
        self,
        image_features: torch.Tensor,
        patch_features: torch.Tensor,
        class_ids: torch.Tensor | None = None,
        *,
        unique_swap_with_rival: bool = False,
        local_source_ids: torch.Tensor | None = None,
        role_evidence_permutation: torch.Tensor | None = None,
    ) -> dict[str, torch.Tensor]:
        """Return the complete frozen base and VCER additive evidence terms."""

        images = self._normalized_images(image_features)
        patches = self._normalized_patches(patch_features, images.shape[0])
        classes = self._candidate_classes(class_ids)
        candidate_count = classes.numel()

        prototypes = self.x2_prototypes.index_select(0, classes)
        base_cosine = images @ prototypes.T
        rival_positions = self._rival_positions(base_cosine.detach())
        rival_class_ids = classes[rival_positions]

        projected_sentences = self._project(self.sentence_embeds)
        candidate_sentences = projected_sentences.index_select(0, classes)
        original_local = candidate_sentences.index_select(1, self.local_role_indices)
        candidate_local = original_local
        if local_source_ids is not None:
            sources = torch.as_tensor(
                local_source_ids,
                device=classes.device,
                dtype=torch.long,
            )
            if tuple(sources.shape) != (candidate_count,):
                raise ValueError("local_source_ids must align with class_ids.")
            if int(sources.min()) < 0 or int(sources.max()) >= self.class_count:
                raise ValueError("local_source_ids contains an out-of-range class.")
            candidate_local = projected_sentences.index_select(0, sources).index_select(
                1, self.local_role_indices
            )
        rival_local = original_local[rival_positions]

        candidate_unique = candidate_sentences[:, self.unique_role_index]
        rival_unique = candidate_unique[rival_positions]
        routed_unique = (
            rival_unique if unique_swap_with_rival else candidate_unique.unsqueeze(0)
        )
        local_direction = F.normalize(
            candidate_local.unsqueeze(0) - rival_local, dim=-1
        )
        unique_direction = F.normalize(routed_unique - rival_unique, dim=-1)
        semantic_distinctiveness = 0.5 * (
            1.0
            - (candidate_local.unsqueeze(0) * rival_local).sum(dim=-1)
        ).clamp(0.0, 2.0)
        unique_alignment = (
            local_direction * unique_direction.unsqueeze(2)
        ).sum(dim=-1).clamp(-1.0, 1.0)
        unique_agreement = 0.5 * (1.0 + unique_alignment)
        raw_role_weights = semantic_distinctiveness * (1.0 + unique_agreement)
        denominator = raw_role_weights.sum(dim=-1, keepdim=True)
        uniform = torch.full_like(raw_role_weights, 1.0 / len(self.local_role_indices))
        role_weights = torch.where(
            denominator > 1e-12,
            raw_role_weights / denominator.clamp_min(1e-12),
            uniform,
        )

        projected_patches = self._project(patches)
        candidate_similarity = torch.einsum(
            "bpd,crd->bcpr", projected_patches, candidate_local
        )
        rival_similarity = torch.einsum(
            "bpd,bcrd->bcpr", projected_patches, rival_local
        )
        patch_margins = 0.5 * (candidate_similarity - rival_similarity)

        candidate_global = candidate_sentences[:, self.global_role_index]
        rival_global = candidate_global[rival_positions]
        candidate_foreground = torch.einsum(
            "bpd,cd->bcp", projected_patches, candidate_global
        )
        rival_foreground = torch.einsum(
            "bpd,bcd->bcp", projected_patches, rival_global
        )
        foreground = (
            0.5 + 0.25 * (candidate_foreground + rival_foreground)
        ).clamp(0.0, 1.0)
        evidence_strength = foreground.unsqueeze(-1) * patch_margins.abs()
        patch_weights = F.softmax(
            evidence_strength * self.x2_scale.detach(), dim=2
        )
        visibility = evidence_strength.amax(dim=2)
        role_evidence = visibility * (patch_weights * patch_margins).sum(dim=2)
        evidence_order = self._role_evidence_order(
            role_evidence_permutation, device=role_evidence.device
        )
        aligned_role_evidence = role_evidence.index_select(-1, evidence_order)
        evidence_correction = (role_weights * aligned_role_evidence).sum(dim=-1)

        final_cosine = 0.5 * (base_cosine + evidence_correction)
        return {
            "base_cosine": base_cosine,
            "base_logits": base_cosine * self.x2_scale,
            "rival_candidate_positions": rival_positions,
            "rival_class_ids": rival_class_ids,
            "semantic_distinctiveness": semantic_distinctiveness,
            "unique_agreement": unique_agreement,
            "role_weights": role_weights,
            "patch_margins": patch_margins,
            "foreground": foreground,
            "evidence_strength": evidence_strength,
            "patch_weights": patch_weights,
            "visibility": visibility,
            "role_evidence": role_evidence,
            "role_evidence_permutation": evidence_order,
            "aligned_role_evidence": aligned_role_evidence,
            "evidence_correction": evidence_correction,
            "final_cosine": final_cosine,
            "final_logits": final_cosine * self.x2_scale,
        }

    def logits(
        self,
        image_features: torch.Tensor,
        class_ids: torch.Tensor | None = None,
        *,
        patch_features: torch.Tensor | None = None,
        evidence_enabled: bool = True,
        unique_swap_with_rival: bool = False,
        local_source_ids: torch.Tensor | None = None,
        role_evidence_permutation: torch.Tensor | None = None,
    ) -> torch.Tensor:
        if not evidence_enabled:
            return self.base_logits(image_features, class_ids)
        if patch_features is None:
            raise ValueError("enabled VCER requires patch_features.")
        return self.score_components(
            image_features,
            patch_features,
            class_ids,
            unique_swap_with_rival=unique_swap_with_rival,
            local_source_ids=local_source_ids,
            role_evidence_permutation=role_evidence_permutation,
        )["final_logits"]

    def preservation_loss(self) -> torch.Tensor:
        projected = self._project(self.sentence_embeds)
        cosine_distance = 1.0 - (projected * self.sentence_embeds).sum(dim=-1)
        return cosine_distance.clamp_min(0.0).mean()

    def training_loss(
        self,
        image_features: torch.Tensor,
        patch_features: torch.Tensor | None,
        labels: torch.Tensor,
        class_ids: torch.Tensor,
        *,
        evidence_enabled: bool = True,
        unique_margin: float = 0.1,
        unique_causal_weight: float = 1.0,
        preserve_weight: float = 0.05,
    ) -> dict[str, torch.Tensor]:
        """Seen-image loss; text for every class remains frozen and transferable."""

        loss_values = (
            float(unique_margin),
            float(unique_causal_weight),
            float(preserve_weight),
        )
        if not all(math.isfinite(value) and value >= 0.0 for value in loss_values):
            raise ValueError("loss margin and weights must be finite and non-negative.")
        classes = self._candidate_classes(class_ids)
        labels = torch.as_tensor(labels, device=classes.device, dtype=torch.long)
        if labels.ndim != 1 or labels.numel() != image_features.shape[0]:
            raise ValueError("labels must have shape [batch].")
        if labels.numel() and (
            int(labels.min()) < 0 or int(labels.max()) >= self.class_count
        ):
            raise ValueError("labels contains an out-of-range class.")
        global_to_local = torch.full(
            (self.class_count,), -1, device=classes.device, dtype=torch.long
        )
        global_to_local[classes] = torch.arange(classes.numel(), device=classes.device)
        targets = global_to_local[labels]
        if (targets < 0).any():
            raise ValueError("training labels must stay inside class_ids.")

        if not evidence_enabled:
            classification = F.cross_entropy(
                self.base_logits(image_features, classes), targets
            )
            zero = classification.new_zeros(())
            return {
                "loss": classification,
                "classification_loss": classification,
                "unique_causal_loss": zero,
                "preservation_loss": zero,
            }
        if patch_features is None:
            raise ValueError("enabled VCER training requires patch_features.")

        correct = self.score_components(image_features, patch_features, classes)
        classification = F.cross_entropy(correct["final_logits"], targets)
        if float(unique_causal_weight) > 0.0:
            swapped = self.score_components(
                image_features,
                patch_features,
                classes,
                unique_swap_with_rival=True,
            )
            rows = torch.arange(labels.numel(), device=classes.device)
            correct_true = correct["evidence_correction"][rows, targets]
            swapped_true = swapped["evidence_correction"][rows, targets]
            unique_causal = F.relu(
                float(unique_margin) - correct_true + swapped_true
            ).mean()
        else:
            unique_causal = classification.new_zeros(())
        preservation = (
            self.preservation_loss()
            if float(preserve_weight) > 0.0
            else classification.new_zeros(())
        )
        total = (
            classification
            + float(unique_causal_weight) * unique_causal
            + float(preserve_weight) * preservation
        )
        return {
            "loss": total,
            "classification_loss": classification,
            "unique_causal_loss": unique_causal,
            "preservation_loss": preservation,
        }
