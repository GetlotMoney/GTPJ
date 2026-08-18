# GTPJ Workflow Helper

> 2026-08-08 起，默认实验入口改为 `SYS-WORKFLOW-V6` 五步短流程。本文后续的 `agent_runtime.yaml`、`prepare-run-start-receipt`、多层审核和旧动态批次命令只作历史兼容或按需工具，不再是普通实验与论文实验的默认门槛。新实验优先使用：唯一实验提交、配置与参数表、一次 clean/data/GPU 检查、直接训练到独立 RUN 目录、结果回填。

`workflow/gtpj_workflow.py` 是 GTPJ 的结构辅助入口。它不训练模型、不 push、不改远端、不自动发布；它只负责创建标准目录、写轻量账本、检查 GitHub 边界和验证基础治理状态。

当前主规范：

```text
docs/GITHUB_GOVERNANCE.md
docs/PROJECT_STRUCTURE.md
docs/PROJECT_STATUS.md
docs/workflow/FRAMEWORK_EXPERIMENT_STANDARD.md
docs/workflow/reference/artifact_policy.md
docs/workflow/reference/result_index_protocol.md
docs/workflow/protocols/quality_gate.md
docs/workflow/reference/agent_contracts.md
```

当前 active mainline code 是 `GTPJ-v5 / tag v5`。`best_observed_H=74.54`，
`confirmed_H=74.44`，仍需和更强 confirmed reference `v3/CONFIRM-001 local-v3-054 confirmed_H=74.47` 区分表述。当前 IDEA-0003/TRIAL-001 的研究最高单次为 `H=75.11`，但 exact repeat 未还原，不能写成 confirmed 或 promoted 结果。
`validate` 会检查本地 baseline tag 是否能读到对应记录；`validate-remote`
用于核对远端 `main` 和 baseline tags 是否与本地治理事实对齐。

任何状态检查、结果比较、promotion 或 tag 前，先用只读命令判断复现状态：

```bash
python workflow/gtpj_workflow.py repro-status --version v5
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
| `消融` | 先确定目标框架和要关闭的因素，再在该框架的 ablation 账本建计划。 |
| `开新模块` | 从当前 active baseline 的 selected ready idea 队列自动选择一个 module trial。 |
| `试这个：...` | 先判断是一句 local heuristic idea、idea inbox，还是可进入 trial 的候选。 |
| `继续上一个` | 找到上一个正式框架实验；旧 Trial/Attempt 只作为追溯链接。 |
| `升版本` | 检查 promotion gate。 |
| `切版本` | 区分 set-current-version 和 activate-version；后者必须 owner 明确授权。 |

这些口令的正式定义见 `docs/workflow/core/QUICK_START.md` 和 `docs/workflow/core/TASK_START_MINI.md`。

## Commands

```bash
# status / validation
python workflow/gtpj_workflow.py start --phrase "开新模块"
python workflow/gtpj_workflow.py status
python workflow/gtpj_workflow.py todo-status
python workflow/gtpj_workflow.py refresh-todo
python workflow/gtpj_workflow.py repro-status --version v5
python workflow/gtpj_workflow.py validate
python workflow/gtpj_workflow.py validate-remote
python workflow/gtpj_workflow.py audit-boundary

# tune suggestion
python workflow/gtpj_workflow.py tune-suggest --version v5

# framework tune example
python workflow/gtpj_workflow.py validate-framework-templates
git switch -c exp/v1/tune/tune-001-topo008 <TEMPLATE_TAG>
python workflow/gtpj_workflow.py new-experiment --base-identity-kind framework_template --version v1 --kind tune --exp-id TUNE-001 --slug topo008
# 填写 experiments/v1/tune/TUNE-001_topo008/PARAMETER_MATRIX.csv 的真实参数、seed 和目的后：
python workflow/gtpj_workflow.py freeze-parameter-matrix --path experiments/v1/tune/TUNE-001_topo008/PARAMETER_MATRIX.csv --config experiments/v1/tune/TUNE-001_topo008/config.yaml --job-id RUN-001
python workflow/gtpj_workflow.py validate-parameter-matrix --path experiments/v1/tune/TUNE-001_topo008/PARAMETER_MATRIX.csv --require-ready
# 提交上述冻结表后，才运行训练。
conda run -n dvsr_gpu python train_GTPJ_CUB.py --config experiments/v1/tune/TUNE-001_topo008/config.yaml
python workflow/gtpj_workflow.py record-result --version v1 --kind tune --exp-id TUNE-001 --slug topo008 --matrix-job-id RUN-001 --parameter conditional_text_ratio --old-value 0.008 --new-value 0.006 --seed 5 --log train_log/CUB/<log>.txt --pre-run-freeze-commit <FREEZE_COMMIT> --command "conda run -n dvsr_gpu python train_GTPJ_CUB.py --config experiments/v1/tune/TUNE-001_topo008/config.yaml" --decision keep

