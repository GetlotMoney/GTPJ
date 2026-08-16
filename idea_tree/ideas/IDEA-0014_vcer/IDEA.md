# IDEA-0014: 可见反事实证据路由（VCER）

```text
idea_id: IDEA-0014
title: 可见反事实证据路由（VCER）
status: candidate
source_type: user
source_ref: owner:2026-08-16:VCER_6local_unique_router_global_foreground
source_status: local_heuristic
global_score: 80.0
idea_dir: idea_tree/ideas/IDEA-0014_vcer/
```

## 来源

Owner 于 2026-08-16 提出的本项目原创框架：把 8 句严格解释为
`6 个局部描述 + 1 个全局描述 + 1 个独特描述`，在冻结 PSE-X2 后加入
可见反事实证据路由。当前来源状态是 `local_heuristic`，不是论文复现。

## 基于什么

- `v5`
- `PSE-X2` 冻结全局文本原型与余弦分类底分

## 目标组件

冻结 PSE-X2 之后的候选—混淆类局部视觉重排。独特描述决定六个局部角色中
哪些差异最有判别力，全局描述估计 patch 是否属于主体，局部描述提供同一 patch
上的候选—混淆类反事实边际。

## 假设

若三种描述各司其职，VCER 应在不编码 seen/unseen 身份的前提下减少 seen 类
对 unseen 图像的错误吸引；同时，打乱角色或交换 unique 描述应显著破坏证据修正，
从而证明模块没有退化成共享视觉 Adapter。

## 实现范围

- 输入：冻结的 8 句证据 `[C, 8, D]`、X2 原型 `[C, D]`、图像 CLS `[B, D]`、patch `[B, P, D]`。
- 新参数：仅一个所有类别与角色共享的低秩残差投影；输出层零初始化。
- 训练：seen 图像分类损失、unique-swap 因果间隔和小权重语义保持损失。
- 边界：不引入类别专属参数、split 身份、gamma 或 official-test 选择；关闭 VCER 时逐元素退回冻结 X2 logits。

## 版本适配记录

| 版本 | 优先级 | 适用性 | 理由 |
|---|---:|---|---|
| `v5` | 80.0 | needs_adaptation | X2 有强全局原型但没有角色依赖的视觉证据；VCER 只增加共享低秩证据空间。 |

机器可读版本适配记录写在 `idea_tree/idea_tree.json` 的 `version_scores` 字段。
新增 `v2`、`v3` 时必须重新评估，不能复制 `v5` 适配记录。

## 迁移说明

后续框架只要能提供同维度的 8 句证据、冻结类别原型、CLS 和 patch 特征即可迁移；
不得复制 v5 的类别顺序、split 或 checkpoint 选择逻辑。

## 风险

- patch 证据可能仍偏向背景，使 U 下降。
- unique 路由可能退化成近似共享角色权重。
- 当前仅完成模块与合成张量测试，尚无正式训练效果证据。

## 阻塞点

模块已经进入正式 Runner 接入与 pre-run review；训练前仍须完成同一最终代码的两轮审核。

## 决策规则

- Owner 于 2026-08-16 明确取消 pseudo-GZSL 前置门；直接用 150 seen 正式训练并读取 official test。
- checkpoint 固定为 epoch 50，不使用 official 指标选择 epoch；不调 gamma、不叠加失败模块。
- 同次报告 X2、VCER、role-shuffle 与 unique-swap；结果标记为 `official-test-guided development`。
