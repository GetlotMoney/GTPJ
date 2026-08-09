# Task Start Mini Card

本文件定义 owner 可见的极简启动卡。完整 `TASK_START_CARD.md` 仍然是正式审查模板，但默认由
Coordinator 在后台展开；owner 日常只看这些最小字段。

只读预览入口：

```bash
python workflow/gtpj_workflow.py start --phrase "开新模块"
```

该命令只打印下面的字段，不写文件、不建分支、不跑训练。

## 1. Mini 启动卡

```yaml
owner_phrase:
task_type:
workflow_mode:
base_version:
base_template_id:
base_template_tag:
base_template_commit:
template_ledger: experiments/vX/TEMPLATE.yaml
experiment_binding: experiments/vX/<type>/<experiment-id>/EXPERIMENT.yaml
target:
subject_id:
evidence_state:
writes:
agent_mode:
agent_instance_mode:
runner_scope:
formal_runner_allowed:
formal_evidence_allowed:
agent_runtime_gate:
multi_agent_preflight:
owner_monitor_mode:
agent_activity_stream:
gates:
blocked_reason:
next_action:
```

`workflow_mode` 必填：`live_multi_agent_monitor` 表示动态多 agents 监控工作流；
`server_frozen_runner` 表示本地规划、冻结计划、服务器 detached 训练工作流。
owner 只说“用工作流”但没有说明哪一种时，必须先确认这一项，不能由 Coordinator 猜测。

字段含义：

| 字段 | 含义 |
|---|---|
| `owner_phrase` | owner 的原始口令，例如 `开新模块`、`复现`、`试这个：...`。 |
| `task_type` | Coordinator 路由后的任务类型。 |
| `base_version` | 默认当前 active baseline；只有 owner 明确指定时才改历史版本。 |
| `base_template_id` | 本实验复制的只读母版编号，例如 `MODEL-V5-TEMPLATE-V1`。 |
| `template_ledger` | 母版身份来源，必须是所属框架的 `TEMPLATE.yaml`。 |
| `experiment_binding` | 实验起点记录，必须是本实验目录的 `EXPERIMENT.yaml`。 |
| `target` | 本次目标，例如 baseline、参数、idea、trial 或候选列表。 |
| `subject_id` | 本次被路由或检查的对象，例如 `TRIAL-003`、`ATTEMPT-007`、`RUN-...`、`CAMP-...`。 |
| `evidence_state` | 当前证据成熟度；正式状态必须能由 `TRANSITIONS.jsonl` 派生。 |
| `writes` | 本次会写哪里；只读任务写 `none`。 |
| `agent_mode` | `role_only` 或 `real_multi_agent`，附一句为什么。 |
| `agent_instance_mode` | `role_only`、`named_owner_thread` 或 `persistent_thread`；正式实验默认 workflow-scoped `named_owner_thread`，跨 workflow 连续追踪才启用 `persistent_thread`。 |
| `runner_scope` | `none`、`debug_smoke` 或 `formal_runner`；只有 `formal_runner` 能产出正式实验证据。 |
| `formal_runner_allowed` | 正式 Runner 是否允许启动；没有真实多 agent preflight 时必须是 `false`。 |
| `formal_evidence_allowed` | 本轮输出是否允许进入 keep / best / confirmation / promotion / version 判断。 |
| `agent_runtime_gate` | 正式 Runner 启动前的 `agent_runtime.yaml` 路径和 `validate-agent-runtime` 状态；纯只读或 debug/smoke 写 `not_required`。 |
| `multi_agent_preflight` | 正式 Runner 启动前必须写 `pass`；缺真实 agent id、独立输出或 allow/pass 时写 `fail`。 |
| `owner_monitor_mode` | 正式 Runner 必须写 `true`；owner 是监控者，过程必须在当前对话或明确 Monitor 线程可见。 |
| `agent_activity_stream` | 记录哪个智能体在做什么的活动流文件；纯只读或 debug/smoke 可写 `not_required`。 |
| `gates` | 本次真正相关的硬门，只列会影响开工的门。 |
| `blocked_reason` | 如果不能开正式 Runner，写最小阻断原因；不能留空后继续跑正式实验。 |
| `next_action` | 下一步最小动作；不能把完整流程丢给 owner 填。 |

## 2. 展开规则

Mini 启动卡是 owner-facing 摘要，不替代完整卡。只要任务会改文件、跑实验或登记结果，
Coordinator 必须能从 mini 卡展开出完整 `TASK_START_CARD.md` 字段：

```text
router
version
inputs
agents
hard_gates
expected_outputs
stop_if
```

如果 mini 卡里出现阻断，先停在最小补齐动作，不创建分支、不建实验目录、不启动训练。

## 3. 示例

### 开新模块

```yaml
owner_phrase: 开新模块
task_type: innovation / module trial
base_version: 当前 active baseline
target: 下一个 selected ready idea
subject_id: pending until trial is created
evidence_state: hypothesis_ready
writes: idea_tree + experiments/module_trials + Warehouse after run
agent_mode: real_multi_agent，因为新模块代码改动需要 Review 0-3
agent_instance_mode: named_owner_thread, lifecycle workflow_scoped
runner_scope: formal_runner
formal_runner_allowed: false until multi_agent_preflight pass
formal_evidence_allowed: false until formal Runner completes with evidence chain
agent_runtime_gate: required before Runner; must record left_sidebar_named_threads
multi_agent_preflight: required before formal Runner
owner_monitor_mode: true; visible reports must name active agents and actions
agent_activity_stream: required before formal Runner
gates: source_status, interface_contract, innovation_code_review, artifact_boundary
blocked_reason: none after real_multi_agent gate passes; otherwise block formal run
next_action: read active version idea view and select the highest-priority ready idea
```

