# GTPJ-v1 结果

状态：已完成本仓库干净复现。

## 正式结果

| 实验 | 数据集 | Seed | U | S | H | ZS | Best epoch | Log |
|---|---|---:|---:|---:|---:|---:|---:|---|
| `CONFIRM-001_clean_seed5` | CUB GZSL | 5 | 72.20 | 75.45 | 73.79 | 81.80 | 26 | `experiments/v1/confirmation/CONFIRM-001_clean_seed5/logs/CONFIRM-001_CUB_seed5_20260620-202215.txt` |

## 导入参考值

这个值只用于定位方向。它不是正式 GTPJ 结果。

| 数据集 | Seed | U | S | H | ZS | Best epoch |
|---|---:|---:|---:|---:|---:|---:|
| CUB GZSL | 5 | 71.46 | 76.40 | 73.85 | 81.61 | 41 |

## 结论

本仓库正式复现结果 `H=73.79`，与导入参考 `H=73.85` 相差 `-0.06`。当前 v1 可以作为后续模块 trial、调参和消融的主框架对照。
