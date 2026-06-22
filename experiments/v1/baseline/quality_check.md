# Quality Check

```text
runtime: local archive
decision: ACCEPTED
```

## 范围

- 确认 `GTPJ-v1` 第一版基准配置。
- 确认当前 baseline 使用 `conditional_text_ratio=0.008`。
- 不修改模型代码、训练脚本、数据划分、评估逻辑或损失结构。

## 发现

- 任务口径：CUB GZSL，seed=5。
- 训练契约：SGDR 20+20+10，三个 stage 均设置非零 `eta_min`，后两段 `restart_from_best=False`。
- 结果：U=72.36、S=75.57、H=73.93、ZS=81.62，best epoch=26。
- 配置副本保存在 `experiments/v1/baseline/config.yaml`。
- 日志副本保存在 `experiments/v1/baseline/logs/GTPJ-v1_CUB_seed5_20260613-145232.txt`。

## 决策

ACCEPTED
