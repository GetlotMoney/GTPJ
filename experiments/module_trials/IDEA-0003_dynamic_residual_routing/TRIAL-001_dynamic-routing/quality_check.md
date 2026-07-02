# TRIAL-001 Quality Check

```text
quality_check_mode: STRICT
attempt_id: ATTEMPT-004
decision: WARN_KEEP_NEEDS_REPEAT
promotion_decision: blocked
evidence_level: valid_single_run
```

## Findings

- Metrics are synchronized from `ATTEMPT-004` / `RUN-20260702-0002` DR-035: U=72.69, S=77.51, H=75.02, ZS=82.04, best_epoch=48.
- The workflow-v2 campaign `RUN-20260702-0003` supports the same direction-gate region but did not exceed DR-035; its best was DR-004 at H=74.75.
- Trial-level decision recorded as `keep`.
- Attempt confirmation status: confirmed_H=pending, confirmation_status=needs_confirmation.
- Promotion/tag remains blocked because ATTEMPT-004 DR-035 is still a best observed single, not min3 confirmed evidence.
- Raw artifacts remain in Warehouse; GitHub stores lightweight identities only.

## Artifact Check

- [x] `runtime:v5:module_trial:TRIAL-001:RUN-20260702-0002:summary` identity is recorded in the campaign final report.
- [x] `runtime:v5:module_trial:TRIAL-001:RUN-20260702-0002:summary_jsonl` identity is recorded in the campaign final report.
- [x] `runtime:v5:module_trial:TRIAL-001:RUN-20260702-0002:batch_status` identity is recorded in the campaign final report.
- [x] `runtime:v5:module_trial:TRIAL-001:RUN-20260702-0002:plan` identity is recorded in the campaign final report.
- [x] `runtime:v5:module_trial:TRIAL-001:RUN-20260702-0002:events` identity is recorded in the campaign final report.
- [x] `manifest.yaml`, `result.yaml`, and `result.md` point back to the attempt-local evidence.
- [x] No raw training log or checkpoint is copied into GitHub.
- [ ] ATTEMPT-004 min3 repeat is not complete.
- [ ] Full per-log audit and Top-3 checkpoint retention still need post-run closeout.

## Decision

WARN_KEEP_NEEDS_REPEAT.
