# GTPJ Workflow Helper

`workflow/gtpj_workflow.py` 是 GTPJ 的结构辅助入口。它不训练模型、不 push、不改远端、不自动发布；它只负责创建标准目录、写轻量账本、检查 GitHub 边界和验证基础治理状态。

当前主规范：

```text
docs/GITHUB_GOVERNANCE.md
docs/PROJECT_STRUCTURE.md
docs/PROJECT_STATUS.md
docs/workflow/artifact_policy.md
docs/workflow/result_index_protocol.md
docs/workflow/quality_gate.md
docs/workflow/agent_contracts.md
```

当前权威 baseline 是 `GTPJ-v1 / tag v1 / H=73.93`。`validate` 会检查本地 `v1` tag 是否能读到该 baseline 记录；`validate-remote` 会检查远端 `main` 和 `v1` 是否与本地治理事实对齐。

## Commands

```bash
python workflow/gtpj_workflow.py status
python workflow/gtpj_workflow.py validate
python workflow/gtpj_workflow.py validate-remote
python workflow/gtpj_workflow.py audit-boundary

python workflow/gtpj_workflow.py tune-suggest --version v1

git switch main
git status --short
git switch -c exp/v1-tune-001-topo008
python workflow/gtpj_workflow.py new-experiment --version v1 --kind tune --exp-id TUNE-001 --slug topo008
python workflow/gtpj_workflow.py runner-lock --run-id RUN-20260625-001 --experiment-id TUNE-001
python train_GTPJ_CUB.py --config experiments/v1/tune/TUNE-001_topo008/config.yaml
python workflow/gtpj_workflow.py record-result --version v1 --kind tune --exp-id TUNE-001 --slug topo008 --parameter conditional_text_ratio --old-value 0.008 --new-value 0.006 --seed 5 --log train_log/CUB/<log>.txt --command "python train_GTPJ_CUB.py --config experiments/v1/tune/TUNE-001_topo008/config.yaml" --decision keep
python workflow/gtpj_workflow.py runner-unlock --run-id RUN-20260625-001

python workflow/gtpj_workflow.py new-idea --idea-id IDEA-XXXX --slug short_name --title "short name" --source-type paper --source-ref "<source>" --source-status verified --base-version v1 --global-score 50 --version-score 50 --applicability direct
python workflow/gtpj_workflow.py set-current-version --version v1

git switch main
git status --short
git switch -c dev/v1-idea-xxxx-trial-001-short-name
python workflow/gtpj_workflow.py new-trial --idea-id IDEA-XXXX --trial-id TRIAL-001 --slug short_name --base-version v1
```

## Boundary Rules

- `new-experiment` only runs on the exact clean `exp/...` branch and that branch must contain current local `main`.
- `new-trial` only runs on the exact clean `dev/...` branch and that branch must contain current local `main`.
- `record-result` parses an external log, computes `sha256` and `size`, writes `manifest.yaml`, `result.yaml`, `result.md`, README, and indexes, but never copies the raw log into GitHub.
- `audit-boundary` blocks raw logs, checkpoints, generated images, feature caches, and copied-log evidence from entering GitHub.
- Historical `GTPJ-v1` baseline raw log has been migrated to `GTPJ_Warehouse`; GitHub keeps only artifact id, URI, hash, size, config, result, and quality records.

## Interface And Evaluation Rules

Experiments that change code, data flow, scoring, loss, or evaluation must satisfy `docs/workflow/code_interface_contract.md`.

If interface, label mapping, seen/unseen split, class order, logits shape, or metric semantics are unclear, the experiment is invalid evidence. Runner must refuse to run it; already produced results must be marked `blocked`, `rerun`, or `rejected`, not `keep` or `promote`.

## Runtime Notes

`runner-lock` and `runner-unlock` use `.gtpj_runtime/gpu_runner.lock` as a local file lock. This lock is not tracked by Git and does not replace checking actual GPU state.

Future OpenClaw/Codex runtime integrations must use the same repository docs, templates, schemas, and CLI checks.
