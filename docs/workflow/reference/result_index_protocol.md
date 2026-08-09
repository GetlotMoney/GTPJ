# Result Index Protocol

本文定义 GitHub 为 GTPJ experiments 保存的最小轻量证据结构。

## Experiment Files

新的 experiment 目录包含：

```text
config.yaml
manifest.yaml
result.yaml
result.md
quality_check.md
agent_summary.md
README.md
```

它们不得创建或提交 raw `logs/`、checkpoints、generated figures、feature caches 或 tensor dumps。

## `manifest.yaml`

`manifest.yaml` 是程序和 agents 的可复现地图。它记录：

- experiment id、kind、attempt id、status
- base version、base code tag、code branch、code commit、dirty state
- config path 和 config sha256
- run command、seed、dataset、split id、class order id、label mapping id、metric contract id
- 当实验改变代码或方法时，记录 idea summary
- 外部 artifact identity：`artifact_id`、`uri`、`sha256`、`size_bytes`、`role`、`status`
- 是否需要 interface contract review 和 boundary audit

对 tune experiments，idea summary 可以为空，但 hypothesis 必须说明这只是参数调优、不改变代码。
对 ablation、innovation 和 module trial experiments，idea summary 必须存在。

## `result.yaml`

`result.yaml` 是 helper、tests、registries 和 promotion gates 使用的机器可读结果文件。它记录：

- U, S, H, ZS, best epoch
- baseline version and baseline H
- delta H
- seed
- decision
- `promotion_decision` and `promote_to`, when applicable
- `evidence.log_artifact_id`
- `evidence.manifest`
- `evidence.agent_summary`
- `evidence.manifest_verified`
- `evidence.boundary_audit_passed`
- metric source 和 metric semantics

`result.yaml` 有意不重复每个 artifact 字段。Promotion 按以下方式解析 raw artifact：

```text
artifact_id = result.evidence.log_artifact_id
artifact    = manifest.artifacts[artifact_id]
uri         = artifact.uri
sha256      = artifact.sha256
size_bytes  = artifact.size_bytes
```

如果 manifest 无法把 artifact id 解析到 URI、sha256 和 size，则该结果不可 promotion。

## `result.md`

`result.md` 是人读解释，不是机器解析的事实源。它解释：

- metrics 是否提升；
- 提升可能来自哪里；
- tradeoff 是什么；
- 结果是 `keep`、`reject`、`rejected`、`rerun`、`needs_confirmation`、`blocked` 还是 `promote`。

## `agent_summary.md`

`agent_summary.md` 是 agent 工作的轻量审计轨迹。它记录哪些 agents 被启用、哪些 agents
被禁用、每个 agent 检查了什么、发现了什么问题，以及哪些 evidence references 支撑最终决策。

它不能包含完整聊天记录或 raw logs。长 agent reports 应放入 Warehouse，并用 artifact id 引用。

## Protected Evaluation Semantics

实验不得静默改变：

- class order
- seen/unseen split
- label mapping
- logits shape
- calibration path
- metric calculation
- output fields consumed by the evaluation script

如果实验本身改变 evaluation，必须显式标记为 high risk，并由 `Interface Checker` 和
`Quality Checker` 双重 review 阻断。否则该结果不能与 baseline 比较。

## Promotion Mapping

Promotion 读取：

```text
code_commit      = manifest.version.code_commit
run_config       = manifest.reproducibility.config_file
run_command      = manifest.reproducibility.command
run_log_artifact = result.evidence.log_artifact_id
run_log_uri      = manifest.artifacts[run_log_artifact].uri
run_log_sha256   = manifest.artifacts[run_log_artifact].sha256
run_log_size     = manifest.artifacts[run_log_artifact].size_bytes
metrics          = result.metrics
decision         = result.decision
```

`record-result` 只记录 evidence，不授权 promotion。`promotion_decision: promote` 只有同时满足
`evidence_level: baseline_grade` 和 `confirmation_status: confirmed` 时，才触发 promotion hard gate；
它本身不会创建正式版本。
