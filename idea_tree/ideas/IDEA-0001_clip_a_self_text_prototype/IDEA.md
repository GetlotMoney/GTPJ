# IDEA-0001: CLIP-A-self text prototype adapter

```text
idea_id: IDEA-0001
title: CLIP-A-self text prototype adapter
status: selected
source_type: paper
source_ref: paper:Enhancing CLIP with GPT-4; code:https://github.com/mayug/VDT-Adapter
source_status: verified
global_score: 82.0
idea_dir: idea_tree/ideas/IDEA-0001_clip_a_self_text_prototype/
```

## 来源

- 论文：`C:/Users/Administrator/Desktop/CV论文/2023/Enhancing CLIP with GPT-4：Harnessing Visual Descriptions as Prompts.pdf`
- 官方代码：`https://github.com/mayug/VDT-Adapter`

来源复核：

- PDF 摘要说明 code、prompts 和 auxiliary text dataset 可在 `github.com/mayug/VDT-Adapter` 获得。
- 官方代码包含 `SelfAttnAdapter`，并在 `self_attn` 分支中对每个类别的 GPT/VDT 句子嵌入做 self-attention 后再 `mean(dim=1)` 得到类别文本 prototype。

## 基于什么

- `v1`
- 当前 v1 已有 GPT/VDT 句子平均文本特征和 seen-class MLP text adapter。

## 目标组件

`model/MyModel.py` 中的 seen-class text prototype adapter。

## 假设

把 v1 的 seen-class MLP text adapter 替换为句子级 CLIP-A-self adapter，可以从每类 GPT/VDT 描述句集合中学习更有用的视觉描述组合，在不改变 GZSL 接口语义的前提下提升 H 或 ZS。

## 实现范围

TRIAL-001 只允许修改文本 prototype 构造路径：

- 保留 GPT/VDT sentence-level embeddings，形状为 `[C（类别数量）, M（每类句子数量）, D（文本特征维度）]`。
- seen 类使用 CLIP-A-self 处理句子集合。
- 保留外层 prototype residual：

```text
base = sentence_embeds.mean(dim=1)
attn = clip_a_self(sentence_embeds).mean(dim=1)
out = (1 - ratio) * base + ratio * attn
out = normalize(out)
```

- TRIAL-001 默认 `clip_a_self_apply_unseen: false`，unseen 类保持原始句子均值。
- 不新增 loss，不改变 CE seen-only，不改变 eval。

## 版本适配记录

| 版本 | 优先级 | 适用性 | 阶段 | 理由 |
|---|---:|---|---|---|
| `v1` | 78.0 | needs_adaptation | selected | v1 已经有 GPT/VDT 文本和 seen prototype adapter，CLIP-A-self 可作为最小替换 trial；需要补 sentence-level 输入和 switch-off 等价检查。 |

机器可读版本适配记录写在 `idea_tree/idea_tree.json` 的 `version_scores` 字段。
新增 `v2`、`v3` 时必须重新评估，不能复制 `v1` 适配记录。

## 接口约束

- class order 不变。
- seen/unseen split 不变。
- label mapping 不变。
- 训练仍只对 seen logits 做 CE。
- eval 仍输出 200 类 logits 做 GZSL/ZS。
- logits shape 保持 `[B（图片/样本数量）, C（类别数量）]`。
- switch-off path 必须等价于 v1 baseline MLP adapter。

## L2SP 边界

L2SP 不属于本 idea 的 TRIAL-001 主变量。

当前定位：

```text
CLIP-A-self = 正式 idea
L2SP = prototype drift 风险下的 follow-up ablation / anchoring question
```

如果 TRIAL-001 出现 seen 提升但 unseen 或 H 明显下滑，后续可以在同一 IDEA-0001 下开 `TRIAL-002_clip_a_self_l2sp_anchor` 或普通 ablation。只有当 anchoring 本身被证明是可复用新机制时，才考虑升级为独立 idea。

## 迁移说明

未来如果产生 `v2` 或更高版本，必须重新检查：

- 文本 prototype 的 owner 是否仍是 `model/MyModel.py`。
- 是否仍使用 GPT/VDT sentence-level 文本源。
- seen/unseen split、class order 和 eval 语义是否与 v1 一致。
- 是否已经存在新的文本 adapter 或 prototype regularizer，避免重复。

## 风险

- seen-only CE 可能把 CLIP-A-self adapter 拉向 seen 类，导致 unseen prototype 泛化变差。
- 如果直接让 unseen 也过可训练 adapter，可能在语义空间中产生不可控漂移。
- 如果把 sentence-level cache 与 averaged cache 混用，可能产生不可复现的文本输入。
- 如果 switch-off path 不等价，trial 结果不能和 v1 baseline 比较。

## 阻塞点

无。来源已复核，v1 接口可做最小适配。

## 决策规则

- `promote`：H 提升且 U/S/ZS 无不可接受退化，artifact、interface、quality evidence 完整。
- `revise`：有局部提升但存在 prototype drift、unseen 退化或证据不完整。
- `reject`：H 和 ZS 均无收益，或接口污染导致无法比较。

## Trial 记录

| Trial | U | S | H | ZS | Best epoch | Decision |
|---|---:|---:|---:|---:|---:|---|
| `TRIAL-001_clip_a_self_residual_seenonly` | 72.32 | 75.19 | 73.72 | 81.13 | 30 | revise |

结论：TRIAL-001 没有超过权威 v1 baseline `H=73.93`，不进入 promotion。下一步如果继续该 idea，优先分析 prototype drift，再考虑更小 `clip_a_self_outer_ratio` 或 L2SP anchoring follow-up。
