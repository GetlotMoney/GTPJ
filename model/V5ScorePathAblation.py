"""V5-ABLATION-008 的四条明确分数路径。

这里刻意使用四个明确对象，而不是在母版模型里堆叠 ``use_x`` 开关。
G/L 的共享参数由同一种子构造的 canonical GTPJ donor 严格复制，确保
消融差异来自路径本身，而不是模块构造顺序改变了随机初始化。
"""

from __future__ import annotations

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from model.MyModel import (
    BidirectionalVisualSemanticAlignment,
    GTPJ,
    ProgressiveSemanticSelfAttention,
)


VALID_SCORE_PATHS = frozenset({"frozen_clip", "global", "local", "full"})


def _validated_class_ids(config, seenclass, unseenclass):
    nclass = int(config.num_class)
    seen_ids = torch.as_tensor(seenclass).detach().cpu().long()
    unseen_ids = torch.as_tensor(unseenclass).detach().cpu().long()
    if seen_ids.dim() != 1 or unseen_ids.dim() != 1:
        raise ValueError("seenclass and unseenclass must be one-dimensional global ids.")
    if seen_ids.unique().numel() != seen_ids.numel():
        raise ValueError("seenclass contains duplicate global ids.")
    if unseen_ids.unique().numel() != unseen_ids.numel():
        raise ValueError("unseenclass contains duplicate global ids.")
    if torch.isin(seen_ids, unseen_ids).any():
        raise ValueError("seenclass and unseenclass must not overlap.")
    combined = torch.cat([seen_ids, unseen_ids]).sort().values
    if not torch.equal(combined, torch.arange(nclass, dtype=torch.long)):
        raise ValueError("seenclass and unseenclass must cover every global class exactly once.")
    return seen_ids, unseen_ids


def _validate_text_shapes(dim_f, seen_ids, unseen_ids, seen_text, unseen_text):
    if tuple(seen_text.shape) != (seen_ids.numel(), dim_f):
        raise ValueError("seen_text_embeds must have shape [C_seen, D].")
    if tuple(unseen_text.shape) != (unseen_ids.numel(), dim_f):
        raise ValueError("unseen_text_embeds must have shape [C_unseen, D].")


class FrozenClipScorer(nn.Module):
    """冻结 CLIP CLS 与未适配 gpt55 句子均值文本的余弦分类器。"""

    def __init__(self, config, seenclass, unseenclass, seen_text_embeds, unseen_text_embeds):
        super().__init__()
        self.nclass = int(config.num_class)
        self.dim_f = int(config.dim_f_clip)
        seen_ids, unseen_ids = _validated_class_ids(config, seenclass, unseenclass)
        _validate_text_shapes(
            self.dim_f, seen_ids, unseen_ids, seen_text_embeds, unseen_text_embeds
        )
        all_text = torch.zeros(self.nclass, self.dim_f, dtype=seen_text_embeds.dtype)
        all_text[seen_ids] = F.normalize(seen_text_embeds.detach(), dim=1)
        all_text[unseen_ids] = F.normalize(unseen_text_embeds.detach(), dim=1)
        self.register_buffer("seenclass", seen_ids, persistent=False)
        self.register_buffer("unseenclass", unseen_ids, persistent=False)
        self.register_buffer("class_text", all_text, persistent=True)

    def forward(self, clip_features, is_train=False):
        if is_train:
            raise ValueError("FrozenClipScorer is evaluation-only; is_train=True is invalid.")
        if clip_features.dim() != 3 or clip_features.size(1) != 577:
            raise ValueError("FrozenClipScorer requires clip_features shaped [B, 577, D].")
        if clip_features.size(2) != self.dim_f:
            raise ValueError(f"FrozenClipScorer requires D={self.dim_f}.")
        image = F.normalize(clip_features[:, 0, :], dim=1)
        text = self.class_text.to(device=image.device, dtype=image.dtype)
        logits = image @ text.T
        return {
            "logits": logits,
            "final_logits": logits,
            "clip_S_pp": logits,
            "evaluation_only": True,
            "score_mode": "frozen_gpt55_cosine",
        }


