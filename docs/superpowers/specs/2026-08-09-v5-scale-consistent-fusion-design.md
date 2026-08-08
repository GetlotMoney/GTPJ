# V5 全局—局部分数尺度一致融合设计

## 1. 结论

本实验只回答一个问题：V5 局部分支的贡献很小，是否主要因为全局分数乘了可学习温度、局部分数没有乘温度，导致两路分数不在同一尺度。

实验从冻结母版 `MODEL-V5-TEMPLATE-V1@2f5fa5e631ef82658d4bac587cdfd17f3534cb35` 建立独立 worktree 和独立分支，不修改母版分支、当前工作分支或历史消融分支。

候选融合公式固定为：

```python
final_logits = global_logits + 0.05 * logit_scale * local_logits
```

`0.05` 在查看本实验测试结果前固定。它把局部分数转换到与全局分数相同的温度尺度，同时只给局部原始余弦约 5% 的名义权重；相对当前约 `0.2 / 14.285 = 1.4%` 的起始名义权重是保守放大，不做测试集权重搜索。

## 2. 已知事实

- 冻结母版先计算 `global_logits = global_cosine * logit_scale`。
- `logit_scale` 初始为 `1 / 0.07 ≈ 14.285`，上限为 100。
- BVSA 的两路局部分数都是归一化余弦，合成后没有乘 `logit_scale`。
- 当前最终分数是 `global_logits + 0.2 * local_logits`。
- 已完成的三种子消融中，完整 V5 相对干净无局部模型的 H 差值为 `+0.25/-0.09/+0.09`，均值仅 `+0.08`，不能支持稳定增益。

因此，现有消融只能说明“当前融合写法下局部分支贡献很小”，不能直接说明“局部信息无效”。

## 3. 实验身份与隔离

```yaml
idea_id: IDEA-0004
experiment_id: V5-INNOVATION-002
candidate_model_version: MODEL-V5-SCALE-FUSION-CANDIDATE-V1
branch: exp/v5/innovation/innovation-002-scale-consistent-fusion
worktree: D:/Backup/Documents/Myself/GTPJ/.runtime/worktrees/v5_scale_fusion
base_template_id: MODEL-V5-TEMPLATE-V1
base_template_tag: model/v5-template-v1
base_template_commit: 2f5fa5e631ef82658d4bac587cdfd17f3534cb35
template_registry_commit: 7da3c72a060510ad35dd66d839cbe22569b3d8cf
dataset: CUB
metric: U/S/H/ZS，沿用冻结母版评估函数
```

母版 Tag 是 annotated tag，剥离后准确指向 `2f5fa5e`。该代码提交内部的 `experiments/v5/TEMPLATE.yaml` 仍是更早的 V0 账本；后续提交 `7da3c72` 才登记 V1。实验记录必须同时写 Tag、代码提交和登记提交，不能把这处历史账本差异隐藏掉。

隔离规则：

- 当前分支中的未提交文件不暂存、不重置、不复制进实验分支。
- 数据通过训练命令显式传入的 `--data-root` 只读访问；不在 worktree 里复制数据，也不新建第二个数据入口。
- 每个 `RUN-xxx` 写入 `D:/Backup/Documents/Myself/GTPJ/.runtime/runs/v5/innovation/V5-INNOVATION-002_scale_consistent_fusion/RUN-xxx/`，目录在启动前必须不存在。
- GPU 串行使用；不同时启动两个训练进程。
- 入口会一次载入约 9.84 GiB 特征缓存；正式开跑前系统可用物理内存至少 14 GiB，低于门槛只完成准备，不强行训练。
- 不 push，不改母版 Tag，不覆盖历史日志或 checkpoint。

## 4. 本轮范围

### 包含

- 保留旧融合路线作为同代码对照。
- 增加尺度一致融合路线，固定 `fusion_beta=0.05`。
- 同一训练入口通过实验配置明确选择 `legacy` 或 `scale_consistent`。
- 为融合公式、默认关闭行为、配置拒绝、输出目录隔离和梯度路径增加自动测试。
- 建立 10 行参数矩阵，其中后 4 行只有第一阶段通过后才运行。
- 运行后记录每轮 U/S/H/ZS、最佳 epoch、日志和最佳模型。

