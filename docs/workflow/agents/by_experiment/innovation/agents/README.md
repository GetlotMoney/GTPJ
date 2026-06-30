# Innovation Agents

创新 workflow 用于 module trial。它只能从对应版本选择清单里的 selected idea 启动。

## 启用角色

```text
Coordinator
Reader / Planner
Implementer
Interface Checker
Runner
Quality Checker
Result Analyst
Reviewer
```

## 编排

```text
Coordinator
  -> Review 0: Reader/Planner + Coordinator
  -> Review 1: Interface Checker
  -> Implementer
  -> Review 2: Interface Checker + Quality Checker + Reviewer
  -> Runner
  -> Review 3: Log Analyst + Quality Checker + Result Analyst + Reviewer
  -> Coordinator
```

## 关键规则

- 只读取 `idea_tree/versions/<base_version>.md` 中已选中的 idea。
- 不从总创意表直接启动 trial。
- 只要 idea / 创新 / module trial 会落成代码改动，必须遵守
  `docs/workflow/innovation_code_review_protocol.md`。
- 本类任务默认 `activation_mode: real_multi_agent`，不得用单 agent 顺序执行冒充真实多 agents。
- 本类任务默认 `agent_instance_mode: persistent_thread`；Reader/Planner、Interface Checker、Quality Checker、Result Analyst、Reviewer 等长期角色优先复用各自 thread。
- 临时 sub-agent 可以开启，但只能作为一次性加速、只读复核或 fallback，必须加载对应长期角色的 `profile.md`、`memory.md` 和本文件，并记录 `temporary_subagent_reason`。
- Review 0 产出 `idea_intent_check.md`，确认 source intent 和 hypothesis。
- Review 1 产出 `interface_precheck.md`，在写代码前确认接口设计。
- Review 2 产出 `review_round_1.md`，在 Runner 前检查 code diff。
- Review 3 产出 `review_round_2.md`，在结果入账、best 或 promotion 前检查证据。
- Implementer 只改当前 trial 代码路径。
- Interface Checker 必须检查 off switch、shape、loss、eval、logits、label mapping、seen/unseen split 和 class order。
- Runner 串行运行。
- Runner 只写 Warehouse raw artifacts，GitHub 只保存 manifest/result/quality/code.diff 等轻量证据。
- Reviewer 独立检查污染、遗漏和误判。
- Coordinator 必须写 `agent_summary.md`；Reviewer 或长报告可进入 Warehouse，由 GitHub 引用 artifact id。
- 失败 trial 保留证据，不合并失败代码。
- `trial_decision: promote` 且 `promotion_decision: promote` 时，转交 promotion agents。
