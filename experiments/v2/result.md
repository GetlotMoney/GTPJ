# GTPJ-v2 Result

| Experiment | Dataset | Seed | U | S | H | ZS | Best epoch | Log artifact |
|---|---|---:|---:|---:|---:|---:|---:|---|
| `GTPJ-v2` | CUB GZSL | 5 | 71.32 | 77.52 | 74.29 | 81.59 | 33 | `log:v1:module_trial:TRIAL-001:attempt-019` |

```text
baseline: GTPJ-v1
baseline_H: 73.93
delta_H: +0.36
evidence_level: valid_single_run
best_observed_H: 74.29
confirmed_H: pending
confirmation_status: needs_confirmation
source_trial: experiments/module_trials/IDEA-0001_clip_a_self_text_prototype/TRIAL-001_clip_a_self_residual_seenonly
source_attempt: ATTEMPT-019
source_trial_run_commit: 453acc0
source_attempt_record_commit: 3a7945a
config: experiments/v2/config.yaml
```

`GTPJ-v2` is the owner-activated mainline code version from `TRIAL-001 / ATTEMPT-019`.
The `H=74.29` result is retained as `best_observed_H`; `confirmed_H` remains pending until
clean confirmation passes. Raw logs and checkpoints remain in Warehouse; GitHub records only
artifact identities, hashes, sizes, config, result, and quality evidence.
