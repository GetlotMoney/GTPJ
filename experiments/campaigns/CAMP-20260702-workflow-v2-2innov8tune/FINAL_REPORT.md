# Final Report

```text
campaign_id: CAMP-20260702-workflow-v2-2innov8tune
campaign_run: RUN-20260702-0003-mixed2innov8tune-2gpu
related_prior_run: RUN-20260702-0002-dr018-confirm-ablate50-2gpu
trial: IDEA-0003 / TRIAL-001 Dynamic Residual Routing
evidence_level: single_run_valid / tune_promising
confirmation_status: needs_min3_repeat
promotion_decision: blocked
```

## Integrated View

| Source | Run | Best job | Group | Key config | H | U | S | ZS | Best epoch | Evidence state |
|---|---|---|---|---|---:|---:|---:|---:|---:|---|
| ATTEMPT-003 | `RUN-20260701-0010-dynroute-bs64-repro-tune50-2gpu` | DR-018 | direction tune | `direction_sample_h48_w0.5_a0.003` | 74.86 | 73.10 | 76.71 | 81.84 | 37 | `tune_promising`, needs confirmation |
| ATTEMPT-004 | `RUN-20260702-0002-dr018-confirm-ablate50-2gpu` | DR-035 | direction narrow tune | `direction_sample_h48_w0.525_a0.005` | 75.02 | 72.69 | 77.51 | 82.04 | 48 | best observed single |
| ATTEMPT-004 | `RUN-20260702-0002-dr018-confirm-ablate50-2gpu` | DR-009 | neighbor repeat | `dr016_direction_sample_h48_w0.45_a0.003_r02` | 75.00 | 72.93 | 77.19 | 81.95 | 48 | supporting single |
| Workflow-v2 campaign | `RUN-20260702-0003-mixed2innov8tune-2gpu` | DR-004 | direction tune | `tune_direction_h48_w0.525_a0.003` | 74.75 | 72.90 | 76.69 | 81.96 | 37 | repeat candidate |
| Workflow-v2 campaign | `RUN-20260702-0003-mixed2innov8tune-2gpu` | DR-006 | direction tune | `tune_direction_h48_w0.50_a0.005` | 74.67 | 72.29 | 77.21 | 81.62 | 48 | repeat candidate |
| Workflow-v2 campaign | `RUN-20260702-0003-mixed2innov8tune-2gpu` | DR-010 | direction tune | `tune_direction_h48_w0.45_a0.004` | 74.64 | 72.43 | 76.98 | 81.62 | 50 | backup repeat candidate |

## Interpretation

- The best current dynamic-routing family is `direction_sample` with `dynamic_gate_hidden=48`.
- The strongest observed single is ATTEMPT-004 DR-035 at H=75.02, using `weight_s2v=0.525` and `dynamic_gate_anchor_lambda=0.005`.
- The workflow-v2 10-run campaign did not exceed DR-035, but it supports the same direction-gate region: `w=0.45-0.525`, `anchor_lambda=0.003-0.005`, hidden 48.
- The two workflow-v2 innovation probes underperformed: DR-001 H=73.62 and DR-002 H=73.63. They are stopped for this campaign unless a new hypothesis or attachment point is proposed.
- No result in this report is `confirmed_H`. All top values remain single-run or support singles until min3 repeat and quality checks are complete.

## Agent Decisions

Result Comparator:

```text
decision: warn
repeat_candidates: DR-004, DR-006, DR-010
innovation_probes: stop_no_gain / revise
promotion: blocked
```

Evidence Quality Checker:

```text
decision: warn
confirmed_results: none
required_before_promotion: min3 repeat, artifact identity, GZSL rule_checks, log checks, checkpoint retention
```

## Repeat Routing

Priority repeat set:

| Priority | Candidate | Reason |
|---:|---|---|
| 1 | ATTEMPT-004 DR-035 `direction_sample_h48_w0.525_a0.005` | Highest observed H=75.02; must be tested for stability. |
| 2 | Workflow-v2 DR-004 `tune_direction_h48_w0.525_a0.003` | Best in the 10-run workflow-v2 campaign; close to the same weight region. |
| 3 | ATTEMPT-004 DR-009 `dr016_direction_sample_h48_w0.45_a0.003_r02` | H=75.00 supporting neighbor evidence. |
| 4 | Workflow-v2 DR-006 `tune_direction_h48_w0.50_a0.005` | Good seen score and same anchor family; backup repeat. |

Default next action: run min3 repeat for DR-035 first. If budget allows, include DR-004 and DR-006 as neighbor stability checks.

## Artifact Pointers

| Run | File | Size bytes | sha256 |
|---|---|---:|---|
| `RUN-20260702-0002-dr018-confirm-ablate50-2gpu` | `summary.csv` | 17040 | `76577412219e35c4757d486da1496e55a2f2980e4816871cb92b8191130b9ab8` |
| `RUN-20260702-0002-dr018-confirm-ablate50-2gpu` | `summary.jsonl` | 42099 | `3a56552e462894db2f068a16397d9ee99bbcb7e1266164ae2b32f63d4592fee8` |
| `RUN-20260702-0002-dr018-confirm-ablate50-2gpu` | `batch_status.json` | 38310 | `7b6636ee81545a2132dec62147d1be17c94194f38f2fed01cc58bd4258d12e9f` |
| `RUN-20260702-0002-dr018-confirm-ablate50-2gpu` | `plan.json` | 30903 | `1d60916386d7008b511d1221e004c6fb97cbebee1f89fed1be16e2d9d1061726` |
| `RUN-20260702-0002-dr018-confirm-ablate50-2gpu` | `events.jsonl` | 19201 | `bd5cfbad128a353b8574a0e35c8fd8c11749cc5172452885ffb286e379cbbf0a` |
| `RUN-20260702-0003-mixed2innov8tune-2gpu` | `summary.csv` | 3427 | `5a4aa2fdb2df56aeb50b4d47bac61d0ae492c7b9c019ae3b8e0aac30b4ae59a1` |
| `RUN-20260702-0003-mixed2innov8tune-2gpu` | `summary.jsonl` | 8491 | `29cd157adc4a3fbceea89aab1e7ba704e41d2fc30bff8fc9ac2495bb91191758` |
| `RUN-20260702-0003-mixed2innov8tune-2gpu` | `batch_status.json` | 7691 | `6ef61bd94e64e7b6f4c3b16ede2cfb30aa57af2b2a6a8701c9302d95bd9c0d9b` |
| `RUN-20260702-0003-mixed2innov8tune-2gpu` | `plan.json` | 7263 | `a4aae1f591ba9f7c27b1dd799d01cd96be4945ef09100bc0db66e96c94b2db4e` |
| `RUN-20260702-0003-mixed2innov8tune-2gpu` | `events.jsonl` | 3841 | `09fd01babdce78a4d23baeaf80e484cfb7d8133dd1a58bf8c8d9077d1e44f05d` |

Server root:

```text
lab4090:/data/lby/projects/cv_project/GTPJ/.gtpj_runtime/batches/
```

Warehouse root:

```text
lab4090:/data/lby/projects/cv_project/GTPJ_Warehouse/runs/v5/module_trial/TRIAL-001/
```
