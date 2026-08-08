# CONFIRM-002：V5 同种子初始化对齐

## 短版

老 V5 中有两个从未参加前向计算的全连接层。删掉它们不会改变公式，却会让后面的
SGMP、ICSA 初始权重和训练批次顺序发生变化。本实验在不恢复无用参数的前提下，
只恢复它们原来消耗的随机数，并验证修复后的 V5 能否回到老 V5 的同种子训练起点。

## 实验身份

```text
experiment_id: V5-CONFIRM-002
kind: confirmation
version: v5
base_template_id: MODEL-V5-TEMPLATE-V1
base_template_tag: model/v5-template-v1
base_template_commit: 2f5fa5e631ef82658d4bac587cdfd17f3534cb35
template_ledger: experiments/v5/TEMPLATE.yaml
experiment_binding: EXPERIMENT.yaml
branch_source: exact_template_commit
code_branch: exp/v5/confirmation/confirm-002-v5-seed-equivalence
historical_reference_tag: v5
historical_reference_commit: 4b259379d99c1a791442ea9e2fac0bb22b2411a9
run_commit: pending_pre_run_freeze
dirty_state: pending_pre_run_freeze
config: config.yaml
command: pending_formal_runner
seed: 5
python_env: pending_server_freeze
torch_cuda: pending_server_freeze
dataset_split: CUB xlsa17 standard_v1
cache_fingerprint: pending_server_freeze
log_artifact_id:
log_uri:
log_sha256:
log_size_bytes:
manifest: manifest.yaml
result_yaml: result.yaml
result_md: result.md
agent_summary: agent_summary.md
attempt_id: R1
repeat_type: same_seed_repeat
diagnostic_subtype: code_repair
not_confirmation_evidence: true
original_seed: 5
failure_stage:
U:
S:
H:
ZS:
best_epoch:
decision: needs_confirmation
promotion_decision: not_applicable
promote_to:
evidence_level: pending
result_status: needs_confirmation
best_observed_H:
confirmed_H:
max_attempts: 5
max_attempts_hard_cap: true
early_stop_on_best_hit: false
restore_target_H: not_applicable
near_miss_tolerance_H: not_applicable
near_miss_not_restored: false
confirmation_status: pending
status: planned
```

## 现在有什么问题

前一轮服务器对照中，今天的干净 V5 平均 H 为 `74.270`，老 V5 平均 H 为 `74.462`，
相差 `0.192` 个百分点。代码审查确认两边的活跃前向公式、七项损失和有效配置一致；
真正的差异出现在模型创建阶段：老 V5 在 BVSA 后创建了两个未使用的
`Linear(512, 768)`，它们虽然不参加预测，却先消耗了随机数。

因此，同样写 `seed=5` 时：

1. 两边的 PSE 和 BVSA 初始权重相同；
2. 从 SGMP、ICSA 开始，初始权重不同；
3. 模型创建后的随机状态不同，随后 `torch.randperm` 生成的训练批次顺序也不同；
4. 这会让两条训练轨迹从前 20 个 batch 内就分开。

前一轮结果只能说明两份代码在同一配置下得到接近的成绩，不能证明它们是严格的
“同 seed 数值等价迁移”。

## 这次怎么修

只在本实验分支的 BVSA 构造位置临时创建两次与历史一致的 `Linear(dim_com, dim_f)`，
让随机数序列前进到老 V5 的同一位置，随后立即丢弃对象。

这两个临时对象：

- 不注册为模型参数；
- 不进入 `forward`；
- 不进入优化器；
- 不进入 `state_dict` 或 checkpoint；
- 不增加正式模型的参数量和推理计算量。

冻结的 `MODEL-V5-TEMPLATE-V1` 不修改。本实验只在独立分支上验证；若服务器确认通过，
是否登记为新的 V5 模板版本要另走一次接纳流程，不能偷偷覆盖旧模板。

## 为什么不直接把两个全连接层加回来

直接加回去也能恢复随机序列，但会让两个完全无用的层永久出现在参数表、优化器和模型文件中，
以后读代码的人会误以为它们参与计算。现在采用的办法只保留历史随机顺序，不保留无效结构，
更容易读，也不会让 checkpoint 变大。

## 验收顺序

### 第 1 步：零训练代码检查

- 同 seed 创建老 V5 和修复版 V5；
- 比较全部活跃状态，必须逐元素完全相同；
- 比较模型创建后的 CPU 随机状态，必须完全相同；
- 比较随后 3 次训练批次抽样，必须完全相同；
- 确认参数名和 checkpoint 中没有 `proj_visual`、`proj_text`；
- 重跑现有前向、损失、梯度、数据和评估测试。

### 第 2 步：服务器零步指纹

用正式服务器 Python、PyTorch 和完整 `512→768` 尺寸重复第 1 步，不进入训练循环。
这一步成本很低，用来排除本机与服务器环境差异。

候选提交完成后，唯一命令为：

```bash
/data/lby/.conda/envs/dvsr_gpu/bin/python \
  experiments/v5/confirmation/CONFIRM-002_v5-seed-equivalence/verify_seed_equivalence.py \
  --formal-candidate-commit <40位候选提交>
```

正式模式除了检查权重和随机数，还会拒绝错误分支、错误提交、脏工作树、被替换的模型或配置。

### 第 3 步：正式 GPU 复现

服务器零步指纹和代码审核通过后，冻结 5 个 `seed=5` 的修复版任务，五次全部跑完，
不按单次最高值提前停止。
本轮改了初始化兼容代码，所以它的标准类型是 `same_seed_repeat`（同种子复跑），并另外标记
`diagnostic_subtype: code_repair`（代码修复诊断）和 `not_confirmation_evidence: true`。
它不是原代码原配置一字不变的 `exact_repeat`，也不会被自动当作正式确认结果。

结果必须完整报告修复版五次的 U/S/H/ZS、mean、min、max 和 range，并同时比较：

- 老 V5 五次 H 均值 `74.462`、范围 `74.41–74.56`；
- 未修复干净 V5 五次 H 均值 `74.270`、范围 `74.12–74.48`；
- 修复版均值分别离上述两个均值多远。

“初始化是否修好”由第 1、2 步的活跃权重与随机状态逐元素相同决定；GPU 五次只回答最终
性能分布是否向老 V5 回归，不能再用“某一次超过 74.40”证明修复。若修复版均值没有更接近
老 V5，再启动一对同时期、同 GPU 波次的老 V5/修复版诊断，而不是无限追加任务。

## 本实验不改变什么

- CUB 数据、xlsa17 划分、类别顺序不变；
- 输入仍为 `[B（图片数量）, 577（1 个全局特征加 576 个局部块）, 768（特征维度）]`；
- `global + 0.2 × local` 不变；
- PSE、FGVD、BVSA、SGMP、ICSA 的活跃计算不变；
- 七项训练损失、优化器、学习率和 U/S/H/ZS 评估口径不变；
- 本实验不创建新正式框架，也不修改任何正式 Tag。

## 当前状态

零训练的本地失败测试已经先复现问题；最小修复后已转为通过。正式 GPU 结果尚未产生，
因此这里不能提前写“74.4 已复现”或“修复已恢复精度”。
