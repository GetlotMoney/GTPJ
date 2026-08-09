# 实现说明

## E1：类别轴 PSE

`ClassPrototypeRelationAdapter` 先把类别原型归一化，再构造 `[1, C, D]`：

```text
prototype -> LayerNorm -> MultiheadAttention -> 0.1 residual -> L2 normalize
```

这个形状让 `C` 成为 token 轴。针对性测试会修改一个类别，并要求其他类别输出也发生变化。

## E2：同一权重、分组运行

`get_adapted_seen_text()` 和 `get_adapted_unseen_text()` 调用同一个 `class_pse_module`，但分别传入 seen 与 unseen 原型。这样权重共享，两个集合暂不做联合注意力。

训练 CE 仍使用 `final_logits[:, seenclass]`，未见类不进入 CE 负类。

## E3：有界训练校准

先计算全类别 softmax 下的未见类总概率 `r(x)`，再使用：

```text
L_floor = mean(relu(log(0.05) - log(r(x))))
L = L_current + 0.1 * L_floor
```

当 `r(x) >= 0.05` 时新增损失为 0，避免无界地把概率推向未见类。单元测试同时检查梯度方向和达到下限后的归零行为。

## E4：纯推理校准

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

当前已通过 25 项相关测试。真实 CUDA smoke、完整训练和 seed 复现尚未开始。
