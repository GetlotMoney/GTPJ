# Agent 编排和长期管理

## 核心结论

GTPJ 正式实验默认使用 `real_multi_agent`，但默认 agent 实例不再绑定到 `persistent_thread`。

默认形态：

```yaml
agents:
  activation_mode: real_multi_agent
  agent_instance_mode: temporary_subagent
  lifecycle: workflow_scoped
  evidence_source: files_and_artifacts
```

含义：

- `temporary_subagent` 是本轮 workflow / campaign 的活上下文，可以在整个 workflow 或 campaign 阶段内持续存在。
- `persistent_thread` 是跨 workflow 的活上下文，只在 owner 明确要求可见长期追踪、或某角色需要跨多轮连续上下文时启用。
- 长期 agent 不是永久在线聊天窗口。长期 agent 是 `profile.md`、`memory.md`、by-experiment 调用规则、历史 `agent_summary.md` 和 issues。
- 正式证据永远来自 repo、Research、Warehouse、manifest、result、quality 和 agent summary，不来自任何隐藏聊天上下文。

## 为什么默认多 Agent

每个正式角色都需要独立上下文。把规划、执行、读日志、质量检查、结果解释和复核放在同一个 agent 上下文里，会污染输入、判断和证据链。

以下任务默认必须使用 `real_multi_agent`：

- 启动真实 Runner；
- 创建或登记正式实验/attempt 证据；
- 改代码、配置语义、forward/loss/eval/data flow 或接口假设；
- 选择 best、影响下一轮高成本实验、影响论文实验路线或 baseline 决策；
- 准备 promotion、versioning、tag 或 owner-facing 正式结论；
- 长周期 autonomous research campaign。
- 任意组合 mixed experiment campaign，例如 `跑10创新+100调参`。

`role_only` 只允许用于纯只读解释/状态检查、训练前候选 triage、不改变结论的机械账本格式整理，或明确不进入正式证据的 debug/smoke。

如果当前工具环境不能提供真实 sub-agent，而任务又需要正式证据，Coordinator 必须阻断或把本轮显式降级为 debug/smoke。`role_only_with_independent_sequential_review` 只是 fallback 标签，不是 `real_multi_agent` 的替代品。

## GitHub 权威目录

```text
docs/workflow/agents/
|-- README.md
|-- shared_roles/
|   |-- coordinator/profile.md
|   |-- coordinator/memory.md
|   |-- reader_planner/profile.md
|   |-- reader_planner/memory.md
|   |-- runner/profile.md
|   |-- runner/memory.md
|   |-- implementer/profile.md
|   |-- implementer/memory.md
|   |-- interface_checker/profile.md
|   |-- interface_checker/memory.md
|   |-- quality_checker/profile.md
|   |-- quality_checker/memory.md
|   |-- log_analyst/profile.md
|   |-- log_analyst/memory.md
|   |-- result_analyst/profile.md
|   |-- result_analyst/memory.md
|   |-- reviewer/profile.md
|   `-- reviewer/memory.md
`-- by_experiment/
    |-- tune/agents/README.md
    |-- ablation/agents/README.md
    |-- innovation/agents/README.md
    |-- confirmation/agents/README.md
    `-- promotion/agents/README.md
```

`shared_roles/` 定义角色身份、权限、读写边界、输出和失败条件。`memory.md` 保存该角色反复踩坑、固定检查项和可复用经验。

`by_experiment/` 定义某类实验如何调用共享角色，不重复定义角色本身。

## 本地 Skill 镜像目录

本地 skill 必须镜像 GitHub 权威目录：

```text
C:\Users\Administrator\.codex\skills\gtpj-workflow\references\agents/
|-- README.md
|-- shared_roles/
`-- by_experiment/
```

如果 GitHub 文档和本地 skill 冲突，以 GitHub 文档为准。

## 活上下文分类

```text
role_only
  没有独立 agent 实例；主 agent 按角色清单执行。

workflow_scoped temporary_subagent
  本轮 workflow 的独立活上下文；正式实验默认值。

campaign_scoped temporary_subagent
  长周期 campaign 阶段内的独立活上下文；适合 10 到 20 天研究 campaign。

persistent_thread
  跨 workflow 的独立活上下文；可见、可复用，但不是正式证据源。
```

