# 实现说明

## 第二版：对称且限幅的原型路径

第二版保留旧句子 PSE，不再用类别关系模块替换它：

```text
7 条类别句子 -> 旧句子 PSE -> 单个类别原型
                              -> 限幅类别关系注意力 -> 最终原型
```

R1 只让 unseen 句子也经过同一个 `pse_module`；seen/unseen 分组运行。新增 unseen 前向放在独立随机数上下文里，计算完成后恢复 RNG，避免改变后续 BVSA/Transformer dropout 的随机数轨迹。

R2 使用 `BoundedClassPrototypeRelationAdapter`：

```text
base = normalize(PSE(sentences))
relation = MHA(LayerNorm(base))
direction = relation / max(norm(relation), 1)
correction = 0.1 * direction
output = normalize(base + correction)
```

因此每个类别的修正范数硬限制为 `<=0.1`。MHA 输出投影从全零开始，所以初始输出与 R1 完全一致；训练后一个类别仍能通过类别轴注意力影响其他类别。

## 类不重叠验证

`build_v5_class_disjoint_validation_split` 先验证训练缓存顺序严格等于 xlsa17 `trainval_loc`，再完成：

- `train_loc` 的 100 类作为 pseudo-seen；每类固定留出 20% 图片评估 S。
- `val_loc` 的 50 类作为 pseudo-unseen，评估 U 和 ZS。
- 原类别编号显式重排到连续的 150 类轴，不靠目录顺序或前后位置猜测。
- 验证配置不登记、读取或加载正式 test 缓存。
- 训练和验证只保留一份约 5.8 GiB 的 patch 缓存，每个 batch 按位置临时取数；不会再为 train、seen validation、unseen validation 各复制一份大张量。

## 第二版暂不使用校准

第一版 E1 已经偏向 unseen，再增加未见概率或降低 seen logits 会让 S 更差。因此 R0–R2 固定 `lambda_self_calibration=0`、`gamma=0`。下面 E3/E4 章节只保留为第一版历史实现说明。

## 第一版历史 E1：类别轴 PSE

`ClassPrototypeRelationAdapter` 先把类别原型归一化，再构造 `[1, C, D]`：

```text
prototype -> LayerNorm -> MultiheadAttention -> 0.1 residual -> L2 normalize
```

这个形状让 `C` 成为 token 轴。针对性测试会修改一个类别，并要求其他类别输出也发生变化。

## 第一版历史 E2：同一权重、分组运行

`get_adapted_seen_text()` 和 `get_adapted_unseen_text()` 调用同一个 `class_pse_module`，但分别传入 seen 与 unseen 原型。这样权重共享，两个集合暂不做联合注意力。

训练 CE 仍使用 `final_logits[:, seenclass]`，未见类不进入 CE 负类。

## 第一版历史 E3：有界训练校准

先计算全类别 softmax 下的未见类总概率 `r(x)`，再使用：

```text
L_floor = mean(relu(log(0.05) - log(r(x))))
L = L_current + 0.1 * L_floor
```

当 `r(x) >= 0.05` 时新增损失为 0，避免无界地把概率推向未见类。单元测试同时检查梯度方向和达到下限后的归零行为。

## 第一版历史 E4：纯推理校准

```text
adjusted_logits[:, seenclasses] = raw_logits[:, seenclasses] - gamma
```

- `gamma=0` 与 E2 逐元素完全一致。
- 输入 logits 不会被原地修改。
- unseen 类内部排序和 ZS 不变。
- `select_calibrated_stacking_gamma` 拒绝 `split_name != "validation"`。

## 复现和结果边界

- 模型 RNG 与 batch RNG 分离；batch generator state 写入 checkpoint。
- 大文件哈希清单原子写入 `.runtime/data_fingerprints/v5_inputs.json`。
- 正式输出目录必须不存在；同一 RUN 内只更新 `checkpoint_last.pth`。
- 训练期间不评估测试集；固定训练结束后只评一次，并保存 `model_final.pth`。

## 已有机器验证

```text
tests.test_v5_pse_class_relation_calibration
tests.test_reproducibility
tests.test_v5_template_contract
```

当前已通过专项 20 项、合计 35 项相关测试；真实 CUDA 前向、反向和最终评估已通过。R0–R2 完整训练在冻结提交后开始，多 seed 复现尚未开始。
