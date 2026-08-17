# 通用 GZSL 实验规范

本文用于在新电脑或新环境中搭建、运行、评估和记录广义零样本学习实验。结论先行：正式 GZSL 实验必须固定 seen/unseen 类划分、固定类别顺序、训练只使用 seen 图像监督、评估在 seen+unseen 全类别空间竞争，并同时报告 `GZSL-U`、`GZSL-S`、`GZSL-H` 和 `ZSL`。

## 1. 适用范围

本规范适用于 CUB、AWA2、SUN 等标准 GZSL 数据集，也适用于自建数据集。只要任务包含“训练类”和“未见类”，并需要在测试时让 seen 类和 unseen 类共同竞争，就应使用本规范。

术语约定：

- `seen class`：训练阶段有图像和类别标签监督的类别。
- `unseen class`：训练阶段没有图像标签监督的类别。
- `semantic prototype`：属性向量、类别文本、CLIP 文本特征、GPT/VDT 描述等类别语义表示。
- `global label`：数据集原始全局类别编号，评估必须回到这个编号体系。
- `local seen label`：训练 CE loss 可用的 seen 类局部编号，只能用于训练内部，不能替代评估标签。

## 2. 新电脑环境基线

新电脑先做环境记录，再跑实验。每次正式 run 必须保存环境快照。

最小检查项：

```text
操作系统和版本
GPU 型号
NVIDIA driver 版本
CUDA runtime 版本
Python 版本
PyTorch / torchvision / timm / transformers 等关键包版本
当前 Git commit
当前配置文件路径
数据集路径
随机种子
```

Windows PowerShell 可记录：

```powershell
python --version
python -c "import torch; print('torch=', torch.__version__); print('cuda=', torch.version.cuda); print('available=', torch.cuda.is_available()); print('gpu=', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'cpu')"
nvidia-smi
git rev-parse HEAD
git status --short
pip freeze > env_pip_freeze.txt
```

Linux Bash 可记录：

```bash
python --version
python - <<'PY'
import torch
print("torch=", torch.__version__)
print("cuda=", torch.version.cuda)
print("available=", torch.cuda.is_available())
print("gpu=", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu")
PY
nvidia-smi
git rev-parse HEAD
git status --short
pip freeze > env_pip_freeze.txt
```

建议目录：

```text
project_root/
  data/
    xlsa17/data/CUB/
    xlsa17/data/AWA2/
    xlsa17/data/SUN/
    cache/
  configs/
  runs/
    <dataset>/<method>/<run_id>/
      config.yaml
      env.txt
      train.log
      eval.log
      metrics.json
      predictions.csv
      rule_checks.yaml
      checkpoints/
```

数据集、特征缓存、checkpoint、大型日志不进 Git。Git 中只保留轻量摘要、配置、脚本、规则检查和结果索引。

## 3. 数据和标注规范

### 3.1 标准 split

标准数据集优先使用公开固定 split，例如 xlsa17 的 `att_splits.mat`。至少要记录：

```text
allclasses_names: 全部类别名，顺序必须固定
seenclasses: seen 类全局编号
unseenclasses: unseen 类全局编号
trainval_loc: seen 训练样本索引
test_seen_loc: seen 测试样本索引
test_unseen_loc: unseen 测试样本索引
labels: 每张图像的全局类别标签
att 或 text_features: 类别语义原型
```

#### 3.1.1 CUB/xlsa17 默认训练—验证—测试方案

CUB 的所有新 GZSL 实验统一使用下面的语义：