任何活上下文结束后，必须把需要保留的结论写入：

```text
agent_summary.md
result.yaml / result.md
quality_check.md
docs/workflow/issues/
shared_roles/<role>/memory.md
Research / Warehouse / campaign ledger
```

## Agent Runtime Protocol

GTPJ workflow-v2 不按 agent 数量启动工作，而是按 `subject_id` 的
`evidence_state transition` 启动必要角色。

固定权限：

```text
Coordinator:
  apply transition，最终写 GitHub 账本。

Planner:
  propose candidate / workstream / hypothesis transition。

Implementer:
  只改一个 trial/code path。

Runner Monitor:
  管服务器、GPU、队列、失败隔离。

Experiment Runner:
  执行单个 frozen run。

Log Analyst:
  propose single_run_valid / failed / metric_invalid。

Result Analyst:
  propose tune_promising / repeat_ready / reject / stop。

Interface Checker:
  check shape、input/output、GZSL hard rules、baseline-off。

Quality Checker:
  check evidence chain，默认 task_scoped。

Reviewer:
  check innovation、promotion、争议结果。
```

固定生命周期：

```text
campaign_scoped:
  Coordinator
  Runner Monitor
  Campaign Result Comparator

workstream_scoped:
  Innovation Planner
  Tune Planner
  Ablation Planner
  Confirmation Planner

task_scoped:
  Implementer
  Interface Checker
  Quality Checker
  Reviewer
  Result Analyst for one decision

run_scoped:
  Experiment Runner
  Log Analyst
  Warehouse Registrar
```

agent 输出必须包含：

```text
subject_id
transition_id
role_key
lifecycle
checked_inputs
rule_checks
authority_refs
decision: propose | allow | block | warn
blocking_issues
non_blocking_warnings
not_checked
reason_summary
```

Quality Checker 默认 `task_scoped`，只有 campaign final audit 才可
`campaign_scoped`，避免长上下文污染质量判断。

## Agent 启用字段

每次任务启动卡必须显式写入：

```yaml
agents:
  activation_mode: role_only | real_multi_agent
  agent_instance_mode: role_only | temporary_subagent | persistent_thread
  lifecycle: role_only | workflow_scoped | campaign_scoped | cross_workflow
  activation_reason:
  required_roles:
  disabled_roles:
  required_real_agents:
  persistent_threads:
    required:
    thread_ids:
    missing:
    reused:
  temporary_subagents:
    allowed:
    reason:
    debug_only:
    lifecycle:
    output_locations:
  single_agent_allowed:
  owner_override:
  tool_support:
    real_multi_agent_available:
    fallback_mode:
    checked_by:
  serial:
  parallel:
  writer_roles:
  reviewer_roles:
  memory_policy:
    session_context_allowed:
    codex_memory_allowed:
    repo_state_required:
    memory_used:
    memory_sources:
    persistent_thread_ids:
    agent_profile_files:
    agent_memory_files:
    verified_against_current_repo:
```

`activation_mode` 只能是 `role_only` 或 `real_multi_agent`。

`agent_instance_mode` 含义：

- `role_only`：没有独立 agent 实例，只适用于允许 `role_only` 的任务。
- `temporary_subagent`：本轮 workflow 或 campaign 的独立 agent 实例；正式实验默认值。
- `persistent_thread`：跨 workflow 的可见连续上下文；只在需要跨轮追踪时启用。

## 最快合规路径

Coordinator 默认必须选择“满足上下文隔离的最小有效路径”：

- 纯只读、状态检查、配置查看、pre-run triage、debug/smoke、机械账本整理，默认 `role_only`。
- Runner 产出的结果会进入正式 evidence、best 选择、confirmation、promotion 或下一轮高成本实验决策，默认 `real_multi_agent`。
- 正式 `real_multi_agent` 默认 workflow-scoped `temporary_subagent`。
- 跨多天 campaign 可以让 `Workflow Coordinator`、`Runner Monitor`、`Result Comparator` 使用 `persistent_thread`，但这不是证据源。
- Runner 永远串行并持有 GPU lock。
- Implementer 对同一代码路径永远单 writer。
- Coordinator 是最终 GitHub 账本唯一 writer。
- Reader/Planner、Log Analyst、Quality Checker、Result Analyst、Reviewer 默认只读，可并行。
- 未被 hard gate 要求、也不影响当前结论的角色必须跳过，并在启动卡里写明 `skipped_agents`。

