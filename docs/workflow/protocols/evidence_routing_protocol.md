# Evidence Routing Protocol

GTPJ workflow-v2 是一个防篡改、只追加的证据状态机。

## Core Object

工作流路由的是具体证据对象，不是抽象聊天结论：

```text
subject_id
subject_type
hypothesis_id
evidence_state
rule_checks
authority_refs
transition
```

## Authoritative History

`TRANSITIONS.jsonl` 是权威状态历史。

`evidence_routing.yaml` 只是物化视图。它的 `current_state` 必须从
`TRANSITIONS.jsonl` 的 chain head 推导出来，不能手工编辑成更强的状态。

每条 transition 必须记录：

```text
previous_transition_id
previous_transition_hash
current_transition_hash
```

哈希基于规范化 UTF-8 JSON 计算，字段按 key 排序，并排除 `current_transition_hash` 本身。

## Transition Authority

agents 不能直接让正式事实成立。

```text
Log Analyst / Result Analyst: propose transition
Interface Checker / Quality Checker / Reviewer: check transition
Coordinator: apply transition
```

只有已经 apply 的 transition 才能更新物化状态。

## Stop And Failure

停止也是一种 transition。失败必须结构化记录为
`transition_type: stop | block | reject | rerun`，必要时同时写明 `failure_type`。

## Fact Source Boundary

campaign 账本可以索引 result refs、quality refs 和 next actions，但不能成为
H/U/S/ZS 的权威来源。

正式事实仍然来自：

```text
manifest.yaml
result.yaml
result.md
quality_check.md
agent_summary.md
ATTEMPTS.md
Warehouse logs/checkpoints/receipts
```

## Helper

使用：

```bash
python workflow/gtpj_workflow.py validate-evidence-routing
```

helper 会检查 transition chain 连续性、哈希正确性、当前状态派生关系、authority refs、
硬规则 verdict，以及 campaign result-index 边界。
