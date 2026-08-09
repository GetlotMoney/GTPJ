# ATTEMPT-006 Result

```text
result_type: trial_internal_mixed_probe_tune
source_campaign: CAMP-20260702-workflow-v2-2innov8tune
campaign_role: routing_index_only
run_id: RUN-20260702-0003-mixed2innov8tune-2gpu
jobs: 10 completed / 0 failed
confirmation_status: not_confirmed
evidence_state: tune_promising
```

## Boundary

This is the formal trial-local result record for the 10-run workflow-v2 mixed
experiment. The campaign directory is only a routing and monitoring index; it
must not be used as the authoritative source for H/U/S/ZS claims.

All jobs belong to IDEA-0003 / TRIAL-001 Dynamic Residual Routing.

## Workstream Summary

| Workstream | Count | Source type | Outcome |
|---|---:|---|---|
| Innovation probe | 2 | existing TRIAL-001 switch probes | stop_no_gain |
| Direction tune | 8 | trial-internal config search | tune_promising |

The two `INNOV-*` work items are not paper-derived innovations and did not open
a new Trial. They only test existing legal dynamic-routing switches.

## Best Single

| Work item | Runner job | Name | H | U | S | ZS | Seed |
|---|---|---|---:|---:|---:|---:|---:|
| TUNE-002 | DR-004 | `tune_direction_h48_w0.525_a0.003` | 74.75 | 72.90 | 76.69 | 81.96 | 5 |

## Interpretation

- Best result in this attempt: TUNE-002 / DR-004 at H=74.75.
- It supports the direction-gate region around hidden 48, `weight_s2v=0.50-0.525`,
  and `dynamic_gate_anchor_lambda=0.003-0.005`.
- It does not exceed ATTEMPT-004 DR-035 H=75.02.
- No result here is confirmed. A repeat or declared stability protocol is still required.

## Decision

```text
status: keep_as_trial_internal_evidence
result_status: tune_promising
promotion_decision: blocked
next_action: repeat top direction candidates under a declared repeat protocol
```
