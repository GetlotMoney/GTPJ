# Innovation Review Round 2: Post-Run Evidence

```text
review_round: Review 3
scope: post-run evidence review
activation_mode: role_only
attempt_id: ATTEMPT-008
decision: not_confirmed
promotion_decision: blocked
evidence_level: valid_single_run
```

## Inputs Checked

- `attempts/ATTEMPT-007/manifest.yaml`
- `attempts/ATTEMPT-007/result.yaml`
- `attempts/ATTEMPT-007/result.md`
- `attempts/ATTEMPT-007/quality_check.md`
- `attempts/ATTEMPT-008/manifest.yaml`
- `attempts/ATTEMPT-008/result.yaml`
- `attempts/ATTEMPT-008/result.md`
- `attempts/ATTEMPT-008/quality_check.md`
- `ATTEMPTS.md`
- `manifest.yaml`
- `result.yaml`
- `result.md`
- `quality_check.md`
- Warehouse artifact identities below

## Review 3 Findings

- Metrics synchronized from `ATTEMPT-008`: U=71.22, S=76.64, H=73.83, ZS=81.62, best_epoch=45.
- Seed-42 pair check: `ATTEMPT-007` produced H=73.94 at epoch 42; `ATTEMPT-008` produced H=73.83 at epoch 45.
- Base version: `v2`.
- Code commit / pre-run freeze: `a51ea9068869487980ec4f24744ade9ac0501aeb`.
- Command: `conda run --no-capture-output -n dvsr_gpu python train_GTPJ_CUB.py --config experiments/module_trials/IDEA-0002_fae_memory_jepa/TRIAL-002_strict_conditional_jepa/attempts/ATTEMPT-008/config.yaml`.
- Trial decision: `not_confirmed`.
- Promotion decision: `blocked`.
- Evidence level: `valid_single_run`.
- Boundary check: raw artifacts remain in Warehouse; GitHub records lightweight ids, URIs, sha256, and size only.
- Runner console receipts for ATTEMPT-007/008 include a PyTorch warning that memory-efficient attention defaults to a non-deterministic backward algorithm under warn-only deterministic mode.

## Artifact Refs

- `log:v2:module_trial:TRIAL-002:attempt-008` -> `warehouse://gtpj/runs/v2/module_trial/TRIAL-002/attempt-008/logs/training_log_CUB_2026-06-28_22-51-02.txt`
- `log:v2:module_trial:TRIAL-002:attempt-007` -> `warehouse://gtpj/runs/v2/module_trial/TRIAL-002/attempt-007/logs/training_log_CUB_2026-06-28_22-41-32.txt`
- `checkpoint:v2:module_trial:TRIAL-002:attempt-008:best` -> `warehouse://gtpj/runs/v2/module_trial/TRIAL-002/attempt-008/checkpoints/best_model_CUB_2026-06-28_22-51-02_H7383.pth`
- `checkpoint:v2:module_trial:TRIAL-002:attempt-008:full` -> `warehouse://gtpj/runs/v2/module_trial/TRIAL-002/attempt-008/checkpoints/ckpt_full_CUB_2026-06-28_22-51-02.pth`
- `receipt:v2:module_trial:TRIAL-002:attempt-008:runner_console` -> `warehouse://gtpj/runs/v2/module_trial/TRIAL-002/attempt-008/receipts/runner_console.log`

## Blocking Issues

None recorded by automated closeout for `ATTEMPT-008`.

## Decision

`not_confirmed`
