# ATTEMPT-013 Result

最终状态：`stopped_invalid_confirmation_scope`。服务器 batch 已收口为 44 completed / 0 failed / 6 skipped / 0 running / 0 pending，`batch_status=completed_with_skips`。

这轮不能算“复现实验”。它实际是 `repeat_type: multi_seed_stability` / seed sweep：候选使用 seeds 6-15，未保留 `original_seed`，因此必须写 `not_confirmation_evidence: true`。严格复现必须是 `repeat_type: exact_repeat`、原配置、原 seed、`max_attempts: 5`、`early_stop_on_best_hit: true`、`restore_target_H` 预声明；只有 clean repeat 达到 `restore_target_H` 才能停止。接近但未达到只能写 `near_miss_not_restored`，表示有效果、还有希望。

最高单次为 `DR-028 dr041_direction_sample_h48_w0.515_a0.002_s13`，H=74.53，未出现 H>=75。该 run 只保留为错误口径边界和稳定性诊断，不允许作为 keep / best / confirmation / promotion evidence。

## Run

- run_id: `RUN-20260707-0001-h76-followup50-live-multiagent-2gpu`
- server_batch_dir: `/data/lby/projects/cv_project/GTPJ/.gtpj_runtime/batches/RUN-20260707-0001-h76-followup50-live-multiagent-2gpu`
- profile: `h76-followup50-multiseed`
- jobs: 50
- latest check: 44 completed, 0 failed, 6 skipped, 0 running, 0 pending
- stop_requested_at: `2026-07-07T21:49+08:00`

## Partial Summary

