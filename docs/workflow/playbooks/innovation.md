# 执行卡：创新 / Module Trial

当 owner 要求开新模块、测试新机制或把 idea 落成代码时使用。

## 必读

```text
START_HERE.md
WORKFLOW_KERNEL.md
GZSL_HARD_RULES.md
innovation_decomposition_protocol.md
idea_tree_protocol.md
module_trial_protocol.md
code_interface_contract.md
innovation_code_review_protocol.md
agent_orchestration.md
agent_report_policy.md
AGENT_RUNTIME_HARD_GATE.md
```

## 角色

正式创新工作必须使用 `real_multi_agent`。

默认角色：

```text
总控 (Coordinator)
阅读/规划 (Reader/Planner)
实现者 (Implementer)
接口检查 (Interface Checker)
运行监控 (Runner Monitor)
日志分析 (Log Analyst)
证据质量检查 (Evidence Quality Checker)
结果比较 (Result Comparator)
复核者 (Reviewer)
```

同一个代码路径只能有一个实现者 (Implementer)。

正式 Runner 启动前必须先启动右侧临时 agents，写 `agent_runtime.yaml`，并通过
`validate-agent-runtime`。如果只是 Coordinator 单窗口代办 Review 0-3，本轮不能作为
正式 `real_multi_agent` 创新证据。

## 创新拆解

创新必须按下面层级管理：

```text
Paper
-> Claim / Mechanism
-> Hypothesis
-> Interpretation
-> Attachment Point
-> Trial
-> Attempt
```

`Hypothesis` 是科学假设；`Trial` 是该假设在某个接入点和实现契约下的一次工程绑定；
`Attempt` 才是同一 Trial 内的参数、seed、epoch、权重或 top-k 尝试。

同一个 Hypothesis 加到不同位置，通常新开 Trial；只调参数才留在 Attempt。

## 复核循环

保留 Review 0-3：

```text
Review 0: 编码前检查 idea 和接口
Review 1: 检查实现边界
Review 2: 检查 runtime 和 evidence readiness
Review 3: 检查结果和 promotion 边界
```

## 输出

```text
idea_tree/
experiments/module_trials/<IDEA-ID>/TRIAL-xxx/
需要长推理时写 GTPJ_Research
raw logs/checkpoints 写 GTPJ_Warehouse
```

## 阻断门

- 没有有效 idea id 或 owner 接受的 local heuristic。
- interface semantics 不清楚。
- attempt 改变了实现假设，应该新开 trial。
- 没有真实右侧临时 agents、没有 `agent_runtime.yaml` 或 `validate-agent-runtime` 未通过。
- 正式 multi-agent 支持不可用，且 owner 没有接受 debug-only 降级。
