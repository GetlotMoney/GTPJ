# IDEA-0006: 局部证据校准与全局候选纠错

```text
idea_id: IDEA-0006
title: 局部证据校准与全局候选纠错
status: candidate
source_type: observation
source_ref: V5-CONFIRM-003@8dd1b5ac10fdacc19aecfb0307c53077dd46bd66
source_status: verified
global_score: 76.0
idea_dir: idea_tree/ideas/IDEA-0006_local_evidence_rescue/
```

## 来源

来自 `V5-CONFIRM-003@8dd1b5a` 的实测观察：局部分支单独 `H≈1.53`，
但仍能在约 `0.65%` 的样本上纠正全局分支，说明问题不是“完全没有局部信息”，
而是局部证据太弱、太噪，且缺少直接监督。

## 基于什么

- `v5`

## 目标组件

FGVD、BVSA 局部分数、局部训练损失和最终候选类决策。

## 假设

先删去无独立证据的几何编码，再用直接分类、全局混淆难负类或真实裁剪 teacher
训练局部分支，最后只在全局 top-k 候选内使用有界局部残差，可以提高 rescue、
同时控制 harm。

## 实现范围

- 不改 CLIP 特征、CUB 划分、50 epoch 日程和 U/S/H/ZS 口径。
- 训练方案一次只增加一种局部监督；所有初筛固定 seed 5。
- top-k 重排不读取真实标签，标签只用于结束后的指标统计。

## 版本适配记录

| 版本 | 优先级 | 适用性 | 理由 |
|---|---:|---|---|
| `v5` | 86.0 | needs_adaptation | 全局分支已强，适合把局部改造成稀疏纠错证据；需先证明局部监督有效。 |

机器可读版本适配记录写在 `idea_tree/idea_tree.json` 的 `version_scores` 字段。
新增 `v2`、`v3` 时必须重新评估，不能复制 `v5` 适配记录。

## 迁移说明

当前只验证 V5，不自动迁移到其他框架；迁移时必须重新核对局部分支输出和类别轴。

## 风险

- 直接监督可能只提高 local-alone，却破坏最终 U/S 平衡。
- 裁剪 CLS 缓存只有两视角，不能代表所有局部尺度。
- top-k 重排的固定上限仍可能在全局本来正确时造成 harm。

## 阻塞点

方案 5 依赖方案 2～4 的 checkpoint，因此必须最后运行。

## 决策规则

先比较 seed 5 的 H、local-alone、rescue 和 harm；只有改善方向明确的方案再补
seed 17/29。若局部能力和最终 H 都没有提升，停止局部路线并采用 global-only。
