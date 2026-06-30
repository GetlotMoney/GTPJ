# Task Start Mini Card

本文件定义 owner 可见的极简启动卡。完整 `TASK_START_CARD.md` 仍然是正式审查模板，但默认由
Coordinator 在后台展开；owner 日常只看本文件的 8 个字段。

只读预览入口：

```bash
python workflow/gtpj_workflow.py start --phrase "开新模块"
```

该命令只打印下面的 8 字段，不写文件、不建分支、不跑训练。

## 1. Mini 启动卡

```yaml
owner_phrase:
task_type:
base_version:
target:
writes:
agent_mode:
agent_instance_mode:
gates:
next_action:
```

字段含义：

| 字段 | 含义 |
|---|---|
| `owner_phrase` | owner 的原始口令，例如 `开新模块`、`复现`、`试这个：...`。 |
| `task_type` | Coordinator 路由后的任务类型。 |
| `base_version` | 默认当前 active baseline；只有 owner 明确指定时才改历史版本。 |
| `target` | 本次目标，例如 baseline、参数、idea、trial 或候选列表。 |
| `writes` | 本次会写哪里；只读任务写 `none`。 |
| `agent_mode` | `role_only` 或 `real_multi_agent`，附一句为什么。 |
| `agent_instance_mode` | `role_only`、`persistent_thread` 或 `temporary_subagent`；正式实验默认 `persistent_thread`。 |
| `gates` | 本次真正相关的硬门，只列会影响开工的门。 |
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
base_version: current active baseline
target: next selected ready idea
writes: idea_tree + experiments/module_trials + Warehouse after run
agent_mode: real_multi_agent, because new module code changes require Review 0-3
agent_instance_mode: persistent_thread
gates: source_status, interface_contract, innovation_code_review, artifact_boundary
next_action: read active version idea view and select the highest-priority ready idea
```

### 复现

```yaml
owner_phrase: 复现
task_type: confirmation
base_version: current active baseline
target: current baseline result
writes: none until owner confirms run and evidence level
agent_mode: real_multi_agent for a formal run; role_only only for preparation before Runner starts
agent_instance_mode: persistent_thread for a formal run
gates: baseline_repro_status, metric_semantics, evidence_level, artifact_boundary
next_action: run repro-status, then decide quick_local vs formal confirmation target
```

### 试这个

```yaml
owner_phrase: 试这个：把 <机制> 接到 <位置>
task_type: local heuristic idea or innovation / module trial
base_version: current active baseline
target: owner-supplied mechanism
writes: Research/idea_tree only if owner asks to register; no code until ready
agent_mode: role_only for pure triage; real_multi_agent if it becomes code or formal evidence
agent_instance_mode: role_only for pure triage; persistent_thread if it becomes formal evidence
gates: source_status, interface_contract
next_action: judge whether this is inbox idea, ready idea, or blocked by missing source/scope
```
