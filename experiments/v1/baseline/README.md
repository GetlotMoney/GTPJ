# GTPJ-v1 Baseline

```text
version: v1
code_tag: v1
baseline_name: GTPJ-v1
dataset: CUB GZSL
seed: 5
config: config.yaml
log: logs/GTPJ-v1_CUB_seed5_20260613-145232.txt
status: accepted
```

## 目的

记录新仓库第一版正式基准。这个目录不是一次调参实验目录，而是 `GTPJ-v1`
的基准证据目录。

## 关键配置

| 参数 | 值 |
|---|---:|
| `conditional_text_ratio` | 0.008 |

训练契约：

```text
stage 1: lr=0.001, epochs=20, eta_min=1e-5
stage 2: lr=0.0001, epochs=20, eta_min=1e-6, restart_from_best=False
stage 3: lr=0.00001, epochs=10, eta_min=1e-7, restart_from_best=False
total_epochs: 50
```

## 结果

| 数据集 | Seed | U | S | H | ZS | Best epoch | Log |
|---|---:|---:|---:|---:|---:|---:|---|
| CUB GZSL | 5 | 72.36 | 75.57 | 73.93 | 81.62 | 26 | `logs/GTPJ-v1_CUB_seed5_20260613-145232.txt` |

## 结论

`GTPJ-v1` 的 CUB seed=5 基准为 `H=73.93`。后续模块 trial、调参、
消融和跨数据集实验都以这个版本配置和结果作为第一版对照。
