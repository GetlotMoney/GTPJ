# 实现说明

## 先做什么、再做什么

1. 母版 `GTPJ.forward` 原样生成 `global_logits`、`local_logits` 和 SGMP/BMDD 等辅助张量。
2. 训练时只在 seen 类全局分数中取 top1-top2；评估时在完整 200 类全局分数中取 top1-top2。
3. margin 只给 gate 使用，并在进入 gate 前 `detach`，因此不会多开一条梯度回到全局分支。
4. 用固定公式重算最终分数，随后按母版原规则得到训练 seen 类轴或评估 200 类轴。

公式为：

```text
margin = top1(global) - top2(global)
gate = sigmoid(bias - softplus(slope_raw) * detach(margin))
final = global_logits + 0.05 * logit_scale * gate * local_logits
```

`slope_raw` 初始化为 `log(exp(1)-1)`，所以经过 `softplus` 后的有效 slope 正好是 `1.0`。由于有效 slope 恒为正数，margin 越大，gate 不会增大。

## 文件职责

| 文件 | 职责 |
|---|---|
| `confidence_local_gate.py` | 实验专属模型包装，只重算最终分数并返回 gate 统计。 |
| `train.py` | import-safe、CUDA-only 的完整训练入口，复用现有数据划分与评估函数。 |
| `configs/RUN-001..003.yaml` | 三份逐字节相同、seed=5 的配置。 |
| `PARAMETER_MATRIX.csv/.md` | 三个真实任务的机器表和阅读版草案。 |

## 安全门和输出

- 必填参数：`--config --data-root --run-dir --expected-run-commit`。
- 启动前拒绝 CPU、脏 Git、错 commit、缺输入、已存在输出目录。
- 对输入特征、logits、loss、梯度、参数和指标做有限数检查。
- 输入身份记录路径、SHA-256、大小、张量形状与 dtype。
- `training.log` 和 `metrics.json` 逐 epoch 记录训练/评估 gate 的 mean/min/max。
- `training.log`、`metrics.json`、`model_best.pt`、`checkpoint_last.pt` 使用同目录临时文件加 `os.replace` 原子落盘。

## 验证与回退

专项测试入口：

```powershell
F:\Anaconda\envs\dvsr_gpu\python.exe -m unittest tests.test_v5_confidence_local_gate -v
```

回退只需撤销本实验目录、专项测试和两处文档登记；canonical 文件没有改动，不需要模型迁移。