1. `train_loc` 共 4,702 张、100 类，是候选阶段数据池；使用项目唯一的 `cub_xlsa17_pseudo_v1` 划分：MATLAB 样本索引与 `res101.mat` 的 `labels` 都先减 1，得到零基样本索引与零基 `global_class_id`；每类样本先升序排列，再以 `np.random.Generator(np.random.PCG64(20260817 + global_class_id)).permutation(...)` 独立打乱，每类前 `floor(0.8 * n_c)` 个为 sub-train、其余为 pseudo-seen，最后分别升序保存。唯一 artifact 为 `data/cache/CUB_xlsa17_pseudo_v1.json`，只含 `algorithm_version`、`att_splits_sha256`、`res101_sha256`、`labels_zero_based_int64_sha256`、`subtrain_indices_zero_based`、`pseudo_seen_indices_zero_based` 六个 key；labels SHA 对 C-order little-endian int64 字节计算。artifact 不内含自身 SHA，以 UTF-8、key 排序、紧凑分隔符、无尾换行序列化后计算 split SHA，并在参数表记录。首次生成后不可改写，所有实验必须复用同一 split SHA。
2. 候选只在固定 80% 上训练；固定 20% 只计算 pseudo-S。`val_loc` 共 2,355 张、50 个不重叠类，只计算 pseudo-U 和 ZS，不进入梯度。
3. 候选在 100 个 pseudo-seen 类与 50 个 pseudo-unseen 类的 150 类联合空间计算 pseudo-U/S/H，并按预先声明的 pseudo-H 冻结结构、超参数、epoch 和校准参数。
4. 冻结后从头使用 `trainval_loc` 全部 7,057 张、150 个 seen 类训练最终模型。
5. 对每个独立正式 run，最终 checkpoint 冻结后，`test_seen` 的 1,764 张与 `test_unseen` 的 2,967 张只正式评估一次；GZSL 在 200 类联合空间报告 U/S/H，ZS 只在 50 个 unseen 类空间报告。

这套方案的目的不是减少候选训练数据，而是给 GZSL 的 S 保留独立验证样本；否则只看 `val_loc` 的 U 会偏向 unseen，无法可靠选择调和指标 H。快速筛选可以统一缩短候选预算，但不能改变固定划分，也不能省略 7,057 张最终重训。

历史结果的 `legacy_protocol_exact_repeat` 必须原样保留其旧评估口径；若旧协议逐 epoch 使用 official test 选模，必须标记 `test_exposed: true`，且只能回答历史结果能否复现，不能作为新方法标准结果、横向公平比较或 promotion 输入。

如果自建 split，必须额外保存：

```text
split_name
split_version
class_order
seen_class_ids
unseen_class_ids
sample_id -> global_label
sample_id -> split
生成 split 的脚本和随机种子
```

### 3.2 标签映射

训练时可以把 seen 类映射到局部编号 `[0, N_seen-1]`，但必须保存双向映射：

```text
global_to_seen_local: global_label -> local_seen_label
seen_local_to_global: local_seen_label -> global_label
eval_class_order: [全部 global_label，顺序固定]
```

评估输出的预测标签必须是全局标签。禁止用局部 seen 标签直接计算 GZSL 指标。

### 3.3 禁止信息泄漏

以下情况视为无效实验：

- unseen 测试图像参与训练、特征训练、缓存拟合或数据增强统计拟合。
- official `test_unseen_loc` 图像标签参与 loss、采样权重、校准参数搜索或 early stopping；`val_loc` 只允许按本协议用于预声明的 pseudo-GZSL 选择。
- 重新排序类别后没有同步修正语义原型和标签。
- 用 test_unseen 的结果反复调超参，却把该结果当作正式测试结果。

允许使用 unseen 类的语义原型，但必须说明来源和使用方式。例如属性向量、类别名文本、CLIP 文本编码、人工描述、GPT 生成描述等。若 unseen 语义原型经过训练模块 forward，必须记录是否进入 loss、是否产生梯度、是否影响训练参数。

## 4. 模型和训练规范

训练阶段默认只从 seen 图像样本构造监督 loss。训练 logits 可是 `[B（图片/样本数量）, N_seen（seen 类别数量）]`，也可以是 `[B（图片/样本数量）, N_total（全部类别数量）]` 后只取 seen 部分算 loss，但必须明确记录。

每个新增模块必须记录：

```text
输入张量形状、dtype、device
输出张量形状、dtype、device
训练阶段行为
评估阶段行为
梯度路径
是否触碰 unseen semantic prototype
是否触碰 unseen image feature
关闭该模块时是否等价回到 baseline
预期影响的指标
```

训练 run 必须固定并记录：

```text
dataset
split_source
backbone
semantic_source
feature_cache_path
config_path
seed
epochs
batch_size
optimizer
learning_rate
weight_decay
augmentation
train_command
eval_command
```

正式对比时，baseline 和新方法必须使用同一 split、同一类别顺序、同一特征缓存或同一 backbone 设置、同一语义来源，除非实验目的就是比较这些因素。

## 5. 评估规范

### 5.1 GZSL 评估

