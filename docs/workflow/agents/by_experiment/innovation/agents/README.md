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
Coordinator -> Reader/Planner -> Implementer -> Interface Checker -> Runner -> Quality Checker + Result Analyst + Reviewer -> Coordinator
```

## 关键规则

- 只读取 `idea_tree/versions/<base_version>.md` 中已选中的 idea。
- 不从总创意表直接启动 trial。
- Implementer 只改当前 trial 代码路径。
- Interface Checker 必须检查 off switch、shape、loss、eval、logits、label mapping、seen/unseen split 和 class order。
- Runner 串行运行。
- Runner 只写 Warehouse raw artifacts，GitHub 只保存 manifest/result/quality/code.diff 等轻量证据。
- Reviewer 独立检查污染、遗漏和误判。
- Coordinator 必须写 `agent_summary.md`；Reviewer 或长报告可进入 Warehouse，由 GitHub 引用 artifact id。
- 失败 trial 保留证据，不合并失败代码。
- `trial_decision: promote` 且 `promotion_decision: promote` 时，转交 promotion agents。
