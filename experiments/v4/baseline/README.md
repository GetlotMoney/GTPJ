# GTPJ-v4 Baseline Evidence

```text
version: v4
source_experiment: experiments/v3/confirmation/CONFIRM-001_local_v3_054_min3
source_candidate: local-v3-054
status: legacy_config_only_not_framework_version
evidence_level: baseline_grade
best_observed_H: 74.47
confirmed_H: 74.47
H_mean: 74.45
confirmation_status: confirmed
promotion_decision: confirmed_config_only
promote_to:
```

This directory records the lightweight evidence for the historical `GTPJ-v4` config-only tag. Raw logs, receipts, and checkpoint files remain in Warehouse and are referenced through `manifest.yaml` and the source confirmation manifest.

`GTPJ-v4` keeps the v3 model/training code path and records only the confirmed tuned configuration:

```text
pse_outer_ratio: 0.5
clip_a_self_outer_ratio: 0.5
local_weight: 0.1
```

The owner standing rule treats 3 clean successful repeats with H metrics as reproducible enough for a confirmed config/reference. After the min3 cluster passes, the confirmed row uses the highest successful repeat (`confirmed_H=74.47`) and records the repeat mean (`H_mean=74.45`) as stability evidence. Because this is pure tuning, it is not a formal framework version and does not imply `activate-version`.
