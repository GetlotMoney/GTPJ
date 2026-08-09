# 实现说明

## 结论

实现采用最小开关：legacy 不动，只有 `scale_consistent` 才进入新公式。训练使用独立入口和独立 RUN 目录，canonical 训练入口与 canonical V5 配置不改。

## 代码路径

### `model/MyModel.py`

- 新增 `fusion_mode` 与 `fusion_beta` 的校验。
- legacy 仍执行字面原式 `final_logits = global_logits + 0.2 * local_logits`。
- `scale_consistent` 执行 `global_logits + fusion_beta * logit_scale * local_logits`。
- 正式配置把 `fusion_beta` 固定为 `0.05`。
- `logit_scale` 与全局分支共用模型中已经计算好的 `clamp(exp(raw_logit_scale), max=100)`，不会再取一次不同值。
- 训练时仍只从 `final_logits` 取 seen 类列；评估时仍使用完整类别列。

### `train_V5_INNOVATION_002_CUB.py`

- 只接受 `--config`、`--data-root`、`--run-dir`、`--run-id` 四个必填入口参数。
- 启动前检查 Git 工作区、配置字段、输入文件和输出目录。
- 用标准库读取可用物理内存；少于 14 GiB 或无法读取时，在创建 RUN 目录之前失败。
- 固定写入 `training.log`、`metrics.json`、`config_snapshot.yaml`、`run_identity.json`、`model_best.pth`、`checkpoint_last.pth`。
- 对训练 logits、loss、梯度、评估 logits、U/S/H/ZS 和 `logit_scale` 做有限值检查。
- `metrics.json` 只在全部训练与落盘完成后写入 `completed` 状态。

### `tools/v5_innovation_002_runtime.py`

- 只允许 `legacy` 和 `scale_consistent`。
- 只允许 `fusion_beta=0.05`、`local_weight=0.2`、`score_mode=add`。
- 只允许 seed `5/17/29`。
- RUN id 必须严格符合 ASCII `RUN-xxx`，且输出目录必须尚不存在。

### 配置与参数矩阵

- `configs/RUN-001.yaml` 至 `RUN-010.yaml` 是逐任务配置快照。
- `PARAMETER_MATRIX.csv` 是机器读取的十行任务表。
- RUN-003/005 精确重复 RUN-001，RUN-004/006 精确重复 RUN-002。
- RUN-007 至 RUN-010 只有在第一阶段门槛通过后才启动。

## 保持不变的内容

- 数据、划分、类别顺序与标签映射。
- 母版的特征路径、损失、优化器、学习率日程、epoch 数和评估指标。
- canonical `train_GTPJ_CUB.py`。
- canonical `config/versions/v5.yaml`、`config/GTPJ_cub_gzsl.yaml`、`experiments/v5/config.yaml` 与 `experiments/v5/baseline/config.yaml`。

## 输入、输出与失败方式

输入是一个冻结的 `RUN-xxx.yaml`、显式数据根目录、全新 RUN 输出目录和 RUN id。输出只进入该 RUN 的独立目录。

出现下面任一情况时，当前 RUN 必须失败并停止后续判断：

- Git 工作区不干净或仓库身份不符。
- 可用物理内存少于 14 GiB，或系统无法给出可信读数。
- 配置字段、seed、融合方式或 beta 不符合冻结规则。
- 目标 RUN 目录已经存在。
- 输入文件身份变化。
- NaN、Inf、OOM、非零退出码或必要结果文件缺失。

## 回退办法

回退时把配置设为 `fusion_mode=legacy`，即可回到母版融合语义。不得删除 scale-consistent 代码、失败配置或日志；如果第一阶段失败，只把后四个任务记为未启动。
