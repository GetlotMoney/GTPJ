# 执行卡：创新 / Module Trial

当 owner 要求开新模块、测试新机制或把 idea 落成代码时使用。

## 必读

```text
START_HERE.md
WORKFLOW_KERNEL.md
docs/workflow/reference/GZSL_HARD_RULES.md
docs/workflow/reference/innovation_decomposition_protocol.md
docs/workflow/protocols/module_template_selection.md
docs/workflow/protocols/idea_tree_protocol.md
docs/workflow/protocols/module_trial_protocol.md
docs/workflow/protocols/code_interface_contract.md
docs/workflow/protocols/innovation_code_review_protocol.md
docs/workflow/protocols/agent_orchestration.md
docs/workflow/protocols/agent_report_policy.md
docs/workflow/core/AGENT_RUNTIME_HARD_GATE.md
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
`validate-agent-runtime` 和 `multi-agent-preflight`。如果只是 Coordinator 单窗口代办
Review 0-3，本轮不能作为正式 `real_multi_agent` 创新证据。

## 探索 / 正式分界

探索性 trial 只允许做这些事：

```text
idea triage
接口草图
debug_smoke
本地 shape / script / speed probe
```

探索性输出必须写：

```yaml
formal_evidence: false
evidence_level: debug_smoke
formal_runner_allowed: false
formal_evidence_allowed: false
eligible_for_keep_best_promotion_confirmation: false
```

正式 module trial 才能登记 attempt/result、选择 best、影响下一轮高成本实验或进入
promotion。正式路径必须通过真实 `real_multi_agent` gate；不能把探索性结果事后补签成
正式证据。

探索性结果如果看起来有价值，升级路径只能是重新跑正式证据：

```yaml
upgrade_path:
  exploration_run:
    kept_as: exploration_ref
    evidence_level: debug_smoke
    formal_evidence: false
  formal_rerun_required:
    - real_multi_agent
    - agent_instance_status / agent_status_refs / agent_output_refs
    - Review 1-3
    - frozen config
    - min3 confirmation when used for confirmed_H or promotion
  forbidden:
    - promote exploration run in place
    - rewrite debug_smoke as valid_single_run
    - use sequential review as formal audit
```

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

## 模板选择

新 module trial 必须先按 `docs/workflow/protocols/module_template_selection.md` 选模板。

```text
feature_adapter
fusion_gate
auxiliary_loss
sampler_or_data_view
```

选择原则：先确定论文/idea 的 mechanism claim，再找 attachment point，最后选最窄模板。
如果 owner 没有明确 `base_version` / `base_code_tag`，只能做 idea discovery，不能开正式 trial。

每个新模块必须写 trial-local `module_source.md`，说明模块来源、论文机制、GTPJ 适配方式、
模板族、接入点、baseline-off 解释和之后写论文可用的表述。

## 代码流程图

只要创新会改变代码逻辑、forward、loss、evaluation、输入输出或关键张量流向，Trial
`README.md` 必须有 `## Code Flow Diagram`：

```text
input tensors -> changed modules / gates / branches -> logits / loss / metrics
```

这张图是 owner 读代码路径的入口，不替代 `framework_diagram.md`。完整变量 glossary、
method glossary、loss flow、baseline-off 和 code-vs-intent 仍写入 trial 级
`framework_diagram.md`。

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
- 论文创新要做实验但缺少 owner 明确指定的 base version / base code tag。
- 没有 `module_source.md` 或没有选择 module template family。
- interface semantics 不清楚。
- attempt 改变了实现假设，应该新开 trial。
- 没有真实右侧临时 agents、没有 `agent_runtime.yaml` 或 `validate-agent-runtime` 未通过。
- 正式 multi-agent 支持不可用。owner 只能把本轮改成 debug-only 排障；不能继续正式 trial。
