# CONFIRM-001_clean_seed5

```text
experiment_id: CONFIRM-001
version: v1
code_tag: v1
runtime: Codex
quality_check: quality_check.md
run_commit: c2571b0
config: config.yaml
log: logs/CONFIRM-001_CUB_seed5_20260620-202215.txt
status: done
```

## 问题

确认 `GTPJ-v1` 能在本仓库中用 `seed=5` 干净运行，并得到可作为后续调参、消融和模块 trial 对照的 CUB GZSL 基准结果。

## 运行前检查

- [x] 当前分支为 `exp/v1-confirm-001-clean-seed5`。
- [x] 配置使用 `experiments/v1/confirmation/CONFIRM-001_clean_seed5/config.yaml`。
- [x] 不修改模型代码、训练脚本或版本配置。
- [x] Quality check decision 为 `ACCEPTED`。
- [x] 环境 smoke check 通过：`torch.cuda.is_available() == True`，`clip` 可导入，CUB split、patch cache、GPT55 text cache 可读取。

## 运行计划

```text
branch: exp/v1-confirm-001-clean-seed5
command: F:\Anaconda\envs\dvsr_gpu\python.exe train_GTPJ_CUB.py --config experiments/v1/confirmation/CONFIRM-001_clean_seed5/config.yaml
python: F:\Anaconda\envs\dvsr_gpu\python.exe
dataset: CUB GZSL
seed: 5
device: cuda:0
data_source: local data junction to C:\Users\Administrator\Desktop\cv-work\DVSR\data
metadata_source: local junction data/xlsa17/data -> C:\Users\Administrator\Desktop\cv-work\DVSR\xlsa17\xlsa17\data
```

训练策略由 `config.yaml` 锁定。`lr_stages` 存在时，训练脚本会用分阶段策略覆盖单独的 `epochs` 字段：

```text
stage 1: lr=0.001, epochs=20, eta_min=1e-5
stage 2: lr=0.0001, epochs=20, eta_min=1e-6, restart_from_best=False
stage 3: lr=0.00001, epochs=10, eta_min=1e-7, restart_from_best=False
total_epochs: 50
amp: disabled by default
```

## 结果

| 数据集 | Seed | U | S | H | ZS | Best epoch | Log |
|---|---:|---:|---:|---:|---:|---:|---|
| CUB GZSL | 5 | 72.20 | 75.45 | 73.79 | 81.80 | 26 | `logs/CONFIRM-001_CUB_seed5_20260620-202215.txt` |

原始本地大文件产物：

```text
train_log/CUB/training_log_CUB_2026-06-20_20-22-15.txt
train_log/CUB/best_model_CUB_2026-06-20_20-22-15_H7379.pth
train_log/CUB/ckpt_full_CUB_2026-06-20_20-22-15.pth
```

## 结论

确认通过。当前 GTPJ-v1 在本仓库、当前本地数据/cache、seed=5、fp32、三阶段训练策略下可复现到 `H=73.79`。

这个结果与导入历史参考 `H=73.85` 相差 `-0.06`，属于可接受的复现误差范围。后续可以把 v1 当作当前主框架的正式 CUB seed=5 基准，再开始调参、消融或模块 trial。
