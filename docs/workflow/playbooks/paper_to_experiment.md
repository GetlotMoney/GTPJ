# 执行卡：论文到实验闭环

当 owner 要求“从论文开始”“论文到实验闭环”“读论文并验证创新”时使用。

这张卡只是把已有链路接起来：paper intake 负责来源和创新提取；idea_tree 负责选择和排队；
module trial / experiment 负责正式验证；结果必须再反馈回 Research 和 idea_tree。

## 必读

```text
START_HERE.md
WORKFLOW_KERNEL.md
docs/workflow/playbooks/paper_intake.md
docs/workflow/playbooks/innovation.md
docs/workflow/protocols/paper_intake.md
docs/workflow/protocols/idea_tree_protocol.md
docs/workflow/protocols/module_trial_protocol.md
```

正式 Runner 前再读：

```text
docs/workflow/core/AGENT_RUNTIME_HARD_GATE.md
docs/workflow/protocols/agent_cleanup_protocol.md
```

## 最小闭环

```text
paper_inbox
-> source_review
-> idea_candidate
-> formal_IDEA
-> selected_queue
-> trial_preflight
-> runner_evidence
-> idea_feedback
```

## 阶段

1. 论文读取：扫描 `GTPJ_Research/papers/_inbox/` 和 `PAPERS_INDEX.md`，更新
   `paper_meta.yaml`、`reading_notes.md`、`source_review.md`、`code_review.md`、
   `extracted_ideas.md`。
2. 来源复核：记录 `source_status`、`source_ref`、官方代码链接、本地代码路径和 clone commit。
3. 候选创新：粗想法只进 `idea_tree/inbox.md`；成熟机制才创建或更新
   `idea_tree/ideas/IDEA-xxxx_slug/IDEA.md` 和 `idea_tree/idea_tree.json`。
4. 正式 IDEA 门：必须有 `hypothesis`、`implementation_scope`、`risk`、
   `version_scores.<base_version>`、空 blockers，以及可检查的接口影响。
5. 选择队列：只有 owner 或当前计划明确选中后，才写入
   `idea_tree/queues/01_selected_next.md` 或当前版本 view。
6. Trial 预检：按 `innovation.md` 和 `module_trial_protocol.md` 创建 trial 前检查
   base version、分支、接口契约、Review 0 和 artifact 边界。
7. 正式实验：必须生成或读取 `agent_runtime.yaml`，记录真实 `agent_instance_id`
   与 UI 显示名/role 映射，依次通过 `validate-agent-runtime`、`multi-agent-preflight`
   和 `agent-cleanup-plan`，并明确 owner-visible monitor loop。
8. 结果反馈：`record-module-attempt`、`sync-trial-summary`、`closeout-check` 后，更新
   Research 的 `decision_history.md` 或 `experiment_plan.md`，并回写 idea_tree 的
   status、version score、risk、linked_trials 和 next_action。

## 写入边界

```text
Research: 长阅读、长推理、源码复核、失败原因、决策历史
GitHub: paper/source 轻量索引、正式 IDEA、版本评分、trial 结果索引
Warehouse: 正式 runner 的日志、checkpoint、receipt 和大 artifact
```

Paper intake 本身不启动训练，也不直接创建 module trial。
只有通过正式 IDEA 门、进入 selected queue，并由 owner 批准实验后，才允许走 formal Runner。

## 阻断门

- 没有 verified source，且 owner 未接受 local heuristic。
- 没有明确 `source_ref`，或官方代码声明无法反查到本地 clone/失败记录。
- 缺少 `hypothesis`、`implementation_scope`、`risk` 或当前版本评分。
- idea 未进入 selected queue。
- Interface Checker 不能判断接口影响。
- 正式实验前缺少真实右侧 temporary agents、`agent_runtime.yaml`、preflight 或 cleanup plan。
- 阶段结束时没有汇报 keep / close / unknown agents，或 completed agents 未关闭并记录 `close_result`。

## 启动口径

Owner 只说“从论文开始”时，默认先做只读 intake 和候选排序：

```text
能不能开工：能做论文读取和候选提取；不能直接训练。
任务类型：paper -> idea -> module trial closed loop。
当前最小动作：读取 PAPERS_INDEX/_inbox，列出候选来源和缺口。
正式实验条件：selected IDEA + owner approval + agent_runtime + preflight + cleanup plan。
```
