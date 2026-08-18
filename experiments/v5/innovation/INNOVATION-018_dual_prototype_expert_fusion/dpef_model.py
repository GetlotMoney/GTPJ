"""Models for V5-INNOVATION-018 dual-prototype expert fusion."""

from __future__ import annotations

import math

import torch
import torch.nn as nn
import torch.nn.functional as F


SENTENCE_SHAPE = (200, 8, 768)


def normalized_sentences(sentence_embeds: torch.Tensor) -> torch.Tensor:
    if tuple(sentence_embeds.shape) != SENTENCE_SHAPE:
        raise ValueError(
            f"sentence embeddings must be {SENTENCE_SHAPE}, "
            f"got {tuple(sentence_embeds.shape)}"
        )
    value = sentence_embeds.detach().float()
    if not torch.isfinite(value).all():
        raise ValueError("sentence embeddings contain non-finite values")
    return F.normalize(value, dim=-1)


class SharedPSE(nn.Module):
    """Frozen source expert; state keys match V5-INNOVATION-017/RUN-002."""

    def __init__(
        self,
        sentence_embeds: torch.Tensor,
        *,
        temperature: float = 0.05,
        heads: int = 4,
        dropout: float = 0.1,
        residual_cap: float = 0.35,
    ) -> None:
        super().__init__()
        self.register_buffer(
            "sentence_embeds", normalized_sentences(sentence_embeds), persistent=True
        )
        self.attention = nn.MultiheadAttention(
            768, heads, dropout=dropout, batch_first=True
        )
        self.context_projection = nn.Linear(768, 768)
        self.role_scorer = nn.Sequential(
            nn.Linear(768, 192), nn.GELU(), nn.Linear(192, 1)
        )
        nn.init.zeros_(self.role_scorer[-1].weight)
        nn.init.zeros_(self.role_scorer[-1].bias)
        self.residual_gate = nn.Parameter(torch.zeros(()))
        self.residual_cap = float(residual_cap)
        self.temperature = float(temperature)

    def base_prototypes(self) -> torch.Tensor:
        return F.normalize(self.sentence_embeds.mean(dim=1), dim=-1)

    def prototypes(self) -> torch.Tensor:
        attended, _ = self.attention(
            self.sentence_embeds,
            self.sentence_embeds,
            self.sentence_embeds,
            need_weights=False,
        )
        contextual = F.normalize(
            self.sentence_embeds + self.context_projection(attended), dim=-1
        )
        weights = F.softmax(self.role_scorer(contextual).squeeze(-1), dim=1)
        pooled = (weights.unsqueeze(-1) * contextual).sum(dim=1)
        base = self.base_prototypes()
        gate = self.residual_cap * torch.tanh(self.residual_gate)
        return F.normalize(base + gate * (pooled - base), dim=-1)


