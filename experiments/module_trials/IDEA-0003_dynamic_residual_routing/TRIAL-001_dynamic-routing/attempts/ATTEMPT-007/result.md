# ATTEMPT-007 Result

Status: `confirmed_candidate`.

This is the strict same-seed min3 exact repeat of ATTEMPT-004 DR-035. It confirms a stable repeat cluster for the DR-035 configuration, but it does not auto-promote a new version.

## Target

| Source | Job | Config | Seed | U | S | H | ZS | Best epoch |
|---|---|---|---:|---:|---:|---:|---:|---:|
| ATTEMPT-004 | DR-035 | `direction_sample_h48_w0.525_a0.005` | 5 | 72.69 | 77.51 | 75.02 | 82.04 | 48 |

## Exact Repeats

| Job | Name | Seed | U | S | H | ZS | Best epoch | Status |
|---|---|---:|---:|---:|---:|---:|---:|---|
| DR-001 | `dr035_direction_sample_h48_w0.525_a0.005_s5_r1` | 5 | 72.02 | 77.32 | 74.58 | 81.78 | 48 | completed |
| DR-002 | `dr035_direction_sample_h48_w0.525_a0.005_s5_r2` | 5 | 73.27 | 76.01 | 74.62 | 81.92 | 37 | completed |
| DR-003 | `dr035_direction_sample_h48_w0.525_a0.005_s5_r3` | 5 | 72.46 | 76.92 | 74.62 | 81.75 | 48 | completed |

## Gate

| Check | Threshold | Observed | Pass |
|---|---:|---:|---|
| mean H | >= 74.60 | 74.61 | yes |
| min H | >= 74.45 | 74.58 | yes |
| range H | <= 0.50 | 0.04 | yes |

Mean U/S/ZS: U=72.58, S=76.75, ZS=81.82.

## Evidence

- Runtime batch: `lab4090:/data/lby/projects/cv_project/GTPJ/.gtpj_runtime/batches/RUN-20260703-0002-dr035-exact-repeat-s5-min3-2gpu`
- Dedicated warehouse: `lab4090:/data/lby/projects/cv_project/GTPJ_Warehouse/runs/v5/module_trial/TRIAL-001/ATTEMPT-007/RUN-20260703-0002-dr035-exact-repeat-s5-min3-2gpu`
- Dedicated warehouse size: 308,806,238 bytes.
- Hash manifest: `SHA256SUMS.txt`.

## Warnings

- The generated dynamic runner kept top-level `batch_status.status` as `planned`; job-level statuses, `summary.csv/jsonl`, and `events.jsonl` show 3/3 completed and are the authoritative runtime evidence.
- The runner's default `warehouse_dir` values point to shared historical `attempt-001/002/003` folders. To avoid retention ambiguity, current ATTEMPT-007 logs/configs/checkpoints were copied to the dedicated warehouse path above.

## Decision

`confirmed_candidate`; promotion remains blocked.
