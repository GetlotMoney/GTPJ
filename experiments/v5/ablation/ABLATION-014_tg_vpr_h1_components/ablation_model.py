from __future__ import annotations

import torch
import torch.nn.functional as F

from tg_vpr_h1_model import TGVPRH1


class TGVPRH1Ablation(TGVPRH1):
    MODES = {
        "single_group_value",
        "three_group_no_value",
        "three_group_fixed_equal_value",
        "full_h1_learned_weights",
    }

    def __init__(self, *args, ablation_mode: str, **kwargs):
        super().__init__(*args, **kwargs)
        if ablation_mode not in self.MODES:
            raise ValueError("unsupported H1 ablation_mode.")
        self.ablation_mode = ablation_mode

    def semantic_group_weights(self) -> torch.Tensor:
        if self.ablation_mode == "full_h1_learned_weights":
            return super().semantic_group_weights()
        return self.sentence_embeds.new_full((3,), 1.0 / 3.0)

    def candidate_base_vectors(self) -> torch.Tensor:
        if self.ablation_mode == "single_group_value":
            candidate = self.base_vectors().clone()
            normalized = self.base_prototypes()
            candidate[self.adapted_classes] = normalized.index_select(
                0, self.adapted_classes
            )
            return candidate
        return super().candidate_base_vectors()

    def transformed_groups(self) -> torch.Tensor:
        if self.ablation_mode != "single_group_value":
            return super().transformed_groups()
        source = self.base_prototypes().index_select(0, self.adapted_classes).unsqueeze(1)
        batch, group_count, dim = source.shape
        value = self.tg_value_projection(source)
        value = value.view(batch, group_count, 1, dim).transpose(1, 2)
        weights = source.new_ones((batch, 1, group_count, group_count))
        weights = F.dropout(weights, p=float(self.dropout.p), training=self.training)
        context = torch.einsum("bhqg,bhgd->bhqd", weights, value)
        context = context.transpose(1, 2).contiguous().view(batch, group_count, dim)
        context = self.tg_output_projection(context)
        context = self.dropout(self.post_projection(context))
        mixed = self.inner_ratio * context + (1.0 - self.inner_ratio) * source
        return self.layer_norm(2.0 * mixed)

    def prototype_components(self):
        if self.ablation_mode == "three_group_no_value":
            candidate = self.candidate_base_vectors()
            base_part = candidate.clone()
            role_part = candidate.new_zeros((200, 3, 768))
            return candidate, base_part, role_part
        if self.ablation_mode == "single_group_value":
            transformed = F.normalize(self.transformed_groups(), dim=-1)
            base = self.candidate_base_vectors()
            base_scale = base.new_ones((200,))
            base_scale[self.adapted_classes] = 1.0 - self.outer_ratio
            base_part = base_scale.unsqueeze(-1) * base
            role_part = transformed.new_zeros((200, 1, 768))
            role_part[self.adapted_classes] = self.outer_ratio * transformed
            return base_part + role_part.sum(dim=1), base_part, role_part
        return super().prototype_components()
