"""ARTV: anatomy-anchored role transport verification on frozen X2."""

from __future__ import annotations

from collections.abc import Sequence

import torch
import torch.nn as nn
import torch.nn.functional as F


class AnatomyAnchoredRoleTransportVerifier(nn.Module):
    """Use crop CLS features to verify only the frozen-X2 top-two pair.

    Six class-independent anatomy anchors form fixed visual slots.  Six local
    class descriptions score only their matching slots, the global description
    supplies pair-symmetric foreground mass, and the unique description casts
    one additional vote.  ARTV swaps the top-two X2 logits only when at least
    five of seven votes support the runner-up; otherwise it returns X2 exactly.
    """

    def __init__(
        self,
        sentence_embeds: torch.Tensor,
        x2_prototypes: torch.Tensor,
        x2_scale: float | torch.Tensor,
        role_anchors: torch.Tensor,
        *,
        local_role_indices: Sequence[int] = (0, 1, 2, 3, 4, 5),
        global_role_index: int = 6,
        unique_role_index: int = 7,
        sinkhorn_iterations: int = 12,
        transport_epsilon: float = 0.05,
        certificate_votes: int = 5,
    ) -> None:
        super().__init__()
        sentences = torch.as_tensor(sentence_embeds).detach().float()
        prototype_input = torch.as_tensor(x2_prototypes).detach()
        anchors = torch.as_tensor(role_anchors).detach().float()
        if sentences.ndim != 3 or sentences.shape[1] != 8:
            raise ValueError("sentence_embeds must have shape [classes, 8, dim].")
        class_count, _, feature_dim = sentences.shape
        if prototype_input.dtype != torch.float32:
            raise ValueError("x2_prototypes must be final float32 prototypes.")
        if tuple(prototype_input.shape) != (class_count, feature_dim):
            raise ValueError("x2_prototypes must have shape [classes, dim].")
        if tuple(anchors.shape) != (6, feature_dim):
            raise ValueError("role_anchors must have shape [6, dim].")
        if not all(torch.isfinite(value).all() for value in (sentences, prototype_input, anchors)):
            raise ValueError("ARTV frozen inputs contain a non-finite value.")
        prototype_norms = prototype_input.norm(dim=-1)
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
        if set((*local_roles, global_role, unique_role)) != set(range(8)):
            raise ValueError("the six local, global, and unique roles must partition 0..7.")
        if int(sinkhorn_iterations) < 1:
            raise ValueError("sinkhorn_iterations must be positive.")
        if not torch.isfinite(torch.tensor(float(transport_epsilon))) or float(transport_epsilon) <= 0.0:
            raise ValueError("transport_epsilon must be finite and positive.")
        if int(certificate_votes) != 5:
            raise ValueError("ARTV freezes a five-of-seven certificate.")
        scale = float(torch.as_tensor(x2_scale).detach().cpu())
        if not torch.isfinite(torch.tensor(scale)) or scale <= 0.0:
            raise ValueError("x2_scale must be finite and positive.")

        normalized_sentences = F.normalize(sentences, dim=-1)
        local = normalized_sentences[:, local_roles]
        centered_local = self._center_class_text(local)
        unique = normalized_sentences[:, unique_role]
        centered_unique = self._center_class_text(unique)
        self.register_buffer("sentence_embeds", normalized_sentences, persistent=True)
        self.register_buffer("centered_local_text", centered_local, persistent=True)
        self.register_buffer("centered_unique_text", centered_unique, persistent=True)
        self.register_buffer("x2_prototypes", prototype_input.clone(), persistent=True)
        self.register_buffer("x2_scale", torch.tensor(scale), persistent=True)
        self.register_buffer("role_anchors", F.normalize(anchors, dim=-1), persistent=True)
        self.register_buffer(
            "local_role_indices", torch.tensor(local_roles, dtype=torch.long), persistent=True
        )
        self.global_role_index = global_role
        self.unique_role_index = unique_role
        self.sinkhorn_iterations = int(sinkhorn_iterations)
        self.transport_epsilon = float(transport_epsilon)
        self.certificate_votes = int(certificate_votes)

    @staticmethod
    def _center_class_text(values: torch.Tensor) -> torch.Tensor:
        centered = values - values.mean(dim=0, keepdim=True)
        return F.normalize(centered, dim=-1, eps=1e-12)

    @property
    def class_count(self) -> int:
        return int(self.sentence_embeds.shape[0])

    @property
    def feature_dim(self) -> int:
        return int(self.sentence_embeds.shape[-1])

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
        if image_features.ndim != 2 or image_features.shape[-1] != self.feature_dim:
            raise ValueError("image_features must have shape [batch, dim].")
        if not torch.isfinite(image_features).all():
            raise ValueError("image_features contains a non-finite value.")
        return F.normalize(image_features.detach().float(), dim=-1)

    def _normalized_crops(
        self, crop_features: torch.Tensor, batch_size: int
    ) -> torch.Tensor:
        if (
            crop_features.ndim != 3
            or crop_features.shape[0] != batch_size
            or crop_features.shape[1] != 15
            or crop_features.shape[-1] != self.feature_dim
        ):
            raise ValueError("crop_features must have shape [batch, 15, dim].")
        if not torch.isfinite(crop_features).all():
            raise ValueError("crop_features contains a non-finite value.")
        return F.normalize(crop_features.detach().float(), dim=-1)

    def base_logits(
        self, image_features: torch.Tensor, class_ids: torch.Tensor | None = None
    ) -> torch.Tensor:
        images = self._normalized_images(image_features)
        classes = self._candidate_classes(class_ids)
        prototypes = self.x2_prototypes.index_select(0, classes)
        return images @ prototypes.T * self.x2_scale

    def _role_slots(
        self, crops: torch.Tensor, pair_global: torch.Tensor
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """Balanced entropic transport with one explicit background column."""

        batch_size, crop_count, _ = crops.shape
        foreground_logits = torch.einsum("bpd,bd->bp", crops, pair_global)
        row_mass = F.softmax(foreground_logits / self.transport_epsilon, dim=1)
        anatomy = torch.einsum("bpd,rd->bpr", crops, self.role_anchors)
        background = anatomy.mean(dim=-1, keepdim=True)
        scores = torch.cat((anatomy, background), dim=-1)
        scores = scores - scores.amax(dim=(1, 2), keepdim=True)
        kernel = torch.exp(scores / self.transport_epsilon).clamp_min(1e-12)
        column_mass = torch.full(
            (batch_size, 7),
            1.0 / 7.0,
            device=crops.device,
            dtype=crops.dtype,
        )
        left = torch.ones_like(row_mass)
        right = torch.ones_like(column_mass)
        for _ in range(self.sinkhorn_iterations):
            left = row_mass / torch.einsum("bpr,br->bp", kernel, right).clamp_min(1e-12)
            right = column_mass / torch.einsum("bpr,bp->br", kernel, left).clamp_min(1e-12)
        plan = left.unsqueeze(-1) * kernel * right.unsqueeze(1)
        role_plan = plan[:, :, :6]
        role_mass = role_plan.sum(dim=1)
        slots = torch.einsum("bpr,bpd->brd", role_plan, crops)
        slots = slots / role_mass.unsqueeze(-1).clamp_min(1e-12)
        return F.normalize(slots, dim=-1, eps=1e-12), role_mass

    @staticmethod
    def _standardize_over_classes(scores: torch.Tensor) -> torch.Tensor:
        mean = scores.mean(dim=1, keepdim=True)
        std = scores.std(dim=1, keepdim=True, unbiased=False).clamp_min(1e-6)
        return (scores - mean) / std

    @staticmethod
    def _top_two_by_score_then_class_id(
        scores: torch.Tensor, canonical_classes: torch.Tensor
    ) -> torch.Tensor:
        """Choose score-descending/class-id-ascending without topk tie ambiguity."""

        excluded = torch.zeros_like(scores, dtype=torch.bool)
        class_grid = canonical_classes.unsqueeze(0).expand(scores.shape[0], -1)
        sentinel = torch.iinfo(torch.long).max
        winners = []
        for _ in range(2):
            eligible = scores.masked_fill(excluded, float("-inf"))
            best_score = eligible.amax(dim=1, keepdim=True)
            tied = eligible.eq(best_score)
            best_class = class_grid.masked_fill(~tied, sentinel).amin(dim=1)
            position = canonical_classes.unsqueeze(0).eq(best_class.unsqueeze(1)).long().argmax(dim=1)
            winners.append(position)
            excluded.scatter_(1, position.unsqueeze(1), True)
        return torch.stack(winners, dim=1)

    def score_components(
        self,
        image_features: torch.Tensor,
        crop_features: torch.Tensor,
        class_ids: torch.Tensor | None = None,
        *,
        role_description_permutation: torch.Tensor | None = None,
        unique_swap_with_runner_up: bool = False,
    ) -> dict[str, torch.Tensor]:
        images = self._normalized_images(image_features)
        crops = self._normalized_crops(crop_features, images.shape[0])
        classes = self._candidate_classes(class_ids)
        prototypes = self.x2_prototypes.index_select(0, classes)
        base_logits = images @ prototypes.T * self.x2_scale
        canonical_order = torch.argsort(classes)
        inverse_canonical_order = torch.argsort(canonical_order)
        canonical_classes = classes.index_select(0, canonical_order)
        canonical_base_logits = base_logits.index_select(1, canonical_order)
        canonical_top_two = self._top_two_by_score_then_class_id(
            canonical_base_logits, canonical_classes
        )
        canonical_top_one = canonical_top_two[:, 0]
        canonical_runner_up = canonical_top_two[:, 1]
        top_one_positions = canonical_order[canonical_top_one]
        runner_up_positions = canonical_order[canonical_runner_up]
        top_one_classes = canonical_classes[canonical_top_one]
        runner_up_classes = canonical_classes[canonical_runner_up]

        global_text = self.sentence_embeds[:, self.global_role_index]
        pair_global = F.normalize(
            global_text[top_one_classes] + global_text[runner_up_classes],
            dim=-1,
            eps=1e-12,
        )
        role_slots, role_mass = self._role_slots(crops, pair_global)

        local_text = self.centered_local_text.index_select(0, canonical_classes)
        if role_description_permutation is not None:
            permutation = torch.as_tensor(
                role_description_permutation,
                device=classes.device,
                dtype=torch.long,
            )
            if tuple(permutation.shape) != (6,) or not torch.equal(
                permutation.sort().values, torch.arange(6, device=classes.device)
            ):
                raise ValueError("role_description_permutation must permute 0..5.")
            local_text = local_text.index_select(1, permutation)
        local_scores = torch.einsum("brd,crd->bcr", role_slots, local_text)
        local_z = self._standardize_over_classes(local_scores)

        unique_text = self.centered_unique_text.index_select(0, canonical_classes)
        unique_scores = torch.einsum("brd,cd->bcr", role_slots, unique_text).amax(dim=-1)
        unique_z = self._standardize_over_classes(unique_scores)
        rows = torch.arange(images.shape[0], device=images.device)
        local_evidence = (
            local_z[rows, canonical_runner_up] - local_z[rows, canonical_top_one]
        )
        unique_evidence = (
            unique_z[rows, canonical_runner_up] - unique_z[rows, canonical_top_one]
        )
        if unique_swap_with_runner_up:
            unique_evidence = -unique_evidence
        all_evidence = torch.cat((local_evidence, unique_evidence.unsqueeze(-1)), dim=-1)
        runner_up_votes = (all_evidence > 0.0).sum(dim=-1)
        certificate = runner_up_votes >= self.certificate_votes

        final_logits = base_logits.clone()
        certified_rows = rows[certificate]
        first = top_one_positions[certificate]
        second = runner_up_positions[certificate]
        if certified_rows.numel() > 0:
            first_values = final_logits[certified_rows, first].clone()
            final_logits[certified_rows, first] = final_logits[certified_rows, second]
            final_logits[certified_rows, second] = first_values
        return {
            "base_logits": base_logits,
            "top_one_positions": top_one_positions,
            "runner_up_positions": runner_up_positions,
            "top_one_classes": top_one_classes,
            "runner_up_classes": runner_up_classes,
            "role_slots": role_slots,
            "role_mass": role_mass,
            "local_scores": local_scores.index_select(1, inverse_canonical_order),
            "local_z": local_z.index_select(1, inverse_canonical_order),
            "unique_scores": unique_scores.index_select(1, inverse_canonical_order),
            "unique_z": unique_z.index_select(1, inverse_canonical_order),
            "local_evidence": local_evidence,
            "unique_evidence": unique_evidence,
            "all_evidence": all_evidence,
            "runner_up_votes": runner_up_votes,
            "certificate": certificate,
            "final_logits": final_logits,
        }

    def logits(
        self,
        image_features: torch.Tensor,
        class_ids: torch.Tensor | None = None,
        *,
        crop_features: torch.Tensor | None = None,
        artv_enabled: bool = True,
        role_description_permutation: torch.Tensor | None = None,
        unique_swap_with_runner_up: bool = False,
    ) -> torch.Tensor:
        if not artv_enabled:
            return self.base_logits(image_features, class_ids)
        if crop_features is None:
            raise ValueError("enabled ARTV requires crop_features.")
        return self.score_components(
            image_features,
            crop_features,
            class_ids,
            role_description_permutation=role_description_permutation,
            unique_swap_with_runner_up=unique_swap_with_runner_up,
        )["final_logits"]
