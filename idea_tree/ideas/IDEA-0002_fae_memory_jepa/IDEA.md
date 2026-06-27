# IDEA-0002: FAE-memory JEPA auxiliary loss

```text
idea_id: IDEA-0002
title: FAE-memory JEPA auxiliary loss
status: selected
source_type: user
source_ref: owner:2026-06-27:move AG-JEPA visual context after FAE while keeping FAE-pre patch target
source_status: local_heuristic
global_score: 72.0
idea_dir: idea_tree/ideas/IDEA-0002_fae_memory_jepa/
```

## 来源

本 idea 来自 owner 对当前 AG-JEPA 梯度流的代码审查讨论。当前实现中 AG-JEPA 使用
`patches -> cross_tf.embed_cv -> context/target`，没有经过 FAE 和 CrossModal decoder。
因此它能优化 `embed_cv`、`embed_text`、seen 文本 adapter 路径和 `jepa_predictor`，但不能直接
把辅助损失施加到 FAE visual memory。

本地长版材料：

```text
D:/backup/Documents/Myself/GTPJ_Research/ideas/IDEA-0002_fae_memory_jepa/idea_full.md
```

## 基于什么

- `v2`

## 目标组件

- `model/MyModel.py`
- `CrossModalTransformer.forward`
- `GTPJ._ag_jepa_loss`
- `config/GTPJ_cub_gzsl.yaml` 或 trial-local config

## 假设

将 AG-JEPA 的视觉 context 从 FAE 前的 `patch_z` 平均值改为 FAE 后的 `memory` 平均值，
同时保持预测 target 为 FAE 前 `patch_z` 的 masked 部分并 `detach`。这样 JEPA 仍然预测较干净的
视觉投影目标，但正向梯度可以穿过 FAE，约束实际 local-score 路径使用的视觉 memory。

## 实现范围

- 新增或切换 JEPA mode，例如 `jepa_context_mode: embed` / `fae_memory`。
- `fae_memory` 模式下，mask 选择和 `lastvit_select_k` 后的 patch 集合保持一致。
- `target = mean(masked patch_z).detach()`。
- `context = mean(kept memory)`。
- 文本端继续使用 `all_text[labels] -> cross_tf.embed_text -> text_z`，其中 seen 类文本仍经过
  CLIP-A-self adapter。
- 不改变 logits、eval、label mapping、seen/unseen split、class order 和 metric calculation。

## 版本适配记录

| 版本 | 优先级 | 适用性 | 理由 |
|---|---:|---|---|
| `v2` | 72.0 | needs_adaptation | 当前 v2 已包含 CLIP-A-self 和 AG-JEPA；本 idea 不改变文本 adapter 或 eval 口径，只把 JEPA visual context 接到 FAE memory，以验证辅助损失能否真正约束主 local-score 视觉路径。 |

机器可读版本适配记录写在 `idea_tree/idea_tree.json` 的 `version_scores` 字段。
新增 `v2`、`v3` 时必须重新评估，不能复制 `v2` 适配记录。

## 迁移说明

这个 idea 依赖当前 `CrossModalTransformer` 中的 `embed_cv -> FAE -> decoder_s2v/decoder_v2s`
结构。如果未来版本重写 FAE 或 patch selection，需要重新检查 `patch_z`、`memory`、mask 和文本
condition 的对应关系。

## 风险

- `target` 和 `context` 位于不同深度，可能造成优化目标不稳定。
- `lastvit_select_k=32` 时，如果 mask 基于 576 个原 patch 而 context 基于 32 个 selected patch，
  会产生语义错位；实现必须统一到同一 patch 集。
- 负样本损失若反传到 visual context，可能扰乱 FAE；第一版应保持 negative context detach。
- 结果即便提升，也只能先作为 `valid_single_run` 或 trial evidence，不能直接作为 confirmed baseline。

## 阻塞点

无当前已知阻塞。Review 1 必须确认 shape、switch-off path 和 gradient probe 方案。

## 决策规则

- 如果梯度检查不能证明 `cross_tf.fae.*` 接收到 JEPA positive loss 梯度，标记为 `blocked`。
- 如果 switch-off path 不能恢复当前行为，标记为 `blocked`。
- 如果训练结果下降或质量门发现接口污染，标记为 `revise` 或 `reject`。
