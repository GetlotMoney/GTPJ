# Workflow Changelog

## workflow-v1

原始的大范围 workflow 协议集合。

## workflow-v1.5

面向 owner 的精简 workflow：

```text
START_HERE.md
WORKFLOW_KERNEL.md
task playbooks
TASK_START_MINI.md
TASK_START_CARD.md
```

日常 workflow 不再需要读完整 protocol 目录也能使用。

## workflow-v2

证据路由内核：

```text
subject_id / subject_type
TRANSITIONS.jsonl
evidence_routing.yaml
transition hash chain
agent propose/check/apply permissions
GZSL hard rules
innovation hypothesis decomposition
validate-evidence-routing
```

目标不是增加更多文档，而是让状态迁移可机器检查，并让 authority refs 清晰可追踪。

## workflow-v2 runtime gate

新增正式 Runner 启动硬门：

```text
AGENT_RUNTIME_HARD_GATE.md
agent_runtime.yaml
validate-agent-runtime
left_sidebar_named_threads
```

正式实验现在要求真实 named threads，并在 Runner 启动前记录 `agent_instance_id`
和 pre-run allow/check。Coordinator 单窗口执行只能算 candidate/debug evidence，
不是完整 `real_multi_agent` workflow。

## workflow-v2 legacy UI-agent cleanup

新增 owner 可见的 agent cleanup 规则：

```text
thread_archive_policy: archive_completed_threads_on_stage_end
archive_completed_threads_on_stage_end: true
archived_threads_record: AGENT_ACTIVITY.md
```

在 workflow 或阶段 closeout 时，Coordinator 必须记录 keep/close lists，把已完成 agent
结论沉淀到 `agent_summary.md` / `AGENT_ACTIVITY.md` / result / quality / issues / memory，
然后归档 completed named threads。左侧栏应该显示当前 active roles，而不是历史窗口。

## workflow-v2 formal multi-agent preflight

收紧正式 evidence 规则：

```text
formal_runner_allowed: true
formal_evidence_allowed: true
multi_agent_preflight
agent_instance_status / agent_status_refs / agent_output_refs
multi-agent-preflight helper
```

如果无法证明真实 multi-agent，正式 Runner start 必须阻断。`role_only` 和顺序结构化 review
仍可用于只读 triage、drafts 和 debug/smoke，但不能事后升级为 formal evidence。
helper 现在会验证每个 recorded temporary sub-agent 的本地 status/output evidence files；
Codex tool state 必须沉淀到这些文件中，因为 Python helper 不能直接查询隐藏 chat-tool sandbox state。
