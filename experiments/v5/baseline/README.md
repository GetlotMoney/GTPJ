# GTPJ-v5 Baseline Evidence

```text
version: v5
source_experiment: RUN-20260630-0002-trial003-main100-2gpu
source_candidate: trial003-main100-069
status: owner_activated_provisional
evidence_level: confirmation_grade
best_observed_H: 74.54
confirmed_H: 74.44
confirmation_status: owner_activated_provisional
promotion_decision: blocked
owner_activation_decision: owner_activate
promote_to: v5
active_main_update: activated
```

This directory records the lightweight evidence for the owner-activated `GTPJ-v5` tag. Raw logs, receipts, checkpoints, and full runtime outputs remain in Warehouse and are referenced through `manifest.yaml`.

`GTPJ-v5` activates TRIAL-003 and freezes the best source config from the 100-run batch:

```text
bvsa_text_mode: conditional
sgmp_text_mode: conditional
jepa_text_mode: conditional
pse_outer_ratio: 0.65
clip_a_self_outer_ratio: 0.65
local_weight: 0.2
```

The active mainline now routes `all_text_cond` into BVSA, including the BVSA local score branch. The evidence is useful for future tuning, but the repeat mean does not exceed `GTPJ-v4 confirmed_H=74.47`.
