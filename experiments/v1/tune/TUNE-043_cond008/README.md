# TUNE-043_cond008

```text
experiment_id: TUNE-043
version: v1
code_tag: v1
source_project: C:\Users\Administrator\Desktop\cv-work\DVSR-workflow-governance
source_experiment: experiments/04_hyperparameter_tuning/v1/TUNE-043_cond008
runtime: Codex
config: config.yaml
log: logs/TUNE-043_CUB_seed5_20260613-145232.txt
status: done
```

## 问题

登记 `GTPJ-v1` 第一版正式 baseline：在当前主框架中使用 `conditional_text_ratio=0.008`，记录 CUB GZSL 主指标。

## 关键配置

| 参数 | 值 |
|---|---:|
| `conditional_text_ratio` | 0.008 |

训练契约保持一致：

```text
stage 1: lr=0.001, epochs=20, eta_min=1e-5
stage 2: lr=0.0001, epochs=20, eta_min=1e-6, restart_from_best=False
stage 3: lr=0.00001, epochs=10, eta_min=1e-7, restart_from_best=False
total_epochs: 50
```

## 结果

| 数据集 | Seed | U | S | H | ZS | Best epoch | Log |
|---|---:|---:|---:|---:|---:|---:|---|
| CUB GZSL | 5 | 72.36 | 75.57 | 73.93 | 81.62 | 26 | `logs/TUNE-043_CUB_seed5_20260613-145232.txt` |

## 结论

`conditional_text_ratio=0.008` 对应 CUB seed=5 `H=73.93`。该结果与当前 GTPJ v1 训练契约一致，因此作为 `GTPJ-v1` 第一版正式 baseline。

注意：该实验最初产生于本地归档实验，本目录保存了配置、结果和日志副本，作为 GTPJ 第一版 baseline 的证据。
