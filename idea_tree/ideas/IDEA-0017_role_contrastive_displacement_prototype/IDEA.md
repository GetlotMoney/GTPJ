# IDEA-0017: 角色对比位移原型（RCDP）

```text
idea_id: IDEA-0017
title: 角色对比位移原型（RCDP）
status: rejected
source_type: user
source_ref: owner:2026-08-16:干净双模块框架的第一模块
source_status: local_heuristic
global_score: 40.0
idea_dir: idea_tree/ideas/IDEA-0017_role_contrastive_displacement_prototype/
```

## 来源

Owner 要求建立至少两个原创候选模块组成的干净框架；RCDP 是第一个模块。它吸收旧 PSE“文本原型可训练”的有效经验，但删除句间 self-attention、双专家和 seen/unseen 两套公式。

## 基于什么

- `v5`

## 目标组件

单一、seen/unseen 对称的类别文本原型生成器。

## 假设

同一语义角色跨类别的混淆差值，能够比类内句子 attention 或类内中心化残差更直接地提供判别方向。

## 实现范围

- 八句话固定等权，不学习句子 softmax 权重；
- 每个角色寻找最相似的非自身类别，形成有符号文本差值；
- 用零初始化的角色低秩映射和一个有界全局 gate 修改原始均值原型；
- 100/50 类不重叠验证只选择 epoch，随后在 150 个正式 seen 类上从零重训；
- checkpoint 冻结后 official test 只评估一次，不使用 gamma。

## 版本适配记录

| 版本 | 优先级 | 适用性 | 理由 |
|---|---:|---|---|
| `v5` | 40.0 | needs_adaptation | RUN-001 H=66.336303，相对同次 Mean8 下降 0.306272，已拒绝。 |

机器可读版本适配记录写在 `idea_tree/idea_tree.json` 的 `version_scores` 字段。
新增 `v2`、`v3` 时必须重新评估，不能复制 `v5` 适配记录。

## 迁移说明

RCDP 单模块未通过无 test 选参协议，不进入后续框架候选，也不在其上叠加 RPV。

## 风险

跨类别 rival 差值可能并不适合 CLIP 联合空间，低秩变换也可能只提高 seen。失败时直接停止，不叠加第二模块掩盖问题。

## 阻塞点

正式结果 `stop_no_gain`：S 上升但 U 下降更多，H 相对 Mean8 下降 0.306272。

## 决策规则

预先冻结门为相对同次纯 CLIP 八句基线 `delta_H >= 0.50`；实际 `delta_H=-0.306272`，因此停止 RCDP 路线。
