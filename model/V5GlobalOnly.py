"""V5-ABLATION-001 的全局分支模型。

这个实验版本只保留 PSE、ICSA、全局余弦分类、CE 和拓扑损失。
输入接口仍为 ``[B, 577, D]``，但只读取第 0 个 CLS 特征。
"""

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


class ProgressiveSemanticSelfAttention(nn.Module):
    """PSE：在同一类别的多句文本描述之间做自注意力。"""

    def __init__(self, dim, heads=1, dropout=0.5, inner_ratio=0.5):
        super().__init__()
        self.inner_ratio = float(inner_ratio)
        self.attn = nn.MultiheadAttention(
            embed_dim=dim,
            num_heads=int(heads),
            dropout=float(dropout),
            batch_first=True,
        )
        self.proj = nn.Linear(dim, dim)
        self.dropout = nn.Dropout(float(dropout))
        self.layer_norm = nn.LayerNorm(dim)

    def forward(self, x):
        attn_out, _ = self.attn(x, x, x, need_weights=False)
        attn_out = self.dropout(self.proj(attn_out))
        mixed = self.inner_ratio * attn_out + (1.0 - self.inner_ratio) * x
        return self.layer_norm(2.0 * mixed)


class GTPJ(nn.Module):
    """V5 的全局路径消融版本：PSE + ICSA + 全局余弦分类。"""

    def __init__(
        self,
        config,
        seenclass,
        unseenclass,
        seen_text_embeds,
        unseen_text_embeds,
        seen_sentence_embeds=None,
    ):
        super().__init__()
        self.config = config
        self.nclass = int(config.num_class)
        self.dim_f = int(config.dim_f_clip)

        seen_ids = torch.as_tensor(seenclass, dtype=torch.long)
        unseen_ids = torch.as_tensor(unseenclass, dtype=torch.long)
        if seen_ids.dim() != 1 or unseen_ids.dim() != 1:
            raise ValueError("seenclass 和 unseenclass 必须是一维全局类别编号。")
        if seen_ids.unique().numel() != seen_ids.numel():
            raise ValueError("seenclass contains duplicate global ids（含重复类别编号）。")
        if unseen_ids.unique().numel() != unseen_ids.numel():
            raise ValueError("unseenclass contains duplicate global ids（含重复类别编号）。")
        if torch.isin(seen_ids, unseen_ids).any():
            raise ValueError("seenclass and unseenclass must not overlap（不能重叠）。")
        combined_ids = torch.cat([seen_ids, unseen_ids]).sort().values
        expected_ids = torch.arange(self.nclass, dtype=torch.long)
        if not torch.equal(combined_ids, expected_ids):
            raise ValueError(
                "seenclass and unseenclass must cover every global class exactly once"
                "（必须无遗漏覆盖全部类别）。"
            )
        if tuple(seen_text_embeds.shape) != (seen_ids.numel(), self.dim_f):
            raise ValueError("seen_text_embeds 必须为 [C_seen, D]。")
        if tuple(unseen_text_embeds.shape) != (unseen_ids.numel(), self.dim_f):
            raise ValueError("unseen_text_embeds 必须为 [C_unseen, D]。")

        self.register_buffer("seenclass", seen_ids, persistent=False)
        self.register_buffer("unseenclass", unseen_ids, persistent=False)
        self.seen_text_embeds = nn.Parameter(
            F.normalize(seen_text_embeds, dim=1), requires_grad=False
        )
        self.unseen_text_embeds = nn.Parameter(
            F.normalize(unseen_text_embeds, dim=1), requires_grad=False
        )

        if seen_sentence_embeds is None:
            raise ValueError("V5-ABLATION-001 需要 seen_sentence_embeds。")
        if (
            seen_sentence_embeds.dim() != 3
            or seen_sentence_embeds.size(0) != seen_ids.numel()
            or seen_sentence_embeds.size(-1) != self.dim_f
        ):
            raise ValueError("seen_sentence_embeds 必须为 [C_seen, M, D]。")
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
            raise ValueError("icsa_ratio 必须大于 0。")

        self.logit_scale = nn.Parameter(torch.ones([]) * np.log(1 / 0.07))

    def get_adapted_seen_text(self):
        sentence_embeds = self.seen_sentence_embeds
        base = sentence_embeds.mean(dim=1)
        attended = self.pse_module(sentence_embeds).mean(dim=1)
        adapted = (
            self.pse_outer_ratio * attended
            + (1.0 - self.pse_outer_ratio) * base
        )
        return F.normalize(adapted, dim=1)

    def get_adapted_unseen_text(self):
        return self.unseen_text_embeds

    def _make_all_text(self, device, dtype):
        seen_text = self.get_adapted_seen_text().to(device=device, dtype=dtype)
        unseen_text = self.get_adapted_unseen_text().to(device=device, dtype=dtype)
        all_text = torch.zeros(self.nclass, self.dim_f, device=device, dtype=dtype)
        all_text[self.seenclass.to(device)] = seen_text
        all_text[self.unseenclass.to(device)] = unseen_text
        return all_text

    def _topology_pearson_loss(self, enhanced_text=None):
        if enhanced_text is None:
            adapted_seen = self.get_adapted_seen_text()
            device = adapted_seen.device
            dtype = adapted_seen.dtype
        else:
            device = enhanced_text.device
            dtype = enhanced_text.dtype

        base_text = torch.zeros(self.nclass, self.dim_f, device=device, dtype=dtype)
        seen_idx = self.seenclass.to(device)
        unseen_idx = self.unseenclass.to(device)
        base_text[seen_idx] = self.seen_text_embeds.to(device=device, dtype=dtype)
        base_text[unseen_idx] = self.unseen_text_embeds.to(device=device, dtype=dtype)

        if enhanced_text is None:
            enhanced_text = torch.zeros_like(base_text)
            enhanced_text[seen_idx] = adapted_seen.to(device=device, dtype=dtype)
            enhanced_text[unseen_idx] = base_text[unseen_idx]

        base_text = F.normalize(base_text.float(), dim=-1)
        enhanced_text = F.normalize(enhanced_text.float(), dim=-1)
        base_sim = base_text @ base_text.T
        if enhanced_text.dim() == 2:
            enhanced_sim = enhanced_text @ enhanced_text.T
        else:
            enhanced_sim = torch.matmul(
                enhanced_text, enhanced_text.transpose(-1, -2)
            )

        off_diag = ~torch.eye(self.nclass, dtype=torch.bool, device=device)
        base_vec = base_sim.detach()[off_diag]
        if enhanced_sim.dim() == 2:
            enhanced_vec = enhanced_sim[off_diag].unsqueeze(0)
        else:
            enhanced_vec = enhanced_sim[:, off_diag]
        base_vec = base_vec.unsqueeze(0).expand_as(enhanced_vec)

        enhanced_centered = enhanced_vec - enhanced_vec.mean(dim=1, keepdim=True)
        base_centered = base_vec - base_vec.mean(dim=1, keepdim=True)
        numerator = (enhanced_centered * base_centered).sum(dim=1)
        denominator = (
            torch.sqrt((enhanced_centered ** 2).sum(dim=1) + 1e-8)
            * torch.sqrt((base_centered ** 2).sum(dim=1) + 1e-8)
        )
        return (1.0 - numerator / denominator).mean()

    def forward(self, clip_features, is_train=False):
        if clip_features.dim() != 3 or clip_features.size(1) != 577:
            raise ValueError(
                "V5-ABLATION-001 要求 clip_features 为 [B, 577, D]；"
                f"实际为 {tuple(clip_features.shape)}。"
            )
        if clip_features.size(2) != self.dim_f:
            raise ValueError(
                f"V5-ABLATION-001 要求 D={self.dim_f}；"
                f"实际 D={clip_features.size(2)}。"
            )

        cls_token = clip_features[:, 0, :]
        all_text = self._make_all_text(cls_token.device, cls_token.dtype)
        image_norm = F.normalize(cls_token, dim=1)
        image_condition = F.normalize(self.icsa_module(cls_token), dim=-1)
        all_text_cond = all_text.unsqueeze(0).expand(cls_token.size(0), -1, -1).clone()
        seen_idx = self.seenclass.to(cls_token.device)
        all_text_cond[:, seen_idx, :] = (
            all_text[seen_idx].unsqueeze(0)
            + self.icsa_ratio * image_condition.unsqueeze(1)
        )
        text_norm = F.normalize(all_text_cond, dim=-1)
        logit_scale = torch.clamp(self.logit_scale.exp(), max=100.0)
        global_logits = (
            image_norm.unsqueeze(1) * text_norm
        ).sum(dim=-1) * logit_scale

        if is_train:
            logits = global_logits[:, seen_idx]
        else:
            logits = global_logits
        return {
            "logits": logits,
            "final_logits": global_logits,
            "global_logits": global_logits,
            "clip_S_pp": logits,
            "all_text_cond": all_text_cond,
        }

    def _global_to_seen_labels(self, labels):
        labels = labels.to(device=self.seenclass.device, dtype=torch.long)
        label_map = torch.full(
            (self.nclass,), -1, device=self.seenclass.device, dtype=torch.long
        )
        label_map[self.seenclass] = torch.arange(
            self.seenclass.numel(), device=self.seenclass.device
        )
        seen_labels = label_map[labels]
        if (seen_labels < 0).any():
            raise ValueError(
                "Training labels must be global ids from seen classes（seen 类全局编号）。"
            )
        return seen_labels

    def compute_loss(self, in_package):
        logits = in_package["logits"]
        labels = in_package["batch_label"]
        if labels.dim() > 1:
            labels = torch.argmax(labels, dim=1)
        labels = labels.to(device=logits.device, dtype=torch.long)
        seen_labels = self._global_to_seen_labels(labels).to(logits.device)

        loss_ce = F.cross_entropy(logits, seen_labels)
        loss_topo = torch.tensor(0.0, device=logits.device)
        topology_weight = float(self.config.lambda_topo_pearson)
        if topology_weight > 0:
            loss_topo = self._topology_pearson_loss()
        return {
            "loss": loss_ce + topology_weight * loss_topo,
            "loss_ce": loss_ce,
            "loss_topo": loss_topo,
        }