GZSL 评估时，候选类别必须是 seen+unseen 全类别。模型输出应能映射到：

```text
logits: [B（图片/样本数量）, C_total（全部候选类别数量）]
class_axis: 固定的 eval_class_order
prediction: argmax(logits, dim=1) 后映射为 global_label
```

在 `test_unseen` 上计算 unseen 类平均准确率：

```text
acc_c = correct_samples_of_class_c / total_samples_of_class_c
GZSL-U = mean(acc_c for c in unseenclasses)
```

在 `test_seen` 上计算 seen 类平均准确率：

```text
acc_c = correct_samples_of_class_c / total_samples_of_class_c
GZSL-S = mean(acc_c for c in seenclasses)
```

调和平均：

```text
GZSL-H = 2 * GZSL-U * GZSL-S / (GZSL-U + GZSL-S)
```

如果 `GZSL-U + GZSL-S = 0`，则 `GZSL-H = 0`。

默认使用 per-class macro accuracy，不使用按样本数加权的 micro accuracy 作为主指标。结果统一报告百分比，例如 `73.93%`。

### 5.2 ZSL 评估

ZSL 只在 unseen 测试样本上评估，候选类别只允许 unseen 类：

```text
ZSL = mean per-class accuracy on test_unseen with candidate labels = unseenclasses
```

注意：`ZSL` 不等于 `GZSL-U`。`GZSL-U` 是 unseen 样本在 seen+unseen 全类别竞争下的准确率，通常更难。

### 5.3 checkpoint 选择

候选阶段以固定 20% pseudo-seen 与 `val_loc` pseudo-unseen 组成的 pseudo-GZSL-H 选择 checkpoint。只看 pseudo-U 或 pseudo-S 的预声明偏置分析只能标记为 `diagnostic_only / not_confirmation_evidence: true`，不能进入正式候选、confirmation 或 promotion。选定 epoch 后，最终模型必须按该固定 epoch 从头使用完整 `trainval_loc` 训练；official GZSL-H 只用于报告，不能再选择 checkpoint。

正式报告至少包含：

```text
pseudo_selected_epoch
GZSL-U
GZSL-S
GZSL-H
ZSL
U/S gap = GZSL-S - GZSL-U
frozen_final_checkpoint
eval_log_path
```

## 6. 评估产物标注

每次评估建议输出 `predictions.csv`：

```text
sample_id
image_path
split: test_seen 或 test_unseen
true_global_label
true_class_name
pred_global_label_gzsl
pred_class_name_gzsl
pred_is_seen_gzsl
pred_score_gzsl
correct_gzsl
pred_global_label_zsl
pred_class_name_zsl
correct_zsl
```

其中 `pred_global_label_zsl`、`pred_class_name_zsl`、`correct_zsl` 只对 unseen 测试样本有意义；seen 测试样本可为空。

`metrics.json` 建议字段：

```json
{
  "dataset": "CUB",
  "split_source": "xlsa17/att_splits.mat",
  "method": "method_name",
  "run_id": "RUN-YYYYMMDD-CUB-method-seed1-attempt001",
  "seed": 1,
  "commit": "<git_commit>",
  "config_path": "configs/xxx.yaml",
  "class_order_hash": "<hash>",
  "seen_class_count": 150,
  "unseen_class_count": 50,
  "metric_semantics": "standard GZSL U/S/H/ZS, per-class macro accuracy",
  "pseudo_selected_epoch": 26,
  "GZSL-U": 71.43,
  "GZSL-S": 76.36,
  "GZSL-H": 73.81,
  "ZSL": 81.25,
  "frozen_final_checkpoint": "runs/.../checkpoints/final_frozen.pt"
}
```

`rule_checks.yaml` 建议字段：

```yaml
rule_checks:
  - rule_id: seen_unseen_split_unchanged
    verdict: pass
    checked_by: script
    authority_ref: xlsa17/att_splits.mat
  - rule_id: class_order_unchanged
    verdict: pass
    checked_by: script
    authority_ref: class_order_hash
  - rule_id: label_mapping_unchanged
    verdict: pass
    checked_by: script
    authority_ref: eval_class_order
  - rule_id: metric_semantics_standard
    verdict: pass
    checked_by: evaluator
    authority_ref: standard GZSL U/S/H/ZS
  - rule_id: unseen_label_leakage_forbidden
    verdict: pass
    checked_by: code_review
    authority_ref: train_dataset_and_loss_trace
```

