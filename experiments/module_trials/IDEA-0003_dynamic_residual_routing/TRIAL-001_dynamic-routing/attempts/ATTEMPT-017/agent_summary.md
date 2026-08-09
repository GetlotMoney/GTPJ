# ATTEMPT-017 Agent Summary

## Mode

- workflow_mode: `server_frozen_runner`
- activation_mode: `role_only`
- agent_instance_mode: `role_only`
- formal_runtime_backend: `server_detached_role_only`
- thread_creation_allowed: `false`

## Sequential Role Outputs

| Role | Output | Decision |
|---|---|---|
| Runner Monitor | `agent_outputs/runner_monitor.md` | allow |
| Interface Checker | `agent_outputs/interface_checker.md` | allow |
| Evidence Quality Checker | `agent_outputs/evidence_quality_checker.md` | allow |

## Closeout

ATTEMPT-017 completed as a server-frozen 100-job tune/search plus narrow-ablation batch. Final synchronized status is 100 completed, 0 failed, 0 skipped. The best single is `DR-095 a015dr035_weight_plus_0.01` with H=75.11, U=73.00, S=77.36, ZS=82.12 at epoch 48.

This is not confirmation evidence. DR-095 is the exact-repeat candidate for the next workflow stage, with `restore_target_H=75.11`, original seed 5, and a hard cap of 5 attempts.

## Memory Policy

Codex memory was used only for orientation about the local ledger and lab4090 runtime split. Current decisions were verified against the repo files, ATTEMPT-015/016 records, helper tests, and live lab4090 read-only status.