### 不包含

- 不修改 seen/unseen 划分、类别顺序、标签映射或评估公式。
- 不修改 PSE、ICSA、FGVD、BVSA、SGMP 和辅助损失的内部公式。
- 不搜索 `fusion_beta`，不根据测试集表现改为 0.1、0.2 或其他数值。
- 不在本实验里修纯 CLIP 基线。
- 不在本实验里做 PSE、ICSA、topology 或局部子模块消融。
- 不物理删除局部分支、母版代码、历史分支或失败结果。

纯 CLIP 公平基线和全局语义模块因子实验是两个独立问题；只有本实验完成并形成 keep/stop 结论后，再分别建立计划。

## 5. 代码设计

新增一个可单元测试的纯函数，输入全局 logits、局部 logits、当前温度、融合模式和固定系数，输出最终 logits：

```python
def fuse_global_local_logits(
    global_logits,
    local_logits,
    *,
    logit_scale,
    fusion_mode,
    fusion_beta,
):
    if fusion_mode == "legacy":
        return global_logits + 0.2 * local_logits
    if fusion_mode == "scale_consistent":
        return global_logits + fusion_beta * logit_scale * local_logits
    raise ValueError(f"不支持的 fusion_mode：{fusion_mode!r}")
```

模型默认值必须保持 `legacy`。缺少实验字段时，冻结母版的输出、损失和梯度仍与历史实现一致。只有实验配置明确写 `fusion_mode: scale_consistent` 且 `fusion_beta: 0.05` 时启用新公式。

训练入口增加实验配置解析和唯一输出目录参数；输出目录已存在时直接拒绝，避免覆盖旧运行。运行日志必须打印：实验编号、RUN 编号、融合模式、beta、实际 `logit_scale`、代码提交、配置哈希和 seed。

## 6. 先测试后实现

实现代码前先增加并运行下列失败测试：

1. `legacy` 返回 `global + 0.2 * local`。
2. `scale_consistent` 返回 `global + beta * logit_scale * local`。
3. 缺少新字段时模型仍走 `legacy`，冻结母版行为不变。
4. 非法 `fusion_mode`、非有限 beta、beta 小于等于 0 时拒绝。
5. 新公式的反向传播能到达局部分数和 `logit_scale`。
6. `local_logits=0` 时两种路线输出完全相同。
7. 正式训练输出目录已存在时拒绝，目录不存在时只创建对应 `RUN-xxx` 目录。

必须先看到测试因“功能尚不存在”而失败，再写最小实现使其通过。随后重跑 V5 母版合同、复现测试和完整相关测试。

## 7. 参数矩阵与运行顺序

### 第一阶段：同 seed 重复性

| RUN | 组别 | seed | repeat_of | 状态 |
|---|---|---:|---|---|
| RUN-001 | legacy | 5 | - | 第一阶段必跑 |
| RUN-002 | scale_consistent | 5 | - | 第一阶段必跑 |
| RUN-003 | legacy | 5 | RUN-001 | 第一阶段必跑 |
| RUN-004 | scale_consistent | 5 | RUN-002 | 第一阶段必跑 |
| RUN-005 | legacy | 5 | RUN-001 | 第一阶段必跑 |
| RUN-006 | scale_consistent | 5 | RUN-002 | 第一阶段必跑 |

第一阶段按 `RUN-001 → 002 → 003 → 004 → 005 → 006` 交替执行，减少运行时段和机器状态只偏向一组的风险。它同时检查两种重复性：同一公式自身是否稳定，以及新旧公式之间是否形成稳定间隔。不能只重复新公式而复用单个旧结果。

第一阶段通过条件：

