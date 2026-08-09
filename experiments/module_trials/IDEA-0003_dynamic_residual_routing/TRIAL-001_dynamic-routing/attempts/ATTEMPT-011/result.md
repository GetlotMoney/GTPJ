# ATTEMPT-011 Result

## 结论

ATTEMPT-011 已完成服务器 detached mixed200 campaign：4 个 batch 合计 200 jobs，全部 completed，0 failed，0 skipped。它提供了 H76 方向的候选来源，但不触发 promotion。

本轮最重要的事实是：`direction_sample h48` 仍是当前最值得复现的热点。最高单次为 `RUN-20260706-0001.../DR-042 direction_sample_h48_w0.515_a0.004`，H=75.00；另一个 supporting single 为 `RUN-20260706-0004.../DR-036 direction_sample_h48_w0.525_a0.002`，H=75.00。

## Repeat 边界

ATTEMPT-011 历史实际 repeat 是 top4 每个候选 seed=5 repeat 10 次；这是旧规则下的历史结果，不能作为以后新 profile 的模板。当前规则已经改成：严格复现必须 `repeat_type: exact_repeat`，不换 seed、不换任何参数；每个候选最多 5 次；只有达到对应 `restore_target_H` 才算还原。

| 候选 | seed | n | best H | mean H | min H | max H | range |
|---|---:|---:|---:|---:|---:|---:|---:|
| DR047 `direction_sample_h48_w0.535_a0.002` | 5 | 10 | 74.87 | 74.630 | 74.41 | 74.87 | 0.46 |
| DR020 `direction_sample_h48_w0.525_a0.003` | 5 | 10 | 74.83 | 74.606 | 74.42 | 74.83 | 0.41 |
| DR041 `direction_sample_h48_w0.515_a0.002` | 5 | 10 | 74.72 | 74.598 | 74.45 | 74.72 | 0.27 |
| DR051 `direction_sample_h48_w0.545_a0.004` | 5 | 10 | 74.75 | 74.524 | 74.29 | 74.75 | 0.46 |

这些 repeat 支持“h48 小 anchor 区域有持续信号”，但没有生成稳定 75+ promotion 证据。

## ATTEMPT-014 候选来源

下一步复现实验应从 ATTEMPT-011 的纯 `direction_sample + h48 + fixed local/ICSA/PSE` source single 中选 20 个候选，每个最多 5 次 exact repeat，总计 100 jobs。每个候选必须使用原 seed=5、原配置和自己的 `restore_target_H=source_H`。

前置候选已经写入 `result.yaml` 的 `attempt014_source_candidates`。原始服务器明细不进入 GitHub；正式引用时使用 `result.yaml` 中的 source id、server run/job 和 artifact hash。

## Artifact

服务器运行目录：

```text
lab4090:/data/lby/projects/cv_project/GTPJ/.gtpj_runtime/batches/
```

四个 batch 的 `summary.csv`、`summary.jsonl`、`batch_status.json`、`events.jsonl` 和 `plan.json` 的 sha256/size 已写入 `result.yaml`。

## Decision

- evidence_state: `tune_promising`
- promotion_decision: `blocked`
- next_action: 创建 ATTEMPT-014，做 100-job strict exact-repeat restore campaign。
