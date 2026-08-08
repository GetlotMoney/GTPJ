# IDEA-0004：尺度一致的局部融合

```text
idea_id: IDEA-0004
title: Scale-Consistent Local Fusion
status: rejected
source_type: observation
source_ref: model/v5-template-v1:model/MyModel.py score-scale audit
source_status: local_heuristic
global_score: 0
idea_dir: idea_tree/ideas/IDEA-0004_scale_consistent_fusion/
base_version: v5
```

## 先说人话

V5 的全局分数和局部分数都来自余弦相似度，但全局分数额外乘了 CLIP 的 `logit_scale`，局部分数没有。随后旧代码直接把二者相加，局部项可能天然显得很小。

这个 idea 只检验一件事：让局部分数先乘同一个温度尺度，再用固定的 `0.05` 融合。公式是：

```text
global_logits + 0.05 * logit_scale * local_logits
```

这里没有新增局部特征提取模块，也不把继承来的 PSE、ICSA、BVSA、FGVD 或 SGMP 说成本实验首创。

实验已经完成并否决当前公式：三组同 seed 配对 H 全部下降，平均 `ΔH=-3.0288`，因此没有启动 seed 17/29。

## 来源与现有证据

- 冻结代码：`model/v5-template-v1:model/MyModel.py`。全局分数使用 `clamp(exp(logit_scale), max=100)`，局部分数没有同尺度处理，旧融合为 `global_logits + 0.2 * local_logits`。
- 已完成消融：`main@4f29e99bb1a940afa66bb66f8150c379c2d0af7f:experiments/v5/ablation/ABLATION-001_local_branch_effect/result.md`。三个同 seed 的局部分支 H 差值为 `+0.25/-0.09/+0.09`，均值仅 `+0.08`。

这两条证据只能提出“量级不一致可能压低局部作用”的假设，不能预先证明新公式会提升。

## 基于什么

- `MODEL-V5-TEMPLATE-V1` 的全局余弦分数。
- V5 已有的 `BVSA local_score`。
- CLIP 已有且可学习的 `logit_scale`。

## 假设

如果局部分支的微小消融增益主要来自全局与局部分数量级不一致，那么尺度一致融合应在同 seed 配对实验中稳定提高 H。反过来，如果预先写死的门槛没有通过，就把这条路线判为当前论文主线失败，不追加系数搜索。

## 实现范围

- 新增 `fusion_mode` 与 `fusion_beta` 两个实验配置。
- `scale_consistent` 固定执行 `global_logits + 0.05 * logit_scale * local_logits`。
- `legacy` 原样执行 `global_logits + 0.2 * local_logits`。
- 不改数据划分、类别顺序、标签映射、损失、优化器、训练轮数和评估口径。

## 版本适配记录

| 版本 | 分数 | 适用性 | 阶段 | 理由 |
|---|---:|---|---|---|
| `v5` | 0 | direct | rejected | V5-INNOVATION-002 的三组配对 H 全部下降，固定 `beta=0.05` 的直接尺度放大不再作为 V5 论文主线。 |

分数保持为 `0`，因为现有证据只支持提出问题，尚不支持对收益大小打分。

## 风险

- 局部分数里的噪声也会被放大。
- `logit_scale` 会随训练变化，可能造成训练不稳定。
- 同一 seed 的三次重复只检查运行重复性，不能代替跨 seed 稳定性。
- 若看完结果再改 `0.05`，就会变成测试集调参，因此本实验不允许这样做。

## 兼容性与回退

`fusion_mode=legacy` 保持旧公式；旧配置没有新字段时也默认 legacy。回退只需关闭 `scale_consistent`，不删除代码、配置或失败记录。

## 实验结果

- legacy 平均 U/S/H/ZS：`72.3776/75.9713/74.1299/81.2702`。
- scale-consistent 平均 U/S/H/ZS：`65.2764/78.0735/71.1010/80.8777`。
- 三组 H 差值：`-3.1909/-2.9176/-2.9780`。
- 结论：S 提高，但 U 大幅下降，H 平均下降 `3.0288`；当前公式被拒绝。

这个失败不等于“局部分支没有信息”，只说明缺少共同温度尺度不是既有小增益的简单主因。

## 决策规则

第一阶段先做 seed 5 的三组 legacy/scale-consistent 配对。只有三组差值都为正、平均 H 至少提高 `0.50`、新路线最差 H 高于 legacy 最好 H，且 U、S 均值都没有下降超过 `0.30`，才继续 seed 17 和 29。详细门槛固定在 `V5-INNOVATION-002` 的 README 中。

实际执行结果未通过上述门槛，IDEA 状态改为 `rejected`；除非以后提出不依赖 test 调参的新机制，否则不重开同一路线。

## 已关联实验

- `experiments/v5/innovation/INNOVATION-002_scale_consistent_fusion`