启动卡里的 `agents.decision_basis` 必须包含：

```yaml
fastest_valid_path:
  selected:
  why_fastest:
  why_still_valid:
  skipped_agents:
  parallelized_roles:
  serialized_roles:
  agent_instance_mode:
  lifecycle:
  persistent_threads:
  temporary_subagent_reason:
```

## 启用矩阵

| 场景 | 默认模式 | 默认实例 | 触发理由 |
|---|---|---|---|
| 只读解释、定位文件、查看配置、普通状态汇报 | `role_only` | `role_only` | 不产生实验事实，不改代码，不改变结论。 |
| 训练前候选建议 | `role_only` | `role_only` | 只提出候选，不启动 Runner。 |
| 单一 Runner 按 frozen config 串行训练 | `real_multi_agent` | `temporary_subagent` | Runner 串行；Log、Quality、Result 等证据角色仍需独立上下文。 |
| debug/smoke | `role_only` | `role_only` | 结果不作为 keep / best / promote / confirmation evidence。 |
| owner 明确要求“多 agents”“独立 review” | `real_multi_agent` | `temporary_subagent` 或 `persistent_thread` | owner 已要求独立分工；是否跨轮由启动卡决定。 |
| 修改模型结构、forward、loss、eval 或数据流 | `real_multi_agent` | `temporary_subagent` | 代码语义变化需要实现、接口、质量独立复核。 |
| 涉及 label mapping、seen/unseen split、class order、logits shape 或 metric semantics | `real_multi_agent` | `temporary_subagent` | 这些是 GZSL 有效性硬门。 |
| 新 module trial 的实现、接口检查或 promotion 前复核 | `real_multi_agent` | `temporary_subagent` | 会影响 trial 结论或版本提升。 |
| 结果异常、争议大、owner 质疑解释 | `real_multi_agent` | `temporary_subagent` | 需要独立复核日志、配置、代码和质量证据。 |
| 准备写 `promotion_decision: promote`、创建 `vX` 或打 tag | `real_multi_agent` | `temporary_subagent` | 版本事实不可由单一视角确认。 |
| 10 到 20 天 autonomous research campaign | `real_multi_agent` | `temporary_subagent` + optional `persistent_thread` | workflow 自行调度多实验类型和最终交付。 |
| 任意组合 mixed experiment campaign | `real_multi_agent` | `temporary_subagent` with campaign/workstream/task/run lifecycle | 根据 requested_mix 拆分多个 workstream，不按实验数量开永久 agent。 |

## 按任务选角色

| 任务 | 必需角色 | 默认模式 |
|---|---|---|
| 只读状态 / 配置检查 | Coordinator，必要时 Reader/Planner | `role_only` |
| 调参建议 | Coordinator、Reader/Planner、Result Analyst | `role_only` |
| 调参真实运行 | Coordinator、Runner、Log Analyst、Result Analyst、Quality Checker | `real_multi_agent` |
| confirmation / rerun | Coordinator、Runner、Log Analyst、Result Analyst、Quality Checker | `real_multi_agent` |
| ablation | Coordinator、Runner、Log Analyst、Interface Checker、Result Analyst、Quality Checker | `real_multi_agent` |
| innovation / module trial | Coordinator、Reader/Planner、Implementer、Interface Checker、Runner、Log Analyst、Result Analyst、Quality Checker、Reviewer | `real_multi_agent` |
| promotion | Coordinator、Quality Checker、Reviewer、Result Analyst，必要时 Interface Checker | `real_multi_agent` |
| autonomous research campaign | Coordinator、Source Reader、Idea Planner、Runner Monitor、Log Metric Parser、Result Comparator、Evidence Quality Checker；按阶段加 Runner、Implementer、Interface Checker、Reviewer、Promotion Manager | `real_multi_agent` |
| mixed experiment campaign | Workflow Coordinator、Campaign Planner、Runner Monitor、Result Comparator、Evidence Quality Checker、Warehouse Registrar；按 workstream 加专用角色 | `real_multi_agent` |
| debug / smoke | Coordinator、Runner、Log Analyst，必要时 Interface Checker | `role_only` |