class _PseIcsaScoreBase(nn.Module):
    """只复用 PSE/ICSA、类别轴和标签映射的短共享基类。"""

    def __init__(
        self,
        config,
        seenclass,
        unseenclass,
        seen_text_embeds,
        unseen_text_embeds,
        seen_sentence_embeds,
    ):
        super().__init__()
        self.config = config
        self.nclass = int(config.num_class)
        self.dim_f = int(config.dim_f_clip)
        seen_ids, unseen_ids = _validated_class_ids(config, seenclass, unseenclass)
        _validate_text_shapes(
            self.dim_f, seen_ids, unseen_ids, seen_text_embeds, unseen_text_embeds
        )
        if (
            seen_sentence_embeds is None
            or seen_sentence_embeds.dim() != 3
            or seen_sentence_embeds.size(0) != seen_ids.numel()
            or seen_sentence_embeds.size(-1) != self.dim_f
        ):
            raise ValueError("seen_sentence_embeds must have shape [C_seen, M, D].")

        self.register_buffer("seenclass", seen_ids, persistent=False)
        self.register_buffer("unseenclass", unseen_ids, persistent=False)
        self.seen_text_embeds = nn.Parameter(
            F.normalize(seen_text_embeds, dim=1), requires_grad=False
        )
        self.unseen_text_embeds = nn.Parameter(
            F.normalize(unseen_text_embeds, dim=1), requires_grad=False
        )
        self.seen_sentence_embeds = nn.Parameter(
            F.normalize(seen_sentence_embeds, dim=-1), requires_grad=False
        )
        self.pse_outer_ratio = float(config.pse_outer_ratio)
        self.pse_module = ProgressiveSemanticSelfAttention(
            dim=self.dim_f,
            heads=int(config.pse_heads),
            dropout=float(config.pse_dropout),
            inner_ratio=float(config.pse_inner_ratio),
        )
        hidden = int(config.icsa_hidden)
        self.icsa_module = nn.Sequential(
            nn.Linear(self.dim_f, hidden),
            nn.LayerNorm(hidden),
            nn.GELU(),
            nn.Linear(hidden, self.dim_f),
        )
        with torch.no_grad():
            self.icsa_module[-1].weight.zero_()
            self.icsa_module[-1].bias.zero_()
        self.icsa_ratio = float(config.icsa_ratio)
        if self.icsa_ratio <= 0:
            raise ValueError("icsa_ratio must be greater than zero.")

    def _validate_features(self, clip_features):
        if clip_features.dim() != 3 or clip_features.size(1) != 577:
            raise ValueError("score-path models require clip_features shaped [B, 577, D].")
        if clip_features.size(2) != self.dim_f:
            raise ValueError(f"score-path models require D={self.dim_f}.")

    def get_adapted_seen_text(self):
        base = self.seen_sentence_embeds.mean(dim=1)
        attended = self.pse_module(self.seen_sentence_embeds).mean(dim=1)
        adapted = self.pse_outer_ratio * attended + (1.0 - self.pse_outer_ratio) * base
        return F.normalize(adapted, dim=1)

    def get_adapted_unseen_text(self):
        return self.unseen_text_embeds

    def _make_all_text(self, device, dtype):
        all_text = torch.zeros(self.nclass, self.dim_f, device=device, dtype=dtype)
        all_text[self.seenclass.to(device)] = self.get_adapted_seen_text().to(device, dtype)
        all_text[self.unseenclass.to(device)] = self.get_adapted_unseen_text().to(
            device, dtype
        )
        return all_text

    def _condition_text(self, cls_token):
        all_text = self._make_all_text(cls_token.device, cls_token.dtype)
        image_condition = F.normalize(self.icsa_module(cls_token), dim=-1)
        conditioned = all_text.unsqueeze(0).expand(cls_token.size(0), -1, -1).clone()
        seen_idx = self.seenclass.to(cls_token.device)
        conditioned[:, seen_idx, :] = (
            all_text[seen_idx].unsqueeze(0)
            + self.icsa_ratio * image_condition.unsqueeze(1)
        )
        return conditioned

    def _topology_pearson_loss(self):
        adapted_seen = self.get_adapted_seen_text()
        device, dtype = adapted_seen.device, adapted_seen.dtype
        base_text = torch.zeros(self.nclass, self.dim_f, device=device, dtype=dtype)
        enhanced = torch.zeros_like(base_text)
        seen_idx = self.seenclass.to(device)
        unseen_idx = self.unseenclass.to(device)
        base_text[seen_idx] = self.seen_text_embeds.to(device=device, dtype=dtype)
        base_text[unseen_idx] = self.unseen_text_embeds.to(device=device, dtype=dtype)
        enhanced[seen_idx] = adapted_seen
        enhanced[unseen_idx] = base_text[unseen_idx]
        base_sim = F.normalize(base_text.float(), dim=-1)
        base_sim = base_sim @ base_sim.T
        enhanced_sim = F.normalize(enhanced.float(), dim=-1)
        enhanced_sim = enhanced_sim @ enhanced_sim.T
        off_diag = ~torch.eye(self.nclass, dtype=torch.bool, device=device)
        base_vec = base_sim.detach()[off_diag]
        enhanced_vec = enhanced_sim[off_diag]
        base_centered = base_vec - base_vec.mean()
        enhanced_centered = enhanced_vec - enhanced_vec.mean()
        numerator = (base_centered * enhanced_centered).sum()
        denominator = torch.sqrt((base_centered.square()).sum() + 1e-8) * torch.sqrt(
            (enhanced_centered.square()).sum() + 1e-8
        )
        return 1.0 - numerator / denominator

    def _global_to_seen_labels(self, labels):
        labels = labels.to(device=self.seenclass.device, dtype=torch.long)
        mapping = torch.full(
            (self.nclass,), -1, device=self.seenclass.device, dtype=torch.long
        )
        mapping[self.seenclass] = torch.arange(
            self.seenclass.numel(), device=self.seenclass.device
        )
        local = mapping[labels]
        if (local < 0).any():
            raise ValueError("Training labels must be global ids from seen classes.")
        return local

    def _ce_and_topology(self, package):
        logits = package["logits"]
        labels = package["batch_label"]
        if labels.dim() > 1:
            labels = labels.argmax(dim=1)
        labels = labels.to(device=logits.device, dtype=torch.long)
        seen_labels = self._global_to_seen_labels(labels).to(logits.device)
        loss_ce = F.cross_entropy(logits, seen_labels)
        loss_topo = torch.tensor(0.0, device=logits.device)
        topology_weight = float(self.config.lambda_topo_pearson)
        if topology_weight > 0:
            loss_topo = self._topology_pearson_loss()
        return labels, loss_ce, loss_topo, loss_ce + topology_weight * loss_topo