# idea and version view
python workflow/gtpj_workflow.py new-idea --idea-id IDEA-XXXX --slug short_name --title "short name" --source-type paper --source-ref "<source>" --source-status verified --base-version v1 --global-score 50 --version-score 50 --applicability direct
python workflow/gtpj_workflow.py set-current-version --version v1

# framework innovation example
python workflow/gtpj_workflow.py validate-framework-templates
git switch -c exp/v1/innovation/innovation-001-short-name <TEMPLATE_TAG>
python workflow/gtpj_workflow.py new-experiment --base-identity-kind framework_template --version v1 --kind innovation --exp-id INNOVATION-001 --slug short_name
# 填写 innovation 实验的 PARAMETER_MATRIX.csv；确认晋级后再注册新的同级正式框架和 Tag。

# owner-selected source example（账本归属 v5，但代码起点由 owner 指定）
git switch -c exp/v5/innovation/innovation-024-owner-source <OWNER_SOURCE_COMMIT>
python workflow/gtpj_workflow.py new-experiment --base-identity-kind owner_selected_code_ref --version v5 --kind innovation --exp-id INNOVATION-024 --slug owner_source --owner-source-ref owner/chosen-branch --owner-source-commit <40_HEX_COMMIT> --owner-source-label chosen-model-v0 --owner-selection-ref owner:2026-08-18 --base-config path/to/source/config.yaml
```

## Boundary Rules

- `new-experiment` 没有默认代码起点，必须由 owner 显式选择 `framework_template` 或 `owner_selected_code_ref`。前者要求 `HEAD` 等于模板 commit；后者必须同时传 `--owner-source-ref`、40 位 `--owner-source-commit`、`--owner-source-label`、`--owner-selection-ref` 和 `--base-config`，并要求创建瞬间 `HEAD` 与 owner 指定 commit 完全相等。
- `start --phrase "..."` is read-only: it prints the owner-facing mini start card and never creates branches, files, or runs.
- `new-trial`、`record-module-attempt` 和 `sync-trial-summary` 仅用于维护迁移前的旧 Trial/Attempt 证据，不是新实验入口。
- `record-result` parses an external log, computes `sha256` and `size`, writes `manifest.yaml`, `result.yaml`, `result.md`, README, and indexes, but never copies the raw log into GitHub.
- 兼容命令 `record-module-attempt` 仍可维护旧目录，但任何新运行必须登记到所属正式框架的正式实验和参数表。
- `closeout-check` is read-only: it verifies attempt evidence, trial root files, module-trial index, idea-tree evidence, and Warehouse artifacts are connected.
- `audit-boundary` blocks raw logs, checkpoints, generated images, feature caches, and copied-log evidence from entering GitHub.
- Historical `GTPJ-v1` baseline raw log has been migrated to `GTPJ_Warehouse`; GitHub keeps only artifact id, URI, hash, size, config, result, and quality records.

## Interface And Evaluation Rules

Experiments that change code, data flow, scoring, loss, or evaluation must satisfy `docs/workflow/protocols/code_interface_contract.md`.

If interface, label mapping, seen/unseen split, class order, logits shape, or metric semantics are unclear, the experiment is invalid evidence. Runner must refuse to run it; already produced results must be marked `blocked`, `rerun`, or `rejected`, not `keep` or `promote`.

## Runtime Notes

`runner-lock` and `runner-unlock` use `.gtpj_runtime/gpu_runner.lock` as a local file lock. This lock is not tracked by Git and does not replace checking actual GPU state.

The current OpenClaw/Codex runtime entrypoints, and any future runtime integration, must use the same repository docs, templates, schemas, and CLI checks.

## 参数矩阵入口（2026-08-04 起）

新的正式实验必须先有逐任务参数表，不能只保留批次总结果。先填写 `PARAMETER_MATRIX.csv`，再用 `freeze-parameter-matrix` 把实际配置快照、种子和完整指纹冻结并生成阅读版；通过 `validate-parameter-matrix --require-ready` 后提交 pre-run freeze commit。随后在 clean worktree 中用现有训练入口直接运行，并把输出保存到独立 `RUN-xxx/training.log`。结果登记必须提供 `--pre-run-freeze-commit`；`record-result` 会核对参数表、实际配置、种子、调参值，以及日志中训练入口实际打印的代码 commit、配置 SHA-256 和随机种子，校验完整 U/S/H/ZS 后把日志哈希和结果回填对应行。`--run-start-receipt` 只作历史兼容或按真实风险启用，不是 V6 默认门槛。完整规则见 `docs/workflow/protocols/parameter_matrix_protocol.md`。
