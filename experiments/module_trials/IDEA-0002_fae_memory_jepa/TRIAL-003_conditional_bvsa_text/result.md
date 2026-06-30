# TRIAL-003 Result

```text
trial_id: TRIAL-003
decision: owner_activated_to_v5
evidence_level: confirmation_grade
best_observed_H: 74.54
confirmed_H: 74.44
confirmation_status: owner_activated_provisional
source_run: RUN-20260630-0002-trial003-main100-2gpu
source_candidate: trial003-main100-069
promote_to: v5
```

TRIAL-003 verifies the owner-requested path:

```text
all_text_cond [B, C, 768] -> BVSA -> local_score [B, C]
```

The best single observed frozen repeat is `trial003-main100-095` with `H=74.54`. The frozen-repeat mean for jobs 091-095 is `H=74.44`, so the result is used as the owner-selected active mainline rather than as a stronger confirmed reference over `GTPJ-v4 confirmed_H=74.45`.
