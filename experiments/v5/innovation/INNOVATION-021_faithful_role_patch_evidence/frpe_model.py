"""FRPE：冻结 CLIP patch 的忠实角色局部证据。"""

from __future__ import annotations

import torch
import torch.nn.functional as F


CLASS_COUNT = 200
ROLE_COUNT = 8
PATCH_COUNT = 576


def normalized_sentences(sentence_embeds: torch.Tensor) -> torch.Tensor:
    tensor = torch.as_tensor(sentence_embeds).float()
    if tensor.shape != (CLASS_COUNT, ROLE_COUNT, 768):
        raise ValueError(f"sentences must be [200, 8, 768], got {tuple(tensor.shape)}")
    if not torch.isfinite(tensor).all():
        raise ValueError("sentences contain non-finite values")
    return F.normalize(tensor, dim=-1)


class FRPE:
    """无训练参数；每个角色局部项是最终 raw score 的真实加数。"""

    MODES = ("all", "drop_high_norm", "drop_random", "topk_only")

    def __init__(
        self,
        sentence_embeds: torch.Tensor,
        *,
        top_k: int = 8,
        temperature: float = 0.05,
    ):
        if not 1 <= top_k < PATCH_COUNT:
            raise ValueError("top_k must be in [1, 575]")
        if temperature <= 0:
            raise ValueError("temperature must be positive")
        self.sentences = normalized_sentences(sentence_embeds)
        self.base_prototypes = F.normalize(self.sentences.mean(dim=1), dim=-1)
        self.top_k = int(top_k)
        self.temperature = float(temperature)

    def to(self, device: torch.device | str) -> "FRPE":
        self.sentences = self.sentences.to(device)
        self.base_prototypes = self.base_prototypes.to(device)
        return self

    def _candidates(self, candidate_classes: torch.Tensor) -> torch.Tensor:
        candidates = torch.as_tensor(candidate_classes, device=self.sentences.device).long()
        if candidates.ndim != 1 or candidates.numel() == 0:
            raise ValueError("candidate classes must be a non-empty vector")
        if candidates.unique().numel() != candidates.numel():
            raise ValueError("candidate classes contain duplicates")
        if int(candidates.min()) < 0 or int(candidates.max()) >= CLASS_COUNT:
            raise ValueError("candidate class is outside [0, 199]")
        return candidates

    @staticmethod
    def _masked_role_evidence(
        similarities: torch.Tensor,
        removed_indices: torch.Tensor,
        top_k: int,
    ) -> torch.Tensor:
        batch, patches, classes, roles = similarities.shape
        removed = torch.as_tensor(removed_indices, device=similarities.device).long()
        if removed.shape != (batch,) or int(removed.min()) < 0 or int(removed.max()) >= patches:
            raise ValueError("removed patch indices are invalid")
        gather_index = removed.view(batch, 1, 1, 1).expand(batch, 1, classes, roles)
        removed_values = similarities.gather(1, gather_index).squeeze(1)
        masked = similarities.clone()
        masked.scatter_(1, gather_index, -torch.inf)
        top_values = masked.topk(top_k, dim=1).values.mean(dim=1)
        remaining_mean = (similarities.sum(dim=1) - removed_values) / (patches - 1)
        return top_values - remaining_mean

    def score_components(
        self,
        cls_features: torch.Tensor,
        patch_features: torch.Tensor,
        candidate_classes: torch.Tensor,
        *,
        random_drop_indices: torch.Tensor,
    ) -> dict[str, torch.Tensor]:
        candidates = self._candidates(candidate_classes)
        cls_value = F.normalize(
            torch.as_tensor(cls_features, device=self.sentences.device).float(), dim=-1
        )
        raw_patches = torch.as_tensor(patch_features, device=self.sentences.device).float()
        if cls_value.ndim != 2 or cls_value.shape[1] != 768:
            raise ValueError("CLS features must be [N, 768]")
        if raw_patches.shape != (cls_value.shape[0], PATCH_COUNT, 768):
            raise ValueError("patch features must be [N, 576, 768]")
        patch_value = F.normalize(raw_patches, dim=-1)
        similarities = torch.einsum(
            "bpd,crd->bpcr", patch_value, self.sentences[candidates]
        )
        spatial_mean = similarities.mean(dim=1)
        top_values = similarities.topk(self.top_k, dim=1).values.mean(dim=1)
        all_roles = top_values - spatial_mean
        high_norm_indices = raw_patches.norm(dim=-1).argmax(dim=1)
        drop_high_roles = self._masked_role_evidence(
            similarities, high_norm_indices, self.top_k
        )
        drop_random_roles = self._masked_role_evidence(
            similarities, random_drop_indices, self.top_k
        )
        base_scores = cls_value @ self.base_prototypes[candidates].T
        return {
            "base_scores": base_scores,
            "all": all_roles,
            "drop_high_norm": drop_high_roles,
            "drop_random": drop_random_roles,
            "topk_only": top_values,
            "high_norm_indices": high_norm_indices,
        }

    def combine(
        self,
        base_scores: torch.Tensor,
        role_evidence: torch.Tensor,
        *,
        strength: float,
    ) -> dict[str, torch.Tensor]:
        if strength < 0:
            raise ValueError("strength must be non-negative")
        if role_evidence.ndim != 3 or role_evidence.shape[-1] != ROLE_COUNT:
            raise ValueError("role evidence must be [N, C, 8]")
        contributions = float(strength) * role_evidence / ROLE_COUNT
        raw_scores = base_scores + contributions.sum(dim=-1)
        return {
            "contributions": contributions,
            "raw_scores": raw_scores,
            "logits": raw_scores / self.temperature,
        }