class GlobalScoreModel(_PseIcsaScoreBase):
    """只保留 PSE、ICSA、全局余弦分数、CE 和 topology。"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logit_scale = nn.Parameter(torch.ones([]) * np.log(1 / 0.07))

    def forward(self, clip_features, is_train=False):
        self._validate_features(clip_features)
        cls_token = clip_features[:, 0, :]
        conditioned = self._condition_text(cls_token)
        image = F.normalize(cls_token, dim=1)
        text = F.normalize(conditioned, dim=-1)
        scale = torch.clamp(self.logit_scale.exp(), max=100.0)
        global_logits = (image.unsqueeze(1) * text).sum(dim=-1) * scale
        logits = (
            global_logits[:, self.seenclass.to(global_logits.device)]
            if is_train
            else global_logits
        )
        return {
            "logits": logits,
            "final_logits": global_logits,
            "global_logits": global_logits,
            "clip_S_pp": logits,
            "all_text_cond": conditioned,
        }

    def compute_loss(self, package):
        _, loss_ce, loss_topo, loss = self._ce_and_topology(package)
        return {"loss": loss, "loss_ce": loss_ce, "loss_topo": loss_topo}


class LocalScoreModel(_PseIcsaScoreBase):
    """只用局部分数分类；没有 global logits 或 global logit scale。"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        config = self.config
        common_dim = int(config.tf_common_dim)
        self.bvsa_module = BidirectionalVisualSemanticAlignment(
            dim_f=self.dim_f,
            dim_com=common_dim,
            heads=int(config.tf_heads),
            dropout=float(config.tf_dropout),
            weight_s2v=float(config.weight_s2v),
            grid_size=(24, 24),
            dim_g=64,
        )
        self.fgvd_select_k = int(config.fgvd_select_k)
        self.sgmp_topk = int(config.sgmp_topk)
        self.sgmp_neg_margin = float(config.sgmp_neg_margin)
        hidden = int(config.sgmp_hidden)
        self.sgmp_predictor = nn.Sequential(
            nn.Linear(common_dim * 2, hidden),
            nn.LayerNorm(hidden),
            nn.GELU(),
            nn.Linear(hidden, common_dim),
        )

    def forward(self, clip_features, is_train=False):
        self._validate_features(clip_features)
        cls_token = clip_features[:, 0, :]
        patches = clip_features[:, 1:, :]
        conditioned = self._condition_text(cls_token)
        bvsa = self.bvsa_module(
            patches, conditioned, fgvd_select_k=self.fgvd_select_k
        )
        local_logits = bvsa["local_score"]
        logits = (
            local_logits[:, self.seenclass.to(local_logits.device)]
            if is_train
            else local_logits
        )
        return {
            "logits": logits,
            "final_logits": local_logits,
            "local_logits": local_logits,
            "clip_S_pp": logits,
            "score_s2v": bvsa["score_s2v"],
            "score_v2s": bvsa["score_v2s"],
            "sgmp_selected_patches": bvsa["fgvd_selected_patches"],
            "sgmp_patch_z": bvsa["fgvd_patch_z"],
            "sgmp_memory": bvsa["fgvd_memory"],
            "all_text_cond": conditioned,
        }

    def _semantic_guided_masked_prediction_loss(self, labels, package):
        patches = package["sgmp_selected_patches"]
        patch_z = package["sgmp_patch_z"]
        memory = package["sgmp_memory"]
        conditioned = package["all_text_cond"]
        batch, count, _ = patches.shape
        if count < 2:
            zero = torch.tensor(0.0, device=labels.device)
            return zero, zero
        k = max(1, min(self.sgmp_topk, count - 1))
        batch_idx = torch.arange(batch, device=labels.device)
        class_text = conditioned[batch_idx, labels].to(dtype=patches.dtype)
        with torch.no_grad():
            similarity = torch.einsum(
                "bnd,bd->bn", F.normalize(patches.float(), dim=-1), F.normalize(class_text.float(), dim=-1)
            )
            masked_idx = torch.topk(similarity, k=k, dim=1, largest=True).indices
        mask = torch.zeros(batch, count, dtype=torch.bool, device=labels.device)
        mask.scatter_(1, masked_idx, True)
        keep = (~mask).unsqueeze(-1).to(memory.dtype)
        context = (memory * keep).sum(dim=1) / keep.sum(dim=1).clamp_min(1.0)
        target = patch_z[mask].view(batch, k, -1).mean(dim=1).detach()
        text_z = self.bvsa_module.embed_text(class_text)
        prediction = self.sgmp_predictor(torch.cat([context, text_z], dim=-1))
        positive = F.cosine_similarity(prediction, target, dim=-1)
        loss_mpp = (1.0 - positive).mean()
        mapping = torch.full((self.nclass,), -1, device=labels.device, dtype=torch.long)
        seen = self.seenclass.to(labels.device)
        mapping[seen] = torch.arange(seen.numel(), device=labels.device)
        local_labels = mapping[labels]
        if (local_labels < 0).any():
            raise ValueError("SGMP expects global labels from seen classes.")
        negative_labels = seen[(local_labels + 1) % seen.numel()]
        negative_text = conditioned[batch_idx, negative_labels].to(dtype=patches.dtype)
        negative_z = self.bvsa_module.embed_text(negative_text)
        prediction_neg = self.sgmp_predictor(
            torch.cat([context.detach(), negative_z], dim=-1)
        )
        negative = F.cosine_similarity(prediction_neg, target, dim=-1)
        loss_neg = F.relu(negative - positive.detach() + self.sgmp_neg_margin).mean()
        return loss_mpp, loss_neg

    def compute_loss(self, package):
        labels, loss_ce, loss_topo, loss = self._ce_and_topology(package)
        loss_mpp, loss_neg = self._semantic_guided_masked_prediction_loss(labels, package)
        loss = loss + float(self.config.lambda_mpp) * loss_mpp
        loss = loss + float(self.config.lambda_neg) * loss_neg
        score_s2v = package["score_s2v"]
        score_v2s = package["score_v2s"]
        loss_bmdd = torch.tensor(0.0, device=loss.device)
        weight_bmdd = float(self.config.lambda_bmdd)
        if weight_bmdd > 0:
            temperature = float(self.config.msdn_temp)
            seen = self.seenclass.to(loss.device)
            s2v = score_s2v[:, seen] / temperature
            v2s = score_v2s[:, seen] / temperature
            loss_bmdd = (temperature * temperature / 2.0) * (
                F.kl_div(F.log_softmax(v2s, dim=-1), F.softmax(s2v, dim=-1).detach(), reduction="batchmean")
                + F.kl_div(F.log_softmax(s2v, dim=-1), F.softmax(v2s, dim=-1).detach(), reduction="batchmean")
            )
            loss = loss + weight_bmdd * loss_bmdd
        return {
            "loss": loss,
            "loss_ce": loss_ce,
            "loss_topo": loss_topo,
            "loss_bmdd": loss_bmdd,
            "loss_mpp": loss_mpp,
            "loss_neg": loss_neg,
        }


