# IDEA-0005：置信度条件局部互补门控

```text
idea_id: IDEA-0005
title: 置信度条件局部互补门控
status: selected
source_type: observation
source_ref: owner-observation:2026-08-09:局部分支整体增益很小，需要检验它是否只在全局分支低置信度样本上提供互补；owner 在本任务中明确要求执行全部计划实验
source_status: local_heuristic
global_score: 70.0
idea_dir: idea_tree/ideas/IDEA-0005_confidence_conditioned_local_gate/
base_version: v5
linked_experiment: V5-INNOVATION-003
```

## 来源

这个想法来自本次局部分支互补性问题：整体消融增益很小，不代表局部分支对每个样本都没有用；它也可能只在全局分支犹豫的困难样本上提供帮助。

Owner 已在 2026-08-09 的当前任务中要求把完整模型、纯全局模型和这个门控候选全部跑完。这里把它登记为可复核的本地观察，不声称来自任何论文。

## 基于什么

- 正式框架：`FRAMEWORK-V5`。
- 只读母版：`MODEL-V5-TEMPLATE-V1` / `model/v5-template-v1`。
- 母版 commit：`2f5fa5e631ef82658d4bac587cdfd17f3534cb35`。
- 母版已经同时输出 `global_logits` 和 `local_logits`，因此可以只改最后融合，不碰类别轴和评估口径。

## 目标组件

V5 全局与局部 logits 的最终融合位置。

## 假设

如果局部分支的价值集中在全局分支低置信度样本上，那么局部权重应随全局分类间隔增大而单调减小：全局越犹豫，越允许局部分支参与；全局越确定，局部分支权重不会变大。

如果三次同配置运行没有改善，或者 gate 几乎恒定、出现非有限数或放大噪声，这个假设就不成立。

## 实现范围

`V5-INNOVATION-003` 只在独立实验分支加入一个小门控：

- 使用 detached 的 global margin，避免通过置信度统计反向改变全局分支；
- `gate = sigmoid(bias - softplus(slope_raw) * margin)`，保证 margin 越大，gate 不会越大；
- 固定 `beta=0.05`，不根据测试集成绩再调；
- 保留原有辅助损失输入、类别顺序、seen/unseen 划分、标签映射和 `U/S/H/ZS` 评估口径；
- 不修改母版，不在确认前创建新框架或 Tag。

## 预期作用

| 指标 | 只允许预先提出的判断 |
|---|---|
| U | 低全局置信度的未见类样本可能得到更多局部信息，必须由正式运行验证。 |
| S | 高全局置信度样本会压低局部干扰，目标是避免明显损伤已见类表现。 |
| H | 只比较三次同配置正式运行和同口径基线，不预写提升结论。 |

## v5 适配

| 版本 | 优先级 | 适用性 | 阶段 | 理由 | 阻塞点 |
|---|---:|---|---|---|---|
| `v5` | 78.0 | direct | selected | V5 已提供 global/local logits，这个最小门控直接回答当前局部分支互补性问题。 | 无 |

## 风险

- global margin 可能不是可靠的置信度。
- gate 可能塌缩、近似常数，或者放大局部分支噪声。
- 相同 seed 的独立进程仍可能受 GPU 非确定性影响，因此三次运行要分别保留日志和结果。

## 决策规则

- 当前只登记 `pre_run` 计划，没有任何实验结果。
- 三次计划运行必须全部使用固定参数和 seed=5，不用测试集成绩改 gate 公式或 `beta`。
- 只有完整结果和质量检查都完成后，才能判断保留、修改或放弃；单次高分不能直接支持论文结论或 promotion。
