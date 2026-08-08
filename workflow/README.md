# GTPJ Workflow Helper

`workflow/gtpj_workflow.py` 是 GTPJ 的结构辅助入口。它不训练模型、不 push、不改远端、不自动发布；它只负责创建标准目录、写轻量账本、检查 GitHub 边界和验证基础治理状态。

当前主规范：

```text
docs/workflow/FRAMEWORK_EXPERIMENT_STANDARD.md
docs/GITHUB_GOVERNANCE.md
docs/PROJECT_STRUCTURE.md
docs/PROJECT_STATUS.md
docs/workflow/artifact_policy.md
docs/workflow/result_index_protocol.md
docs/workflow/quality_gate.md
docs/workflow/agent_contracts.md
```

涉及改代码的创新时，先按正式规范冻结为候选框架快照；候选自己的消融、调参和确认必须从同一冻结候选提交独立开始。`new-trial` 相关命令仅保留给旧记录兼容，不能作为新正式实验入口。

当前 active mainline code 是 `GTPJ-v3 / tag v3`。`H=74.27` 记录为
`best_observed_H`，`confirmed_H` 仍待 clean confirmation；`GTPJ-v1 / tag v1 / H=73.93`
仍是历史 confirmed baseline。`validate` 会检查本地 baseline tag 是否能读到对应记录；`validate-remote`
用于核对远端 `main` 和 baseline tags 是否与本地治理事实对齐。

任何状态检查、结果比较、promotion 或 tag 前，先用只读命令判断复现状态：

```bash
python workflow/gtpj_workflow.py repro-status --version v3
```

如果输出 `verdict: needs_confirmation`，该版本只能作为 active code / unconfirmed reference，
不能表述为 confirmed baseline。

## Owner Phrases

owner 日常可以直接说人话口令，Coordinator 负责映射到下面的结构命令和协议：

| 口令 | 默认动作 |
|---|---|
| `查状态` | 运行只读状态检查和必要的结构检查。 |
| `复现` | 走当前 active baseline 的 confirmation 准备；未要求正式证据时优先最快合规路径。 |
| `调参` | 先用 `tune-suggest` 生成最多 3 个候选，不自动训练。 |
| `消融` | 先判断是版本级消融，还是某个冻结候选内部的窄消融，再建对应计划。 |
| `开新模块` | 从当前 active baseline 的 selected ready idea 队列选择一个，先建立 `Vx-INNOVATION-xxx` 候选，不直接生成正式框架。 |
| `试这个：...` | 先判断是一句 local heuristic idea、idea inbox，还是可进入正式创新候选的想法。 |
| `继续上一个` | 继续当前正式创新候选或实验的下一步最小动作；旧 trial/attempt 只读回查。 |
| `升版本` | 检查 promotion gate。 |
| `切版本` | 区分 set-current-version 和 activate-version；后者必须 owner 明确授权。 |

这些口令的正式定义见 `docs/workflow/QUICK_START.md` 和 `docs/workflow/TASK_START_MINI.md`。

## Commands

```bash
# status / validation
python workflow/gtpj_workflow.py start --phrase "开新模块"
python workflow/gtpj_workflow.py status
python workflow/gtpj_workflow.py repro-status --version v3
python workflow/gtpj_workflow.py validate
python workflow/gtpj_workflow.py validate-remote
python workflow/gtpj_workflow.py audit-boundary

# tune suggestion
python workflow/gtpj_workflow.py tune-suggest --version v3

# retired formal-experiment helper example
# 当前发布版 `new-experiment` 仍有“实验分支必须包含 main”的旧限制，
# 不能用于从冻结模板或冻结候选开始的新正式实验。等专门的 helper 升级审核通过后，
# 再在这里补回与 FRAMEWORK_EXPERIMENT_STANDARD.md 一致的可执行示例。

# idea and version view
python workflow/gtpj_workflow.py new-idea --idea-id IDEA-XXXX --slug short_name --title "short name" --source-type paper --source-ref "<source>" --source-status verified --base-version v1 --global-score 50 --version-score 50 --applicability direct
python workflow/gtpj_workflow.py set-current-version --version v1

# retired Trial/Attempt commands
# `new-trial`、`record-module-attempt` 和 `sync-trial-summary` 仅供旧历史回查，
# 不能用于任何新的候选、消融、调参、确认或正式证据。
```

## Boundary Rules

- 当前发布版 `new-experiment` 的“分支必须包含 current local main”规则已被正式实验规范废止；在模板绑定 helper 升级审核通过前，禁止用它创建新的正式实验。
- `start --phrase "..."` is read-only: it prints the owner-facing mini start card and never creates branches, files, or runs.
- `new-trial` 仅为旧 `TRIAL / ATTEMPT` 历史兼容保留；禁止用它创建任何新的候选、消融、调参、确认或正式证据。
- 当前发布的 helper 还不能创建 `candidate_frozen` 子实验。新候选的子实验必须等专门的 helper 升级通过审核后再启动，不能把它伪装成普通模板实验。
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
