"""Role-Contrastive Displacement Prototype (RCDP).

RCDP never performs within-class sentence attention.  For every semantic role,
it contrasts a class sentence with the most similar sentence from another
candidate class, maps that signed displacement with a small role-specific
low-rank transform, and adds the eight equal contributions to the raw mean
prototype.  The same computation is used for every candidate class.
"""

from __future__ import annotations

import math

import torch
import torch.nn as nn
import torch.nn.functional as F


CLASS_COUNT = 200
ROLE_COUNT = 8
EMBED_DIM = 768


def normalized_sentences(sentence_embeds: torch.Tensor) -> torch.Tensor:
    tensor = torch.as_tensor(sentence_embeds).detach().float()
    if tuple(tensor.shape) != (CLASS_COUNT, ROLE_COUNT, EMBED_DIM):
        raise ValueError("sentence embeddings must have shape [200, 8, 768]")
    if not torch.isfinite(tensor).all():
        raise ValueError("sentence embeddings contain non-finite values")
    return F.normalize(tensor, dim=-1)


def validate_candidate_classes(candidate_classes: torch.Tensor) -> torch.Tensor:
    classes = torch.as_tensor(candidate_classes).detach().long()
    if classes.ndim != 1 or classes.numel() < 2:
        raise ValueError("candidate classes must be a one-dimensional set")
    if classes.unique().numel() != classes.numel():
        raise ValueError("candidate classes must be unique")
    if int(classes.min()) < 0 or int(classes.max()) >= CLASS_COUNT:
        raise ValueError("candidate class id is outside [0, 199]")
    return classes.sort().values


def same_role_rivals(
    normalized: torch.Tensor, candidate_classes: torch.Tensor
) -> tuple[torch.Tensor, torch.Tensor]:
    """Return signed role displacements and global rival ids.

    Rival search is performed independently for each role and never returns
    the class itself.  No image or label is used.
    """

    classes = validate_candidate_classes(candidate_classes).to(normalized.device)
    selected = normalized.index_select(0, classes)  # [C, R, D]
    by_role = selected.transpose(0, 1)  # [R, C, D]
    similarities = torch.matmul(by_role, by_role.transpose(1, 2))
    diagonal = torch.eye(classes.numel(), dtype=torch.bool, device=normalized.device)
    similarities = similarities.masked_fill(diagonal.unsqueeze(0), float("-inf"))
    rival_local = similarities.argmax(dim=-1)  # [R, C]
    rival_global = classes[rival_local].transpose(0, 1).contiguous()  # [C, R]
    role_ids = torch.arange(ROLE_COUNT, device=normalized.device).view(1, ROLE_COUNT)
    rival_sentences = normalized[rival_global, role_ids]
    displacements = selected - rival_sentences
    if torch.equal(rival_global, classes.view(-1, 1).expand_as(rival_global)):
        raise RuntimeError("same-role rival search returned only self ids")
    if (rival_global == classes.view(-1, 1)).any():
        raise RuntimeError("same-role rival search returned a self id")
    return displacements, rival_global


