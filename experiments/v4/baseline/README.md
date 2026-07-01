# GTPJ-v4 Baseline Evidence

```text
version: v4
source_experiment: experiments/v3/confirmation/CONFIRM-001_local_v3_054_min3
source_candidate: local-v3-054
status: confirmed
evidence_level: baseline_grade
best_observed_H: 74.47
confirmed_H: 74.47
H_mean: 74.45
confirmation_status: confirmed
promotion_decision: promote
promote_to: v4
```

This directory records the lightweight evidence for the confirmed `GTPJ-v4` tag. Raw logs, receipts, and checkpoint files remain in Warehouse and are referenced through `manifest.yaml` and the source confirmation manifest.

`GTPJ-v4` keeps the v3 model/training code path and promotes only the confirmed tuned configuration:

```text
pse_outer_ratio: 0.5
clip_a_self_outer_ratio: 0.5
local_weight: 0.1
```

The owner standing rule from 2026-06-29 treats 3 clean successful repeats with H metrics as reproducible enough for automatic promotion to a formal version. After the min3 cluster passes, the formal result uses the highest successful repeat (`confirmed_H=74.47`) and records the repeat mean (`H_mean=74.45`) as stability evidence. This does not imply `activate-version`.
