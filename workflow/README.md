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

当前 active mainline code 是 `GTPJ-v2 / tag v2`。`H=74.29` 记录为
`best_observed_H`，`confirmed_H` 仍待 clean confirmation；`GTPJ-v1 / tag v1 / H=73.93`
仍是历史 confirmed baseline。`validate` 会检查本地 baseline tag 是否能读到对应记录；`validate-remote`
用于核对远端 `main` 和 baseline tags 是否与本地治理事实对齐。

## Owner Phrases

owner 日常可以直接说人话口令，Coordinator 负责映射到下面的结构命令和协议：

| 口令 | 默认动作 |
|---|---|
| `查状态` | 运行只读状态检查和必要的结构检查。 |
| `复现` | 走当前 active baseline 的 confirmation 准备；未要求正式证据时优先最快合规路径。 |
| `调参` | 先用 `tune-suggest` 生成最多 3 个候选，不自动训练。 |
| `消融` | 先判断 version-level ablation 还是 trial-internal narrow ablation，再建对应计划。 |
| `开新模块` | 从当前 active baseline 的 selected ready idea 队列自动选择一个 module trial。 |
| `试这个：...` | 先判断是一句 local heuristic idea、idea inbox，还是可进入 trial 的候选。 |
| `继续上一个` | 继续当前 trial/attempt 的下一步最小动作。 |
| `升版本` | 检查 promotion gate。 |
| `切版本` | 区分 set-current-version 和 activate-version；后者必须 owner 明确授权。 |

这些口令的正式定义见 `docs/workflow/QUICK_START.md` 和 `docs/workflow/TASK_START_MINI.md`。

## Commands

```bash
# status / validation
python workflow/gtpj_workflow.py start --phrase "开新模块"
python workflow/gtpj_workflow.py status
python workflow/gtpj_workflow.py validate
python workflow/gtpj_workflow.py validate-remote
python workflow/gtpj_workflow.py audit-boundary

# tune suggestion
python workflow/gtpj_workflow.py tune-suggest --version v2

# version-level tune example
git switch main
git status --short
git switch -c exp/v1-tune-001-topo008
python workflow/gtpj_workflow.py new-experiment --version v1 --kind tune --exp-id TUNE-001 --slug topo008
python workflow/gtpj_workflow.py runner-lock --run-id RUN-20260625-001 --experiment-id TUNE-001
python train_GTPJ_CUB.py --config experiments/v1/tune/TUNE-001_topo008/config.yaml
python workflow/gtpj_workflow.py record-result --version v1 --kind tune --exp-id TUNE-001 --slug topo008 --parameter conditional_text_ratio --old-value 0.008 --new-value 0.006 --seed 5 --log train_log/CUB/<log>.txt --command "python train_GTPJ_CUB.py --config experiments/v1/tune/TUNE-001_topo008/config.yaml" --decision keep
python workflow/gtpj_workflow.py runner-unlock --run-id RUN-20260625-001

# idea and version view
python workflow/gtpj_workflow.py new-idea --idea-id IDEA-XXXX --slug short_name --title "short name" --source-type paper --source-ref "<source>" --source-status verified --base-version v1 --global-score 50 --version-score 50 --applicability direct
python workflow/gtpj_workflow.py set-current-version --version v1

# module trial example
git switch main
git status --short
git switch -c dev/v1-idea-xxxx-trial-001-short-name
python workflow/gtpj_workflow.py new-trial --idea-id IDEA-XXXX --trial-id TRIAL-001 --slug short_name --base-version v1
python workflow/gtpj_workflow.py record-module-attempt --trial-dir experiments/module_trials/IDEA-XXXX_short_name/TRIAL-001_short_name --attempt-id ATTEMPT-001 --log train_log/CUB/<log>.txt --decision revise
python workflow/gtpj_workflow.py sync-trial-summary --trial-dir experiments/module_trials/IDEA-XXXX_short_name/TRIAL-001_short_name --attempt-id ATTEMPT-001 --decision revise
python workflow/gtpj_workflow.py closeout-check --trial-dir experiments/module_trials/IDEA-XXXX_short_name/TRIAL-001_short_name --attempt-id ATTEMPT-001
```

## Boundary Rules

- `new-experiment` only runs on the exact clean `exp/...` branch and that branch must contain current local `main`.
- `start --phrase "..."` is read-only: it prints the owner-facing mini start card and never creates branches, files, or runs.
- `new-trial` only runs on the exact clean `dev/...` branch and that branch must contain current local `main`.
- `record-result` parses an external log, computes `sha256` and `size`, writes `manifest.yaml`, `result.yaml`, `result.md`, README, and indexes, but never copies the raw log into GitHub.
- `record-module-attempt` writes attempt-local evidence under `attempts/ATTEMPT-xxx/`; `sync-trial-summary` then promotes that attempt's lightweight evidence into the trial root README/result/quality, `experiments/module_trials/INDEX.md`, and `idea_tree/`.
- `closeout-check` is read-only: it verifies attempt evidence, trial root files, module-trial index, idea-tree evidence, and Warehouse artifacts are connected.
- `audit-boundary` blocks raw logs, checkpoints, generated images, feature caches, and copied-log evidence from entering GitHub.
- Historical `GTPJ-v1` baseline raw log has been migrated to `GTPJ_Warehouse`; GitHub keeps only artifact id, URI, hash, size, config, result, and quality records.

## Interface And Evaluation Rules

Experiments that change code, data flow, scoring, loss, or evaluation must satisfy `docs/workflow/code_interface_contract.md`.

If interface, label mapping, seen/unseen split, class order, logits shape, or metric semantics are unclear, the experiment is invalid evidence. Runner must refuse to run it; already produced results must be marked `blocked`, `rerun`, or `rejected`, not `keep` or `promote`.

## Runtime Notes

`runner-lock` and `runner-unlock` use `.gtpj_runtime/gpu_runner.lock` as a local file lock. This lock is not tracked by Git and does not replace checking actual GPU state.

The current OpenClaw/Codex runtime entrypoints, and any future runtime integration, must use the same repository docs, templates, schemas, and CLI checks.