### 复现

```yaml
owner_phrase: 复现
task_type: confirmation
base_version: 当前 active baseline
target: 当前 baseline 结果
subject_id: confirmation subject selected after repro-status
evidence_state: single_run_valid or confirmation target state
writes: none until owner confirms run and evidence level
agent_mode: 正式运行用 real_multi_agent；Runner 启动前的准备可以 role_only
agent_instance_mode: 正式运行用 named_owner_thread；跨 workflow 追踪才用 persistent_thread
runner_scope: formal_runner if confirmation will enter evidence; none for read-only repro-status
formal_runner_allowed: false until multi_agent_preflight pass
formal_evidence_allowed: false until formal Runner and result review pass
agent_runtime_gate: required before formal rerun; not required for read-only repro-status
multi_agent_preflight: required before formal rerun
owner_monitor_mode: true for formal rerun
agent_activity_stream: required before formal Runner
gates: baseline_repro_status, metric_semantics, evidence_level, artifact_boundary
blocked_reason: none for read-only; missing real_multi_agent gate blocks formal rerun
next_action: run repro-status, then decide quick_local vs formal confirmation target
confirmation_policy:
  repeat_type: exact_repeat
  original_seed: must match source result
  max_attempts: 5
  max_attempts_hard_cap: true
  early_stop_on_best_hit: true
  restore_target_H: must be reached to count as reproduced
  near_miss_tolerance_H: default 0.2, records hope only
  near_miss_not_restored: true
  seed_sweep_or_multi_seed_stability: not_confirmation_evidence
```

同一候选不管是否还原成功，exact repeat 最多 5 次；命中 `restore_target_H` 可提前停止，5 次未命中则收口为 not restored / near miss。

### 试这个

```yaml
owner_phrase: 试这个：把 <机制> 接到 <位置>
task_type: local heuristic idea or innovation / module trial
base_version: 当前 active baseline
target: owner-supplied mechanism
subject_id: pending until hypothesis/trial registration
evidence_state: hypothesis_ready if accepted for triage
writes: Research/idea_tree only if owner asks to register; no code until ready
agent_mode: 纯 triage 用 role_only；变成代码或正式证据后用 real_multi_agent
agent_instance_mode: 纯 triage 用 role_only；进入正式证据后用 named_owner_thread
runner_scope: none for triage; formal_runner only after gate passes
formal_runner_allowed: false until real_multi_agent gate passes
formal_evidence_allowed: false during triage
agent_runtime_gate: not_required until code or Runner starts
multi_agent_preflight: not_required during triage; required before formal Runner
gates: source_status, interface_contract
blocked_reason: formal run blocked until real_multi_agent gate exists
next_action: judge whether this is inbox idea, ready idea, or blocked by missing source/scope
```

### 全自动研究 Campaign

```yaml
owner_phrase: 全自动研究 campaign
task_type: autonomous research campaign
base_version: 当前 active baseline，除非 owner 指定其它版本
target: workflow-managed source intake, idea discovery, experiments, evidence, final result and code
subject_id: campaign id after campaign creation
evidence_state: hypothesis_ready for first accepted subjects
writes: campaign ledger + idea_tree + experiments + Research + Warehouse
agent_mode: real_multi_agent，因为 workflow 会调度多类实验并产出最终证据
agent_instance_mode: named_owner_thread, lifecycle workflow_scoped; persistent_thread optional for cross-workflow coordinator/monitor
runner_scope: formal_runner per formal batch
formal_runner_allowed: false until campaign/workstream/run preflight passes
formal_evidence_allowed: false for any batch without real_multi_agent evidence chain
agent_runtime_gate: required for every formal runner-start transition
multi_agent_preflight: required at campaign level and before every formal Runner batch
owner_monitor_mode: true; owner watches the campaign, agents write activity updates
agent_activity_stream: required at campaign level and per formal Runner batch
gates: source_status, baseline_repro_status, interface_contract, metric_semantics, artifact_boundary, quality_gate, promotion_gate
blocked_reason: formal batches blocked when real_multi_agent support is absent
next_action: create campaign brief from sources, evaluation standard, safety boundaries, experiment standard, budget, and deliverables
```

### 任意组合实验

```yaml
owner_phrase: 跑10创新+100调参
task_type: mixed experiment campaign
base_version: 当前 active baseline，除非 owner 指定其它版本
target: requested_mix innovation=10, tune=100
subject_id: campaign id after campaign creation
evidence_state: campaign planning, then per-task evidence_state
writes: experiments/campaigns + each workstream's canonical experiment directory + Warehouse
agent_mode: real_multi_agent，因为多个 workstream 需要隔离规划、运行、分析和质量检查
agent_instance_mode: named_owner_thread, lifecycle campaign_scoped/workstream_scoped/task_scoped/run_scoped
runner_scope: formal_runner per formal batch
formal_runner_allowed: false until campaign/workstream/run preflight passes
formal_evidence_allowed: false for any batch without real_multi_agent evidence chain
agent_runtime_gate: required at campaign level and before each formal runner batch
multi_agent_preflight: required at campaign level and before each formal Runner batch
owner_monitor_mode: true; no silent server-only run
agent_activity_stream: required; every report names role, action, evidence, next
gates: baseline_repro_status, source_status, interface_contract, metric_semantics, artifact_boundary, quality_gate
blocked_reason: formal batches blocked when real_multi_agent support is absent
next_action: parse requested_mix, create campaign manifest, build workstreams, and freeze campaign plan before Runner starts
```