class RCDP(nn.Module):
    """One shared prototype formula for a fixed candidate class set."""

    def __init__(
        self,
        sentence_embeds: torch.Tensor,
        candidate_classes: torch.Tensor,
        *,
        rank: int = 32,
        gate_init: float = 0.05,
        gate_cap: float = 0.35,
        temperature: float = 0.05,
    ) -> None:
        super().__init__()
        if rank <= 0 or rank > EMBED_DIM:
            raise ValueError("rank must be in [1, 768]")
        if not 0.0 < gate_init < gate_cap <= 1.0:
            raise ValueError("gate must satisfy 0 < gate_init < gate_cap <= 1")
        if temperature <= 0.0:
            raise ValueError("temperature must be positive")

        normalized = normalized_sentences(sentence_embeds)
        classes = validate_candidate_classes(candidate_classes)
        displacements, rivals = same_role_rivals(normalized, classes)
        global_to_local = torch.full((CLASS_COUNT,), -1, dtype=torch.long)
        global_to_local[classes] = torch.arange(classes.numel())

        self.register_buffer("sentence_embeds", normalized, persistent=True)
        self.register_buffer("candidate_classes", classes, persistent=True)
        self.register_buffer("global_to_local", global_to_local, persistent=False)
        self.register_buffer("rival_displacements", displacements, persistent=True)
        self.register_buffer("rival_class_ids", rivals, persistent=True)

        self.down = nn.Parameter(torch.empty(ROLE_COUNT, EMBED_DIM, rank))
        self.up = nn.Parameter(torch.zeros(ROLE_COUNT, rank, EMBED_DIM))
        nn.init.normal_(self.down, mean=0.0, std=0.02)
        ratio = gate_init / gate_cap
        self.gate_logit = nn.Parameter(torch.tensor(math.log(ratio / (1.0 - ratio))))
        self.gate_cap = float(gate_cap)
        self.temperature = float(temperature)

    def base_vectors(self) -> torch.Tensor:
        sentences = self.sentence_embeds.index_select(0, self.candidate_classes)
        return sentences.mean(dim=1)

    def base_prototypes(self) -> torch.Tensor:
        return F.normalize(self.base_vectors(), dim=-1)

    def gate(self) -> torch.Tensor:
        return self.gate_cap * torch.sigmoid(self.gate_logit)

    def role_contributions(self) -> torch.Tensor:
        hidden = torch.einsum("crd,rdk->crk", self.rival_displacements, self.down)
        hidden = F.gelu(hidden)
        mapped = torch.einsum("crk,rkd->crd", hidden, self.up)
        mapped = mapped / math.sqrt(self.down.shape[-1])
        # Each role direction has norm at most one.  Scaling by the raw base
        # norm makes the bound relative to the prototype being moved: every
        # role contributes at most gate*||base||/8 and their sum at most
        # gate*||base||, independent of the learned weight norms.
        bounded = mapped / mapped.norm(dim=-1, keepdim=True).clamp_min(1.0)
        base_norm = self.base_vectors().norm(dim=-1).view(-1, 1, 1)
        return self.gate() * base_norm * bounded / ROLE_COUNT

    def prototypes(self, *, residual_enabled: bool = True) -> torch.Tensor:
        base = self.base_vectors()
        if not residual_enabled:
            return F.normalize(base, dim=-1)
        displacement = self.role_contributions().sum(dim=1)
        return F.normalize(base + displacement, dim=-1)

    def local_indices(self, class_ids: torch.Tensor) -> torch.Tensor:
        ids = torch.as_tensor(class_ids, device=self.global_to_local.device).long()
        local = self.global_to_local.index_select(0, ids)
        if (local < 0).any():
            raise ValueError("requested class is outside this candidate set")
        return local

    def logits(
        self, image_features: torch.Tensor, class_ids: torch.Tensor | None = None
    ) -> torch.Tensor:
        prototypes = self.prototypes()
        if class_ids is not None:
            prototypes = prototypes.index_select(0, self.local_indices(class_ids))
        images = F.normalize(image_features.float(), dim=-1)
        return images @ prototypes.T / self.temperature

    @torch.no_grad()
    def diagnostics(self) -> dict[str, object]:
        base = self.base_prototypes()
        adapted = self.prototypes()
        contributions = self.role_contributions()
        return {
            "gate": float(self.gate().cpu()),
            "base_adapted_cosine_min": float(
                F.cosine_similarity(base, adapted, dim=-1).min().cpu()
            ),
            "base_adapted_cosine_mean": float(
                F.cosine_similarity(base, adapted, dim=-1).mean().cpu()
            ),
            "role_contribution_norm_mean": contributions.norm(dim=-1)
            .mean(dim=0)
            .cpu()
            .tolist(),
            "role_contribution_norm_max": float(
                contributions.norm(dim=-1).max().cpu()
            ),
            "total_displacement_norm_max": float(
                contributions.sum(dim=1).norm(dim=-1).max().cpu()
            ),
            "total_displacement_to_base_ratio_max": float(
                (
                    contributions.sum(dim=1).norm(dim=-1)
                    / self.base_vectors().norm(dim=-1).clamp_min(1e-12)
                )
                .max()
                .cpu()
            ),
            "rival_class_ids": self.rival_class_ids.cpu().tolist(),
        }
