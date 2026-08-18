"""RACE：不移动原型的角色对齐竞争证据。"""

from __future__ import annotations

import torch
import torch.nn.functional as F


CLASS_COUNT = 200
ROLE_COUNT = 8


def normalized_sentences(sentence_embeds: torch.Tensor) -> torch.Tensor:
    tensor = torch.as_tensor(sentence_embeds).float()
    if tensor.shape != (CLASS_COUNT, ROLE_COUNT, 768):
        raise ValueError(
            f"sentence embeddings must be [200, 8, 768], got {tuple(tensor.shape)}"
        )
    if not torch.isfinite(tensor).all():
        raise ValueError("sentence embeddings contain non-finite values")
    return F.normalize(tensor, dim=-1)


def same_role_text_rivals(sentences: torch.Tensor) -> torch.Tensor:
    """在固定 200 类语义全集中，为每类每角色冻结一个文本最近邻。"""
    sentences = normalized_sentences(sentences)
    rivals = torch.empty((CLASS_COUNT, ROLE_COUNT), dtype=torch.long)
    for role in range(ROLE_COUNT):
        similarity = sentences[:, role] @ sentences[:, role].T
        similarity.fill_diagonal_(-torch.inf)
        rivals[:, role] = similarity.argmax(dim=1)
    if torch.equal(rivals, torch.arange(CLASS_COUNT).view(-1, 1).expand_as(rivals)):
        raise RuntimeError("rival construction returned the identity mapping")
    own = torch.arange(CLASS_COUNT).view(-1, 1)
    if bool((rivals == own).any()):
        raise RuntimeError("a class cannot be its own rival")
    return rivals


class RACE:
    """冻结的决策级模块；所有角色项都是最终 raw score 的真实加数。"""

    MODES = ("aligned", "no_contrast", "wrong_role")

    def __init__(self, sentence_embeds: torch.Tensor, *, temperature: float = 0.05):
        if temperature <= 0:
            raise ValueError("temperature must be positive")
        self.sentences = normalized_sentences(sentence_embeds)
        self.base_prototypes = F.normalize(self.sentences.mean(dim=1), dim=-1)
        self.rivals = same_role_text_rivals(self.sentences)
        self.temperature = float(temperature)

    def to(self, device: torch.device | str) -> "RACE":
        self.sentences = self.sentences.to(device)
        self.base_prototypes = self.base_prototypes.to(device)
        self.rivals = self.rivals.to(device)
        return self

    def _validate_candidates(self, candidate_classes: torch.Tensor) -> torch.Tensor:
        candidates = torch.as_tensor(candidate_classes, device=self.sentences.device).long()
        if candidates.ndim != 1 or candidates.numel() == 0:
            raise ValueError("candidate classes must be a non-empty vector")
        if candidates.unique().numel() != candidates.numel():
            raise ValueError("candidate classes contain duplicates")
        if int(candidates.min()) < 0 or int(candidates.max()) >= CLASS_COUNT:
            raise ValueError("candidate class is outside [0, 199]")
        return candidates

    def score_parts(
        self,
        features: torch.Tensor,
        candidate_classes: torch.Tensor,
        *,
        strength: float,
        mode: str = "aligned",
    ) -> dict[str, torch.Tensor]:
        if mode not in self.MODES:
            raise ValueError(f"unsupported RACE mode: {mode}")
        if strength < 0:
            raise ValueError("strength must be non-negative")
        candidates = self._validate_candidates(candidate_classes)
        image = F.normalize(torch.as_tensor(features, device=self.sentences.device).float(), dim=-1)
        if image.ndim != 2 or image.shape[1] != 768:
            raise ValueError("features must have shape [N, 768]")

        target_text = self.sentences[candidates]
        target_scores = torch.einsum("nd,crd->ncr", image, target_text)
        rival_classes = self.rivals[candidates]
        roles = torch.arange(ROLE_COUNT, device=self.sentences.device).view(1, -1)
        if mode == "wrong_role":
            rival_roles = (roles + 1) % ROLE_COUNT
        else:
            rival_roles = roles
        rival_text = self.sentences[rival_classes, rival_roles]
        rival_scores = torch.einsum("nd,crd->ncr", image, rival_text)

        if mode == "no_contrast":
            evidence = target_scores
        else:
            evidence = target_scores - rival_scores
        contributions = float(strength) * evidence / ROLE_COUNT
        base_scores = image @ self.base_prototypes[candidates].T
        raw_scores = base_scores + contributions.sum(dim=-1)
        return {
            "base_scores": base_scores,
            "target_scores": target_scores,
            "rival_scores": rival_scores,
            "contributions": contributions,
            "raw_scores": raw_scores,
            "logits": raw_scores / self.temperature,
            "rival_classes": rival_classes,
        }

    def logits(
        self,
        features: torch.Tensor,
        candidate_classes: torch.Tensor,
        *,
        strength: float,
        mode: str = "aligned",
    ) -> torch.Tensor:
        return self.score_parts(
            features, candidate_classes, strength=strength, mode=mode
        )["logits"]

    def max_decomposition_error(
        self,
        features: torch.Tensor,
        candidate_classes: torch.Tensor,
        *,
        strength: float,
        mode: str = "aligned",
    ) -> float:
        parts = self.score_parts(
            features, candidate_classes, strength=strength, mode=mode
        )
        reconstructed = parts["base_scores"] + parts["contributions"].sum(dim=-1)
        return float((parts["raw_scores"] - reconstructed).abs().max().detach().cpu())