任何 hard rule 不清楚时，该 run 只能标为 `blocked`、`rerun` 或 `reject`，不能标为 `best`、`confirmed` 或 `promote`。

## 7. 新电脑首轮验证流程

在长时间训练前，先跑小验证：

1. 环境检查：确认 `torch.cuda.is_available()`、GPU 名称、driver、CUDA 和 PyTorch 版本。
2. 数据检查：打印 seen/unseen 类数量、训练样本数、test_seen 样本数、test_unseen 样本数。
3. 标签检查：随机抽 5 个样本，打印 `sample_id`、`image_path`、`global_label`、`class_name`、`split`。
4. 类别顺序检查：保存 `eval_class_order` 和 hash，确认语义原型行数等于全部类别数。
5. one batch 检查：跑一个 batch，确认输入、输出和 loss 都不是 NaN。
6. tiny run：用少量 batch 跑 1 个 epoch，确认 train log、eval log、checkpoint、metrics.json 都能生成。
7. resume 检查：从 checkpoint 恢复一次，确认 epoch 和 optimizer 状态能延续。
8. dry eval 检查：固定 checkpoint 在 smoke/validation 数据上重跑 eval，确认指标可复现；不得为 dry eval 读取 official test。

这些检查通过后，再跑正式完整实验。

## 8. 结果记录和结论分级

每个 run 结论按以下等级标注：

```text
explore: 探索 run，可用于找方向，不能支撑论文 claim
best_single: 单次最优结果，只能说 best single
repeat_pending: 已有单次结果，等待同 seed、同配置、同协议的 exact repeat
confirmed_repeat: exact repeat 达到预注册恢复门；多 seed 只能另记稳定性诊断
rejected: 指标差、规则失败或证据不足
blocked: 关键规则、路径、数据或评估语义不清楚
promote_candidate: 可进入下一轮主线或论文表格候选
```

正式 promotion 至少需要：

```text
hard rules 全部 pass
baseline 与新方法同 split、同评估语义
promotion 必须先通过预注册 exact-repeat 门；只有 promotion/quality gate 明确要求时，才额外做多次同 seed clean repeat 作为 stable-confirm 证据
多 seed / seed sweep 只报告 mean ± std，并标记 not_confirmation_evidence: true
同时检查 best single 与 confirmed exact repeat；若 gate 明确要求，再检查同 seed stable-confirm
GZSL-H 提升不是由 GZSL-U 或 GZSL-S 单边崩塌换来的
保留训练日志、评估日志、checkpoint 路径和 metrics.json
```

结论表达模板：

```text
best single:
  RUN-xxx epoch=xx U=xx.xx S=xx.xx H=xx.xx ZS=xx.xx

stability diagnostic (not confirmation evidence):
  seeds=[1,2,3]
  H mean=xx.xx std=xx.xx
  U mean=xx.xx std=xx.xx
  S mean=xx.xx std=xx.xx
  ZS mean=xx.xx std=xx.xx

stable confirm (only when explicitly required):
  repeat_type=exact_repeat
  original_seed=<same seed>
  H mean/min/max/range=...

promotion judgment:
  promote / hold / reject / rerun

main risk:
  U/S gap、数据泄漏风险、class order 风险、超参调优风险、复现风险
```

## 9. 常见无效结果

以下结果不能进入正式表格：

- 只输出整体 accuracy，没有拆分 `GZSL-U` 和 `GZSL-S`。
- `GZSL-U` 用 unseen-only candidate labels 计算，混成了 `ZSL`。
- 训练时类别顺序和评估时类别顺序不一致。
- 训练 CE 用局部 seen label，评估时没有映射回 global label。
- 用 test_unseen 反复调校准参数，然后宣称无偏测试结果。
- 新模块关闭后不能回到 baseline，导致无法判断收益来自哪里。
- 只保存截图或聊天结论，没有日志、配置、commit 和指标 JSON。

## 10. 最小交付包

一次可审计的正式 GZSL run 至少交付：

```text
config.yaml
env.txt 或 env_pip_freeze.txt
train.log
eval.log
metrics.json
predictions.csv
rule_checks.yaml
checkpoint 路径
运行命令
Git commit
结论摘要
```

如果这些文件不完整，结论最多是探索结果，不应写成论文级 claim。
