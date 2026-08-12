"""V5-INNOVATION-011 的独立最小句子—区域匹配模型。

这不是 V5 模型的延续。V5 母版只提供数据、评估、checkpoint 和可复现工具；
本文件重新定义模型、forward、特征交互和唯一损失。
"""

import math

import torch
import torch.nn as nn
import torch.nn.functional as F


SENTENCE_ROLES = (
    "beak",
    "head_features",
    "body_plumage",
    "wings",
    "tail",
    "legs",
    "overall_appearance",
    "unique_discriminative_features",
)
LOCAL_SENTENCE_COUNT = 6
GLOBAL_SENTENCE_INDEX = SENTENCE_ROLES.index("overall_appearance")
UNIQUE_SENTENCE_INDEX = SENTENCE_ROLES.index("unique_discriminative_features")
EXPECTED_PATCH_COUNT = 576


class GTPJ(nn.Module):
    """用 6 个局部句、1 个全局句和 1 个独特句直接分类。"""

    def __init__(
        self,
        config,
        seenclass,
        unseenclass,
        sentence_embeds,
    ):
        super().__init__()
        self.nclass = int(config.num_class)
        self.dim_f = int(config.dim_f_clip)
        self.region_temperature = float(config.region_temperature)
        if self.region_temperature <= 0:
            raise ValueError("region_temperature 必须大于 0。")

        seen_ids = torch.as_tensor(seenclass, dtype=torch.long).detach().cpu()
        unseen_ids = torch.as_tensor(unseenclass, dtype=torch.long).detach().cpu()
        self._validate_class_partition(seen_ids, unseen_ids)
        if tuple(sentence_embeds.shape) != (self.nclass, 8, self.dim_f):
            raise ValueError(
                "sentence_embeds 必须严格为 "
                f"[{self.nclass}, 8, {self.dim_f}]，实际为 {tuple(sentence_embeds.shape)}。"
            )

        self.register_buffer("seenclass", seen_ids, persistent=True)
        self.register_buffer("unseenclass", unseen_ids, persistent=True)
        self.register_buffer(
            "sentence_embeds",
            sentence_embeds.detach().float().clone(),
            persistent=True,
        )

        self.shared_projection = nn.Linear(self.dim_f, self.dim_f, bias=False)
        with torch.no_grad():
            self.shared_projection.weight.copy_(torch.eye(self.dim_f))
        self.logit_scale = nn.Parameter(torch.tensor(math.log(1.0 / 0.07)))

    def _validate_class_partition(self, seen_ids, unseen_ids):
        if seen_ids.dim() != 1 or unseen_ids.dim() != 1:
            raise ValueError("seenclass 和 unseenclass 必须是一维全局类别编号。")
        if seen_ids.unique().numel() != seen_ids.numel():
            raise ValueError("seenclass 含有重复类别。")
        if unseen_ids.unique().numel() != unseen_ids.numel():
            raise ValueError("unseenclass 含有重复类别。")
        if torch.isin(seen_ids, unseen_ids).any():
            raise ValueError("seenclass 与 unseenclass 不能重叠。")
        combined = torch.cat([seen_ids, unseen_ids]).sort().values
        expected = torch.arange(self.nclass, dtype=torch.long)
        if not torch.equal(combined, expected):
            raise ValueError("seen/unseen 必须无遗漏地覆盖全部全局类别。")

    @staticmethod
    def _validate_features(clip_features, dim_f):
        if clip_features.dim() != 3:
            raise ValueError("clip_features 必须是 [B, 577, D]。")
        if tuple(clip_features.shape[1:]) != (EXPECTED_PATCH_COUNT + 1, dim_f):
            raise ValueError(
                f"clip_features 必须是 [B, {EXPECTED_PATCH_COUNT + 1}, {dim_f}]，"
                f"实际为 {tuple(clip_features.shape)}。"
            )

    def _project_and_normalize(self, value):
        return F.normalize(self.shared_projection(value.float()), dim=-1)

    def _sentence_region_score(self, patches, sentence_text):
        similarity = torch.einsum("bnd,cd->bcn", patches, sentence_text)
        weights = F.softmax(similarity / self.region_temperature, dim=-1)
        return (weights * similarity).sum(dim=-1)

    def _all_role_logits(self, clip_features):
        self._validate_features(clip_features, self.dim_f)
        global_image = self._project_and_normalize(clip_features[:, 0])
        patches = self._project_and_normalize(clip_features[:, 1:])
        text = self._project_and_normalize(self.sentence_embeds)

        local_logits = torch.zeros(
            clip_features.size(0),
            self.nclass,
            device=clip_features.device,
            dtype=patches.dtype,
        )
        for sentence_index in range(LOCAL_SENTENCE_COUNT):
            local_logits = local_logits + self._sentence_region_score(
                patches, text[:, sentence_index]
            )
        local_logits = local_logits / LOCAL_SENTENCE_COUNT

        unique_logits = self._sentence_region_score(
            patches, text[:, UNIQUE_SENTENCE_INDEX]
        )
        global_logits = global_image @ text[:, GLOBAL_SENTENCE_INDEX].T
        return local_logits, unique_logits, global_logits

    def forward(self, clip_features, is_train=False):
        local_all, unique_all, global_all = self._all_role_logits(clip_features)
        final_all = (local_all + unique_all + global_all) / 3.0
        final_all = self.logit_scale.exp().clamp(max=100.0) * final_all

        class_ids = self.seenclass if is_train else torch.arange(
            self.nclass, device=final_all.device
        )
        class_ids = class_ids.to(final_all.device)
        logits = final_all.index_select(1, class_ids)
        local_logits = local_all.index_select(1, class_ids)
        unique_logits = unique_all.index_select(1, class_ids)
        global_logits = global_all.index_select(1, class_ids)
        return {
            "logits": logits,
            "final_logits": logits,
            "clip_S_pp": logits,
            "local_logits": local_logits,
            "unique_logits": unique_logits,
            "global_logits": global_logits,
            "all_final_logits": final_all,
        }

    def _global_to_seen_labels(self, labels):
        labels = labels.to(device=self.seenclass.device, dtype=torch.long)
        mapping = torch.full(
            (self.nclass,), -1, device=labels.device, dtype=torch.long
        )
        mapping[self.seenclass.to(labels.device)] = torch.arange(
            self.seenclass.numel(), device=labels.device
        )
        seen_labels = mapping[labels]
        if (seen_labels < 0).any():
            raise ValueError("训练标签包含 unseen 类别。")
        return seen_labels

    def compute_loss(self, in_package):
        if "logits" not in in_package or "batch_label" not in in_package:
            raise ValueError("compute_loss 需要 logits 和 batch_label。")
        seen_labels = self._global_to_seen_labels(in_package["batch_label"])
        seen_labels = seen_labels.to(in_package["logits"].device)
        loss_ce = F.cross_entropy(in_package["logits"], seen_labels)
        return {"loss": loss_ce, "loss_ce": loss_ce}
