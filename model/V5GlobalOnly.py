"""V5-ABLATION-011 的最小 global-only 因果消融模型。"""

from __future__ import annotations

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from model.MyModel import GTPJ, ProgressiveSemanticSelfAttention


class GlobalOnlyGTPJ(GTPJ):
    """只保留 canonical V5 的 PSE、ICSA、全局分数和文本拓扑损失。"""

    def __init__(
        self,
        config,
        seenclass,
        unseenclass,
        seen_text_embeds,
        unseen_text_embeds,
        seen_sentence_embeds,
    ):
        nn.Module.__init__(self)
        if getattr(config, "score_path", "global_only") != "global_only":
            raise ValueError("GlobalOnlyGTPJ 只接受 score_path='global_only'。")

        self.config = config
        self.nclass = int(config.num_class)
        self.dim_f = int(config.dim_f_clip)
        seen_ids = torch.as_tensor(seenclass).detach().cpu().long()
        unseen_ids = torch.as_tensor(unseenclass).detach().cpu().long()
        self._validate_inputs(
            seen_ids,
            unseen_ids,
            seen_text_embeds,
            unseen_text_embeds,
            seen_sentence_embeds,
        )
        self.register_buffer("seenclass", seen_ids, persistent=False)
        self.register_buffer("unseenclass", unseen_ids, persistent=False)

        self.seen_text_embeds = nn.Parameter(
            F.normalize(seen_text_embeds.detach(), dim=1), requires_grad=False
        )
        self.unseen_text_embeds = nn.Parameter(
            F.normalize(unseen_text_embeds.detach(), dim=1), requires_grad=False
        )
        self.seen_sentence_embeds = nn.Parameter(
            F.normalize(seen_sentence_embeds.detach(), dim=-1), requires_grad=False
        )

        self.pse_outer_ratio = float(config.pse_outer_ratio)
        self.pse_module = ProgressiveSemanticSelfAttention(
            dim=self.dim_f,
            heads=int(config.pse_heads),
            dropout=float(config.pse_dropout),
            inner_ratio=float(config.pse_inner_ratio),
        )
        self.logit_scale = nn.Parameter(torch.ones([]) * np.log(1 / 0.07))

        icsa_hidden = int(config.icsa_hidden)
        self.icsa_module = nn.Sequential(
            nn.Linear(self.dim_f, icsa_hidden),
            nn.LayerNorm(icsa_hidden),
            nn.GELU(),
            nn.Linear(icsa_hidden, self.dim_f),
        )
        with torch.no_grad():
            self.icsa_module[-1].weight.zero_()
            self.icsa_module[-1].bias.zero_()
        self.icsa_ratio = float(config.icsa_ratio)
        if self.icsa_ratio <= 0:
            raise ValueError("GlobalOnlyGTPJ 要求 icsa_ratio > 0。")

    def _validate_inputs(
        self,
        seen_ids,
        unseen_ids,
        seen_text_embeds,
        unseen_text_embeds,
        seen_sentence_embeds,
    ):
        if seen_ids.dim() != 1 or unseen_ids.dim() != 1:
            raise ValueError("seenclass 和 unseenclass 必须是一维全局类别编号。")
        if seen_ids.unique().numel() != seen_ids.numel():
            raise ValueError("seenclass 含有重复类别。")
        if unseen_ids.unique().numel() != unseen_ids.numel():
            raise ValueError("unseenclass 含有重复类别。")
        if torch.isin(seen_ids, unseen_ids).any():
            raise ValueError("seenclass 和 unseenclass 不能重叠。")
        combined = torch.cat([seen_ids, unseen_ids]).sort().values
        if not torch.equal(combined, torch.arange(self.nclass, dtype=torch.long)):
            raise ValueError("seenclass 和 unseenclass 必须完整覆盖全局类别。")
        if tuple(seen_text_embeds.shape) != (seen_ids.numel(), self.dim_f):
            raise ValueError("seen_text_embeds 必须是 [C_seen, D]。")
        if tuple(unseen_text_embeds.shape) != (unseen_ids.numel(), self.dim_f):
            raise ValueError("unseen_text_embeds 必须是 [C_unseen, D]。")
        if (
            seen_sentence_embeds.dim() != 3
            or seen_sentence_embeds.size(0) != seen_ids.numel()
            or seen_sentence_embeds.size(2) != self.dim_f
        ):
            raise ValueError("seen_sentence_embeds 必须是 [C_seen, M, D]。")

    @classmethod
    def from_canonical(cls, donor):
        """从一个 canonical GTPJ donor 严格复制所有共享全局状态。"""
        if not isinstance(donor, GTPJ):
            raise TypeError("donor 必须是 canonical GTPJ。")
        # 候选模块自身的临时初始化不能挪动 canonical donor 之后的批次随机流。
        with torch.random.fork_rng(devices=[]):
            candidate = cls(
                donor.config,
                donor.seenclass,
                donor.unseenclass,
                donor.seen_text_embeds,
                donor.unseen_text_embeds,
                donor.seen_sentence_embeds,
            )
        donor_state = donor.state_dict()
        required = set(candidate.state_dict())
        missing = sorted(required - set(donor_state))
        if missing:
            raise ValueError(f"canonical donor 缺少共享全局状态：{missing}。")
        candidate.load_state_dict(
            {name: donor_state[name].detach().clone() for name in required},
            strict=True,
        )
        return candidate

    def forward(self, cls_features, is_train=False):
        if cls_features.dim() != 2:
            raise ValueError(
                "GlobalOnlyGTPJ 只接受 CLS 特征 [B, D]；"
                f"实际为 {tuple(cls_features.shape)}。"
            )
        if cls_features.size(1) != self.dim_f:
            raise ValueError(
                f"GlobalOnlyGTPJ 要求 D={self.dim_f}；实际为 D={cls_features.size(1)}。"
            )

        logit_scale = torch.clamp(self.logit_scale.exp(), max=100.0)
        all_text = self._make_all_text(cls_features.device, cls_features.dtype)
        vis_n = F.normalize(cls_features, dim=1)
        pi_x = F.normalize(self.icsa_module(cls_features), dim=-1)
        all_text_cond = all_text.unsqueeze(0).expand(cls_features.size(0), -1, -1).clone()
        seen_idx = self.seenclass.to(cls_features.device)
        all_text_cond[:, seen_idx, :] = (
            all_text[seen_idx].unsqueeze(0) + self.icsa_ratio * pi_x.unsqueeze(1)
        )
        text_n_cond = F.normalize(all_text_cond, dim=-1)
        global_logits = (vis_n.unsqueeze(1) * text_n_cond).sum(dim=-1) * logit_scale
        logits = global_logits[:, seen_idx] if is_train else global_logits
        return {
            "logits": logits,
            "final_logits": global_logits,
            "global_logits": global_logits,
            "clip_S_pp": logits,
        }

    def compute_loss(self, in_package):
        logits = in_package["logits"]
        labels = in_package["batch_label"]
        if labels.dim() > 1:
            labels = torch.argmax(labels, dim=1)
        labels = labels.to(device=logits.device, dtype=torch.long)
        seen_labels = self._global_to_seen_labels(labels).to(logits.device)
        loss_ce = F.cross_entropy(logits, seen_labels)
        loss_topo = self._topology_pearson_loss()
        loss = loss_ce + float(self.config.lambda_topo_pearson) * loss_topo
        return {"loss": loss, "loss_ce": loss_ce, "loss_topo": loss_topo}