| Job | Candidate | Seed | H | U | S | ZS |
|---|---|---:|---:|---:|---:|---:|
| `DR-002` | `DR047 direction_sample_h48_w0.535_a0.002` | 7 | 74.19 | 71.42 | 77.19 | 81.55 |
| `DR-001` | `DR047 direction_sample_h48_w0.535_a0.002` | 6 | 73.96 | 70.98 | 77.21 | 81.27 |
| `DR-003` | `DR047 direction_sample_h48_w0.535_a0.002` | 8 | 73.96 | 70.58 | 77.68 | 81.59 |
| `DR-004` | `DR047 direction_sample_h48_w0.535_a0.002` | 9 | 73.89 | 71.47 | 76.47 | 81.25 |
| `DR-005` | `DR047 direction_sample_h48_w0.535_a0.002` | 10 | 74.05 | 72.05 | 76.16 | 81.04 |
| `DR-006` | `DR047 direction_sample_h48_w0.535_a0.002` | 11 | 74.08 | 71.12 | 77.30 | 80.90 |
| `DR-007` | `DR047 direction_sample_h48_w0.535_a0.002` | 12 | 74.32 | 71.48 | 77.40 | 81.50 |
| `DR-008` | `DR047 direction_sample_h48_w0.535_a0.002` | 13 | 74.37 | 72.71 | 76.11 | 81.52 |
| `DR-009` | `DR047 direction_sample_h48_w0.535_a0.002` | 14 | 74.32 | 71.56 | 77.30 | 81.49 |
| `DR-010` | `DR047 direction_sample_h48_w0.535_a0.002` | 15 | 74.20 | 71.38 | 77.25 | 80.93 |
| `DR-011` | `DR020 direction_sample_h48_w0.525_a0.003` | 6 | 73.90 | 70.99 | 77.06 | 80.94 |
| `DR-012` | `DR020 direction_sample_h48_w0.525_a0.003` | 7 | 74.29 | 71.48 | 77.33 | 81.58 |
| `DR-013` | `DR020 direction_sample_h48_w0.525_a0.003` | 8 | 74.23 | 71.12 | 77.62 | 81.51 |
| `DR-014` | `DR020 direction_sample_h48_w0.525_a0.003` | 9 | 74.20 | 71.64 | 76.95 | 81.66 |
| `DR-015` | `DR020 direction_sample_h48_w0.525_a0.003` | 10 | 74.00 | 71.35 | 76.85 | 81.03 |
| `DR-016` | `DR020 direction_sample_h48_w0.525_a0.003` | 11 | 73.97 | 71.01 | 77.18 | 80.87 |
| `DR-017` | `DR020 direction_sample_h48_w0.525_a0.003` | 12 | 74.22 | 72.04 | 76.54 | 81.56 |
| `DR-018` | `DR020 direction_sample_h48_w0.525_a0.003` | 13 | 74.20 | 71.08 | 77.60 | 81.78 |
| `DR-019` | `DR020 direction_sample_h48_w0.525_a0.003` | 14 | 74.19 | 72.43 | 76.04 | 81.58 |
| `DR-020` | `DR020 direction_sample_h48_w0.525_a0.003` | 15 | 74.11 | 72.03 | 76.31 | 81.32 |
| `DR-021` | `DR041 direction_sample_h48_w0.515_a0.002` | 6 | 74.00 | 71.50 | 76.67 | 81.10 |
| `DR-022` | `DR041 direction_sample_h48_w0.515_a0.002` | 7 | 74.22 | 71.50 | 77.15 | 81.59 |
| `DR-023` | `DR041 direction_sample_h48_w0.515_a0.002` | 8 | 74.16 | 71.10 | 77.50 | 81.49 |
| `DR-024` | `DR041 direction_sample_h48_w0.515_a0.002` | 9 | 74.07 | 73.18 | 74.99 | 81.62 |
| `DR-025` | `DR041 direction_sample_h48_w0.515_a0.002` | 10 | 74.02 | 71.45 | 76.77 | 80.90 |
| `DR-026` | `DR041 direction_sample_h48_w0.515_a0.002` | 11 | 73.66 | 71.60 | 75.83 | 80.53 |
| `DR-027` | `DR041 direction_sample_h48_w0.515_a0.002` | 12 | 74.06 | 72.16 | 76.05 | 81.55 |
| `DR-028` | `DR041 direction_sample_h48_w0.515_a0.002` | 13 | 74.53 | 71.89 | 77.36 | 81.58 |
| `DR-029` | `DR041 direction_sample_h48_w0.515_a0.002` | 14 | 74.27 | 73.01 | 75.58 | 81.45 |
| `DR-030` | `DR041 direction_sample_h48_w0.515_a0.002` | 15 | 74.28 | 71.24 | 77.59 | 81.06 |
| `DR-031` | `A011DR042 direction_sample_h48_w0.515_a0.004` | 6 | 74.26 | 71.17 | 77.63 | 81.40 |
| `DR-032` | `A011DR042 direction_sample_h48_w0.515_a0.004` | 7 | 74.26 | 71.32 | 77.46 | 81.45 |
| `DR-033` | `A011DR042 direction_sample_h48_w0.515_a0.004` | 8 | 74.13 | 70.75 | 77.85 | 81.45 |
| `DR-034` | `A011DR042 direction_sample_h48_w0.515_a0.004` | 9 | 73.96 | 71.66 | 76.41 | 81.34 |
| `DR-035` | `A011DR042 direction_sample_h48_w0.515_a0.004` | 10 | 73.80 | 71.93 | 75.77 | 81.01 |
| `DR-036` | `A011DR042 direction_sample_h48_w0.515_a0.004` | 11 | 74.08 | 71.16 | 77.25 | 80.85 |
| `DR-037` | `A011DR042 direction_sample_h48_w0.515_a0.004` | 12 | 73.93 | 71.86 | 76.12 | 81.49 |
| `DR-038` | `A011DR042 direction_sample_h48_w0.515_a0.004` | 13 | 74.30 | 72.33 | 76.39 | 81.72 |
| `DR-039` | `A011DR042 direction_sample_h48_w0.515_a0.004` | 14 | 74.20 | 71.73 | 76.84 | 81.72 |
| `DR-040` | `A011DR042 direction_sample_h48_w0.515_a0.004` | 15 | 74.03 | 71.55 | 76.69 | 81.10 |

当前 best single 是 `DR-028`，H=74.53。DR047 seed 6-15 mean H=74.134，min H=73.89，max H=74.37，range H=0.48。该候选没有 75+ 命中，也不能支持稳定 75+ 结论。

DR020 已完整完成 seed 6-15，mean H=74.131，min H=73.90，max H=74.29，range H=0.39。该候选没有 75+ 命中，也不能支持稳定 75+ 结论。

DR041 已完整完成 seed 6-15，mean H=74.127，min H=73.66，max H=74.53，range H=0.87，没有 75+ 命中，不能支持稳定 75+ 结论。

A011DR042 已完整完成 seed 6-15，mean H=74.095，min H=73.80，max H=74.30，range H=0.50，没有 75+ 命中，不能支持稳定 75+ 结论。

A011DR020 已开始运行，当前 seed 6/7 正在 GPU0/GPU1 上训练，尚未产生 completed 结果。

## Planned Work

- 5 candidates
- seeds 6-15
- 50 planned jobs

## Boundary

`ATTEMPT-012` partial output 不进入本轮正式结论。Promotion 保持 blocked，直到 ATTEMPT-013 完整跑完并补齐 summary、quality 和 result analysis。