def _copy_shared_canonical_state(candidate, donor):
    donor_state = donor.state_dict()
    candidate_state = candidate.state_dict()
    missing = [
        name
        for name, value in candidate_state.items()
        if name not in donor_state or donor_state[name].shape != value.shape
    ]
    if missing:
        raise RuntimeError("canonical donor lacks exact shared state: " + ", ".join(missing))
    candidate.load_state_dict(
        {name: donor_state[name].detach().clone() for name in candidate_state},
        strict=True,
    )
    return candidate


def build_score_path_model(
    score_path,
    config,
    seenclass,
    unseenclass,
    seen_text_embeds,
    unseen_text_embeds,
    seen_sentence_embeds,
    *,
    initialization_seed,
):
    """构造一条路径；G/L 共享参数严格来自同一种子的 canonical donor。"""
    if score_path not in VALID_SCORE_PATHS:
        raise ValueError(f"score_path must be one of {sorted(VALID_SCORE_PATHS)}.")
    if score_path == "frozen_clip":
        return FrozenClipScorer(
            config, seenclass, unseenclass, seen_text_embeds, unseen_text_embeds
        )
    args = (
        config,
        seenclass,
        unseenclass,
        seen_text_embeds,
        unseen_text_embeds,
        seen_sentence_embeds,
    )
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(int(initialization_seed))
        donor = GTPJ(*args)
        if score_path == "full":
            return donor
        candidate_type = GlobalScoreModel if score_path == "global" else LocalScoreModel
        candidate = candidate_type(*args)
        return _copy_shared_canonical_state(candidate, donor)