- 两组各自 3 次都完整结束，无 NaN、OOM 或证据缺失。
- legacy 三次均值必须落在旧 seed 5 结果 `74.17 ± 0.30 H` 内；否则先判为环境或复现异常，不能把新公式记为失败。
- `mean(H_scale) - mean(H_legacy) >= 0.50`。
- 三组配对差值 `RUN-002−001`、`RUN-004−003`、`RUN-006−005` 全部大于 0。
- 新公式最差一次 H 必须高于旧公式最好一次 H，使两组三次结果形成清楚分离。
- 新公式相对旧公式的三轮平均 U、S 任一项不得下降超过 `0.30`；若 H 达标但越过该边界，进入人工解释，不自动进入第二阶段。

任一硬条件不满足，RUN-007 至 RUN-010 保持未启动，本候选记录为“尺度假设未获支持”。

### 第二阶段：排除幸运 seed

| RUN | 组别 | seed | 对照 | 状态 |
|---|---|---:|---|---|
| RUN-007 | legacy | 17 | RUN-008 | 第一阶段通过后运行 |
| RUN-008 | scale_consistent | 17 | RUN-007 | 第一阶段通过后运行 |
| RUN-009 | legacy | 29 | RUN-010 | 第一阶段通过后运行 |
| RUN-010 | scale_consistent | 29 | RUN-009 | 第一阶段通过后运行 |

第二阶段通过条件：

- seed 17、29 的 H 差值都大于 0。
- 先把 seed 5 的三次重复压成一个 seed 均值，再与 seed 17、29 等权汇总；三个 seed 的平均 H 增益至少 `+0.50`，不能让 seed 5 因为重复三次而获得三倍权重。
- 三个 seed 的方向一致，结果不能只由 seed 5 的三次重复撑起。
- 完整报告 U/S/H/ZS，不只挑 H 或最好单次。

## 8. 结果解释

### 通过

只把“尺度一致融合”登记为候选主贡献。FGVD、BVSA、SGMP 和辅助损失仍是支持组件，不能因为总体通过就自动声称它们各自有效；它们需要后续独立消融。

候选论文叙事是：全局 CLIP 证据与局部对齐证据来自不同计算路径，直接相加会造成温度尺度失配；尺度一致融合让局部证据在同一 logit 空间参与决策。

该叙事在正式写论文前仍需做文献查重，不能仅凭本地代码宣布首创。

### 未通过

不删除任何代码或历史。结论写为：在保守的同尺度融合下，局部分支仍未表现出稳定 H 增益，因此停止把局部路线作为当前论文主线，后续以已验证的干净无局部模型开展全局语义组件消融。

## 9. 风险与回退

- 风险：放大局部 logits 也可能放大噪声。处理：beta 预先固定且只跑一个值。
- 风险：相同 seed 的三次运行可能完全一致。处理：第一阶段仍能证明可复现；第二阶段负责排除幸运 seed。
- 风险：新旧模型的配置或输出目录不一致。处理：除融合字段外配置逐字段相同，输出目录不参与科学参数指纹。
- 风险：当前训练入口把日志写到共享 `train_log/CUB`。处理：实验入口必须使用显式、不可覆盖的 `RUN-xxx` 目录。
- 风险：worktree 没有本地 `data` 入口。处理：专用训练入口强制接收 `--data-root`，开跑检查核对该路径和关键文件身份，不创建 Junction 或数据副本。

回退方式：丢弃实验分支中的候选提交即可；冻结母版、原分支和历史实验不受影响。不得使用 `git reset --hard` 或删除历史结果。

## 10. 完成标准

- 设计、实现说明、框架图、参数矩阵和技术演进记录均在项目内。
- 机器测试通过，且有一次独立只读代码审核。
- 运行前提交唯一、工作树干净、配置和数据身份固定。
- 每个已启动 RUN 都有独立目录、完整训练日志、U/S/H/ZS 和最佳模型。
- 未启动的条件 RUN 明确记录为未启动，不能写成失败或完成。
- 结果只按预先写下的门槛解释，不在看到测试集分数后改变 beta 或成功标准。
