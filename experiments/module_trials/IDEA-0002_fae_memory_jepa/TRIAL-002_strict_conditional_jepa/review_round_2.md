# Innovation Review Round 2: Post-Run Evidence

```text
review_round: Review 3
scope: post-run evidence review
activation_mode: real_multi_agent
attempt_id: ATTEMPT-006
decision: not_confirmed
promotion_decision: blocked
evidence_level: valid_single_run
```

## Inputs Checked

- `attempts/ATTEMPT-006/manifest.yaml`
- `attempts/ATTEMPT-006/result.yaml`
- `attempts/ATTEMPT-006/result.md`
- `attempts/ATTEMPT-006/quality_check.md`
- `ATTEMPTS.md`
- `manifest.yaml`
- `result.yaml`
- `result.md`
- `quality_check.md`
- Warehouse artifact identities below

## Review 3 Findings

- Metrics synchronized from `ATTEMPT-006`: U=71.29, S=76.73, H=73.91, ZS=81.52, best_epoch=42.
- Base version: `v2`.
- Code commit / pre-run freeze: `59e8cd7`.
- Command: `conda run --no-capture-output -n dvsr_gpu python train_GTPJ_CUB.py --config experiments/module_trials/IDEA-0002_fae_memory_jepa/TRIAL-002_strict_conditional_jepa/attempts/ATTEMPT-006/config.yaml`.
- Trial decision: `not_confirmed`.
- Promotion decision: `blocked`.
- Evidence level: `valid_single_run`.
- Boundary check: raw artifacts remain in Warehouse; GitHub records lightweight ids, URIs, sha256, and size only.

## Artifact Refs

- `log:v2:module_trial:TRIAL-002:attempt-006` -> `warehouse://gtpj/runs/v2/module_trial/TRIAL-002/attempt-006/logs/training_log_CUB_2026-06-28_22-12-57.txt`
- `checkpoint:v2:module_trial:TRIAL-002:attempt-006:best` -> `warehouse://gtpj/runs/v2/module_trial/TRIAL-002/attempt-006/checkpoints/best_model_CUB_2026-06-28_22-12-57_H7391.pth`
- `checkpoint:v2:module_trial:TRIAL-002:attempt-006:full` -> `warehouse://gtpj/runs/v2/module_trial/TRIAL-002/attempt-006/checkpoints/ckpt_full_CUB_2026-06-28_22-12-57.pth`
- `receipt:v2:module_trial:TRIAL-002:attempt-006:runner_console` -> `warehouse://gtpj/runs/v2/module_trial/TRIAL-002/attempt-006/receipts/stdout_ATTEMPT-006.log`

## Blocking Issues

None recorded by automated closeout for `ATTEMPT-006`.

## Decision

`not_confirmed`