## Agent 记忆规则

Agent 不能把隐藏聊天记忆当作实验事实源。GTPJ 的可审计事实源按优先级排序：

1. 当前仓库文件、commit、tag、实验账本、config、manifest、result、quality check。
2. Warehouse / Research 中被 artifact id、URI、hash、size 引用的外部证据。
3. 当前对话中 owner 明确给出的任务约束。
4. Codex 全局 memory、persistent thread 或历史会话摘要，只能用于定位和背景提醒，必须回到当前仓库或 artifact 验证后才能入账。

长期 agent 记忆的读取顺序：

```text
shared_roles/<role>/profile.md
shared_roles/<role>/memory.md
by_experiment/<task_type>/agents/README.md
docs/workflow/issues/README.md 和最近相关问题文档
当前 task start card
```

长期 agent 记忆的写入规则：

- 新问题只出现一次：先写入本次 `agent_summary.md` 或当日 issue 文档。
- 同一类问题重复出现两次：写入对应角色 `memory.md` 的 failure mode。
- 同一类后处理动作重复三次：优先升级成 `workflow/gtpj_workflow.py` helper 或 sync check。
- `memory.md` 只能保存检查规则和经验，不保存 raw logs、长推理、完整论文笔记或实验大文件。

`agent_summary.md` 必须记录：

- `memory_used: yes | no`
- `memory_sources:`
- `verified_against_current_repo:`
- `agent_instance_mode:`
- `agent_instance_type:`
- `lifecycle:`
- `persistent_thread_id:` 如启用 persistent thread，否则写 `not_used`
- `independence_scope:`
- `output_locations:`

## 创新代码改动多轮审查

凡是 idea、创新机制或 module trial 会改变模型、forward、loss、eval、data flow、scoring 或配置语义，必须同时遵守：

```text
docs/workflow/innovation_code_review_protocol.md
```

最低审查顺序：

```text
Review 0: Reader/Planner + Coordinator 检查 idea/source intent
Review 1: Interface Checker 在写代码前检查设计和接口
Review 2: Interface Checker + Quality Checker + Reviewer 在正式 run 前检查 code diff
Review 3: Log Analyst + Quality Checker + Result Analyst + Reviewer 在 run 后检查证据和结论
```

临时 workflow-scoped agents 可以承担这些独立审查；它们必须加载对应长期角色的 `profile.md`、
`memory.md` 和 by-experiment 规则，并把发现写入 `review_round_*.md`、`agent_summary.md`、
`docs/workflow/issues/` 或对应 role memory。

Implementer 是同一代码路径唯一 writer。Reader/Planner、Interface Checker、Quality Checker、
Reviewer、Log Analyst 和 Result Analyst 默认只读。代码修复后必须重跑相关 review，不得沿用旧通过结论。

## 禁止事项

- 多个 agents 同时写同一个 `INDEX.md`。
- 多个 agents 同时改同一实验代码路径。
- Runner 并行抢同一块 GPU。
- 非 Coordinator 删除分支、合并分支、创建 tag。
- 非用户明确要求时 push 到 GitHub。
- 把 persistent thread、临时 agent 上下文或 Codex memory 当成正式实验事实。
- 为了显得规范而启动不影响 hard gate 的多余 agent。

## 进度看板联动

真实实验运行时，Coordinator 负责按 `docs/workflow/progress_dashboard.md` 创建和更新：

```text
.gtpj_runtime/runs/<run_id>/status.json
.gtpj_runtime/runs/<run_id>/events.jsonl
```

网页看板只读这些状态和 GitHub 账本，不直接启动训练、删除分支、打 tag、执行 promotion 或 push。

## 同步规则

修改 workflow agent 规范时：

1. 先更新 `docs/workflow/agents/` 和本文件。
2. 如果影响 agent 工作凭证，同步更新 `docs/workflow/agent_report_policy.md` 和模板。
3. 同步更新本地 `gtpj-workflow` skill 的 `references/agents/` 与相关 reference 文件。
4. 运行仓库验证。
5. 提交 GitHub 文档；只有 owner 明确要求时才 push。
