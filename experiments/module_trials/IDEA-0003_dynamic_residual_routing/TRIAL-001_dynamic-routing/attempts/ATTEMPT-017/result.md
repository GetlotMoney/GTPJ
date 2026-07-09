# ATTEMPT-017 Result

当前状态：completed。

本轮是 `server_frozen_runner` 的 `h76-escape100-supported-routing` 调参/窄消融批次，不是 confirmation。服务器运行完成后，本地已同步 `batch_status.json`、`summary.csv`、`summary.jsonl`、`events.jsonl` 和 `ATTEMPT017_SERVER_STATUS.json`。

## 完成状态

- run_id: `RUN-20260709-0001-h76-escape100-supported-routing-server-frozen-2gpu`
- completed: 100
- failed: 0
- skipped: 0
- running: 0
- pending: 0
- screen: supervisor 完成后正常退出
- GPU: GPU0/GPU1 空闲

## Top Single

| rank | job_id | name | H | U | S | ZS | best_epoch |
|---:|---|---|---:|---:|---:|---:|---:|
| 1 | DR-095 | `a015dr035_weight_plus_0.01` | 75.11 | 73.00 | 77.36 | 82.12 | 48 |
| 2 | DR-022 | `a015ridge_direction_sample_h48_w0.512_a0.00265` | 74.92 | 72.90 | 77.06 | 81.98 | 37 |
| 3 | DR-025 | `a015ridge_direction_sample_h48_w0.5165_a0.00215` | 74.90 | 72.49 | 77.48 | 81.82 | 48 |
| 4 | DR-018 | `a015dr035_direction_sample_h48_w0.528_a0.00385` | 74.86 | 73.07 | 76.73 | 81.92 | 37 |
| 5 | DR-021 | `a015ridge_direction_sample_h48_w0.512_a0.00215` | 74.86 | 72.56 | 77.31 | 81.88 | 50 |

## DR-095 复现候选

DR-095 是本轮唯一 H>=75 的 best single。它只能作为 `valid_single_run` / `tune_promising` 候选，不能写成 restored、confirmed 或 promotion evidence。

exact repeat 复现规则如下：

```yaml
source_candidate_id: A017DR095
source_job_id: DR-095
repeat_type: exact_repeat
original_seed: 5
restore_target_H: 75.11
max_attempts: 5
max_attempts_hard_cap: true
early_stop_on_best_hit: true
near_miss_tolerance_H: 0.2
near_miss_not_restored: true
config_updates:
  use_dynamic_routing: true
  dynamic_local_mode: fixed
  dynamic_icsa_mode: fixed
  dynamic_direction_mode: sample
  dynamic_pse_mode: fixed
  dynamic_gate_hidden: 48
  dynamic_gate_anchor_lambda: 0.0035
  weight_s2v: 0.535
  random_seed: 5
```

## Decision

- result_state: completed
- evidence_level: valid_single_run
- confirmation_decision: not_confirmation_evidence
- promotion_decision: blocked
- next_action: 以 DR-095 原配置和原 seed 做最多 5 次 exact_repeat，达到 H>=75.11 即停止。