class UniformSeenPrototypeExpert(nn.Module):
    """Fixed-uniform sentence mapper applied only to seen class prototypes.

    Q/K parameters exist only to reproduce the reviewed historical uniform-PSE
    initialization. The forward path uses V/out projections with fixed 1/M weights;
    no sentence can be selected by attention.
    """

    def __init__(
        self,
        sentence_embeds: torch.Tensor,
        seenclasses: torch.Tensor,
        *,
        heads: int = 4,
        dropout: float = 0.5,
        inner_ratio: float = 0.35,
        outer_ratio: float = 0.65,
        temperature_init: float = 0.07,
    ) -> None:
        super().__init__()
        normalized = normalized_sentences(sentence_embeds)
        seen = torch.as_tensor(seenclasses).detach().long()
        if seen.ndim != 1 or seen.unique().numel() != seen.numel():
            raise ValueError("seenclasses must be unique one-dimensional ids")
        if int(seen.min()) < 0 or int(seen.max()) >= 200:
            raise ValueError("seenclasses are outside the 200-class axis")
        self.register_buffer("sentence_embeds", normalized, persistent=True)
        self.register_buffer("seenclasses", seen, persistent=True)
        self.attention = nn.MultiheadAttention(
            768, heads, dropout=dropout, batch_first=True
        )
        self.context_projection = nn.Linear(768, 768)
        self.dropout = nn.Dropout(dropout)
        self.layer_norm = nn.LayerNorm(768)
        self.inner_ratio = float(inner_ratio)
        self.outer_ratio = float(outer_ratio)
        self.logit_scale = nn.Parameter(torch.tensor(math.log(1.0 / temperature_init)))

    def base_prototypes(self) -> torch.Tensor:
        return F.normalize(self.sentence_embeds.mean(dim=1), dim=-1)

    def _uniform_value_path(self, x: torch.Tensor) -> torch.Tensor:
        batch, tokens, dim = x.shape
        heads = self.attention.num_heads
        head_dim = dim // heads
        _, _, value_weight = self.attention.in_proj_weight.chunk(3, dim=0)
        _, _, value_bias = self.attention.in_proj_bias.chunk(3, dim=0)
        value = F.linear(x, value_weight, value_bias)
        value = value.view(batch, tokens, heads, head_dim).transpose(1, 2)
        weights = x.new_full((batch, heads, tokens, tokens), 1.0 / tokens)
        weights = F.dropout(
            weights, p=float(self.attention.dropout), training=self.training
        )
        context = torch.matmul(weights, value)
        context = context.transpose(1, 2).contiguous().view(batch, tokens, dim)
        return F.linear(
            context,
            self.attention.out_proj.weight,
            self.attention.out_proj.bias,
        )

    def prototypes(self) -> torch.Tensor:
        seen_sentences = self.sentence_embeds.index_select(0, self.seenclasses)
        value_context = self._uniform_value_path(seen_sentences)
        projected = self.dropout(self.context_projection(value_context))
        contextual = self.layer_norm(
            2.0
            * (
                self.inner_ratio * projected
                + (1.0 - self.inner_ratio) * seen_sentences
            )
        )
        adapted_seen = F.normalize(
            self.outer_ratio * contextual.mean(dim=1)
            + (1.0 - self.outer_ratio) * seen_sentences.mean(dim=1),
            dim=-1,
        )
        prototypes = self.base_prototypes().clone()
        prototypes[self.seenclasses] = adapted_seen
        return prototypes

    def logits(
        self, image_features: torch.Tensor, class_ids: torch.Tensor | None = None
    ) -> torch.Tensor:
        prototypes = self.prototypes()
        if class_ids is not None:
            prototypes = prototypes.index_select(
                0, torch.as_tensor(class_ids, device=prototypes.device).long()
            )
        scale = torch.clamp(self.logit_scale.exp(), max=100.0)
        return F.normalize(image_features.float(), dim=-1) @ prototypes.T * scale

    def topology_loss(self) -> torch.Tensor:
        base = self.base_prototypes()
        adapted = self.prototypes()
        mask = ~torch.eye(200, dtype=torch.bool, device=base.device)
        base_vector = (base @ base.T)[mask].detach()
        adapted_vector = (adapted @ adapted.T)[mask]
        base_vector = base_vector - base_vector.mean()
        adapted_vector = adapted_vector - adapted_vector.mean()
        numerator = (base_vector * adapted_vector).sum()
        denominator = torch.sqrt((base_vector.square()).sum() + 1e-8) * torch.sqrt(
            (adapted_vector.square()).sum() + 1e-8
        )
        return 1.0 - numerator / denominator


def fused_prototypes(
    strong: torch.Tensor,
    shared: torch.Tensor,
    raw: torch.Tensor,
    seenclasses: torch.Tensor,
    unseenclasses: torch.Tensor,
    *,
    seen_blend: float,
    unseen_blend: float,
) -> torch.Tensor:
    """Fuse two prototype experts on the known GZSL class split."""
    if not 0.0 <= seen_blend <= 1.0 or not 0.0 <= unseen_blend <= 1.0:
        raise ValueError("fusion coefficients must be in [0, 1]")
    if strong.shape != shared.shape or strong.shape != raw.shape:
        raise ValueError("all prototype tensors must have the same shape")
    seen = torch.as_tensor(seenclasses, device=strong.device).long()
    unseen = torch.as_tensor(unseenclasses, device=strong.device).long()
    combined = strong.clone()
    combined[seen] = F.normalize(
        (1.0 - seen_blend) * strong[seen] + seen_blend * shared[seen], dim=-1
    )
    combined[unseen] = F.normalize(
        (1.0 - unseen_blend) * raw[unseen] + unseen_blend * shared[unseen], dim=-1
    )
    return combined
