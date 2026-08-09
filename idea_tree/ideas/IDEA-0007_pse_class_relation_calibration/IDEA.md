# IDEA-0007：PSE 类别关系增强与 GZSL 自校准

```text
idea_id: IDEA-0007
status: rejected
source_type: hybrid
source_ref: owner_plan_2026-08-10 + counterfactual_probe_other_classes_delta_0
base_version: v5
linked_experiment: V5-INNOVATION-008
```

## 来源与当前事实

这个想法来自 owner 的五组渐进实验计划，以及对旧 PSE 的反事实检查。

旧 PSE 接收 `[类别数, 句子数, 特征维度]`，但 `MultiheadAttention` 实际把“类别数”当作 batch，所以注意力只在每个类别自己的句子之间发生。固定其他输入、只修改类别 A 后，其他类别输出的最大变化为 `0.0`，说明它没有建立类别间关系。

推理期校准采用 calibrated stacking 的定义：统一从已见类 logits 中减去 `gamma`。参考论文为 [An Empirical Study and Analysis of Generalized Zero-Shot Learning for Object Recognition](https://arxiv.org/pdf/1605.04253)。

训练期校准只借鉴 DAZLE“给未见类保留概率”的动机，不照搬其无界损失。原因是本实验坚持 seen-only CE；若直接最小化 `-log(unseen probability mass)`，模型会持续把未见类总概率推向 1。这里改为固定概率下限，达到下限后损失归零。

## 假设

先让 PSE 真正沿类别轴建模，再用同一套权重分别处理已见与未见原型，应当优先改善 `U` 和 `H`。如果表示学习改善后仍有已见类偏置，再分别测试训练期有界校准和推理期判决线移动。

## 五组最小闭环

| 组别 | 唯一变化 | 回答的问题 |
|---|---|---|
| E0 | 原 V5 PSE 路径 | 新公平口径下的基线是多少 |
| E1 | 类别轴自注意力 | 类别关系是否真的有用 |
| E2 | 同一 PSE 分组处理未见原型 | 未见原型的一致处理是否改善迁移 |
| E3 | `lambda=0.1`、未见总概率下限 `0.05` | 训练期能否温和减少已见偏置 |
| E4 | E2 checkpoint + 验证集确定的 `gamma` | 单纯移动判决线还有多少空间 |

第一阶段只跑 seed 5。最好的训练方案再与 E0 做 seed 5、17、29 的成对复现；第二阶段尚未展开成运行行，避免在 seed 5 结果出来前预造任务。

## 不变边界

- 未见类图片和标签不进入训练。
- 交叉熵仍只计算已见类，未见类不作为 CE 负类。
- 类别顺序、seen/unseen split、logits 形状和 U/S/H/ZS 算法不变。
- 批次采样使用独立随机数生成器，并随 checkpoint 保存和恢复。
- 正式测试只在固定训练结束后执行一次；`gamma` 只能由类不重叠验证划分选择。

## 风险与停止条件

- E1 不提升：停止把类别关系 PSE 当作有效创新。
- E1 提升而 E2 不提升：未见原型继续使用原始 CLIP/GPT-5.5 均值。
- E3 只交换 U/S 而不提高 H：删除训练校准。
- 只有 E4 提升：结论只能写“判决偏置改善”，不能写成表示学习提升。
- E4 在类不重叠验证入口准备好之前保持未启动，绝不从测试集反推 `gamma`。

## 2026-08-10 实验结论

E0 `RUN-007` 得到 `U/S/H/ZS=71.25/76.30/73.69/81.32`；E1 `RUN-002` 得到 `78.75/58.17/66.92/81.28`。E1 的 U 上升 7.50，但 S 下降 18.13，H 下降 6.77。按第一条停止条件，本想法在当前实现上标记为 `rejected`，E2-E4 跳过。

随后按 owner 批准的第二版，用不接触正式 test 的 100/50 类划分补做 R0/R1/R2。三组 H 分别为 `69.91/61.27/58.14`；R2 的修正范数和旋转角严格受限，但 U 比 R0 低 `15.96`。因此失败并非第一版单纯尺度失控造成：共享旧句子 PSE 与当前类别关系迁移方向本身都不利于 pseudo-unseen。本 idea 维持 `rejected`，不再进入正式测试、校准或多 seed。
