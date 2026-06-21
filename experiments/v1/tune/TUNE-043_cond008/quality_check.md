# Quality Check

```text
runtime: Codex
decision: ACCEPTED
```

## 范围

- 核对 `TUNE-043_cond008` 是否可以作为 `GTPJ-v1` 第一版正式 baseline 配置。
- 确认当前 baseline 使用 `conditional_text_ratio=0.008`。
- 不修改模型代码、训练脚本、数据划分、评估逻辑或损失结构。

## 发现

- `TUNE-043` 与当前 GTPJ v1 使用相同主框架、同一 CUB GZSL 任务、同一 seed=5 对照口径。
- 训练契约一致：SGDR 20+20+10，三个 stage 均设置非零 `eta_min`，后两段 `restart_from_best=False`。
- 结果为 U=72.36、S=75.57、H=73.93、ZS=81.62，best epoch=26。
- 实际 `TUNE-043_cond008/config.yaml` 中 `lambda_jepa_neg=0.01`，本次以实验目录配置为准。

## 决策

ACCEPTED
