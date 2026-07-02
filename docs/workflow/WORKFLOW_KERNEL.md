# GTPJ 工作流内核

本文件是精简后的硬规则层，应该保持短而稳定。

## 1. 权威来源

- GitHub 是可复现控制面、治理账本和轻量结果索引。
- `GTPJ_Research` 保存长推理、论文/来源笔记和完整 idea 历史。
- `GTPJ_Warehouse` 保存 raw logs、checkpoints、生成图、运行 receipt 和大型 artifact。
- 聊天上下文、临时 agent 上下文、persistent thread 上下文和 Codex memory 只能辅助定位，不能作为正式证据。

## 2. 正式证据边界

只要任务会影响下面任一内容，就属于正式证据工作：

```text
manifest/result/quality/agent_summary
ATTEMPTS keep/drop/reject/rerun
best 或 top-k 选择
repeat/confirmation
promotion/version/tag 判断
论文或 baseline 表述
下一轮高成本实验
代码/配置/评估语义
```

正式证据工作必须使用 `real_multi_agent`，除非 owner 明确降级为 debug/smoke。
正式 Runner 启动前还必须满足 `docs/workflow/AGENT_RUNTIME_HARD_GATE.md`。也就是说，
状态机记录和服务器 runner 都不能替代真实右侧临时 agents；没有 `agent_runtime.yaml`
和通过的 `validate-agent-runtime`，只能降级为 debug/smoke 或 candidate 线索。

正式证据对象必须绑定 `subject_id` 和 `subject_type`。`evidence_state` 只能由
tamper-evident append-only `TRANSITIONS.jsonl` 派生，`evidence_routing.yaml`
只是当前状态缓存，不能手写覆盖。

debug/smoke 只能用于排障或环境探针，必须记录：

```yaml
evidence_level: debug_smoke
formal_evidence: false
eligible_for_keep_best_promotion_confirmation: false
```

## 3. Agent 规则

正式任务默认：

```yaml
activation_mode: real_multi_agent
agent_instance_mode: temporary_subagent
lifecycle: workflow_scoped
```

含义：

- 每个角色在当前 workflow 或 campaign 阶段拥有独立活上下文。
- 正式运行必须记录真实 `agent_instance_id` 或可见 thread id；`temporary_subagent` 这类占位词不能冒充实例。
- 需要长期保留的经验必须写回 `agent_summary.md`、角色 `memory.md`、workflow issues、result 文件或 campaign 账本。
- `persistent_thread` 只是跨 workflow 可见追踪的可选上下文，不是 evidence。
- 不要给每个实验 run 创建一个永久 agent/thread。
- 角色名要清晰，例如 `运行监控 (Runner Monitor)`、`日志分析 (Log Analyst)`、`证据质量检查 (Evidence Quality Checker)`、`结果比较 (Result Comparator)`。
- `Experiment Runner` 表示实际启动训练命令的运行角色；`Runner Monitor` 表示监控服务器、队列、GPU slot 和失败隔离的运行监控角色。小任务中二者可以由同一 Runner family 承担，但在启动卡和 `agent_summary.md` 里必须写清楚显示名和职责。

写入边界：

- 总控 (Coordinator) 是最终 GitHub 账本 writer。
- 总控 (Coordinator) 是唯一可以 apply evidence transition 的角色。
- 日志/结果角色可以 propose transition；接口/质量/复核角色可以 check transition。
- 运行者 (Runner) 管理服务器/GPU 运行状态。
- 同一个代码路径只能有一个实现者 (Implementer)。
- 阅读/规划 (Reader/Planner)、日志分析 (Log Analyst)、质量检查 (Quality Checker)、结果分析 (Result Analyst)、接口检查 (Interface Checker) 和复核者 (Reviewer) 默认只读，除非明确授权。

## 4. 版本规则

- 只调参数不能开新的 `vX`。
- 新 `vX` 需要 confirmed promoted framework 或 method state，不能只是 tuned config。
- confirmation 默认跑 3 次。复现通过后，正式单值取 3 次中的最高 H，同时保留 mean/min/max 作为稳定性证据。
- promotion 和 baseline claim 默认比较 `confirmed_H` / repeat mean，不能只凭 best repeat。
- 不能把未确认的 `best_observed_H` 说成 confirmed baseline。
- 每个正式版本 `experiments/vX/` 必须有版本级 `framework_diagram.md` 和 `MODULES.md`；`VERSION.md` 必须链接它们并包含 `## Framework Diagram`。模块说明不能只列名字，必须解释 purpose、input、output、config switch 和 baseline-off behavior。

## 5. 运行安全

正式运行前必须记录：

```text
branch 和 commit
git dirty 状态
冻结后的 config
agent_runtime.yaml 及 validate-agent-runtime 结果
dataset/split/label mapping 假设
GPU 或 runner slot 锁
result/artifact 写入位置
checkpoint retention 规则
```

如果 label mapping、seen/unseen split、class order、logits shape 或 metric semantics 不清楚，必须硬阻断。
所有正式实验必须满足 `docs/workflow/GZSL_HARD_RULES.md`。

## 6. Checkpoint 保留规范

工作流规范：

```text
每轮实验结束后删除非保留 checkpoint。
除非 playbook 明确另有规定，否则只保留最好的 3 个模型 checkpoint（Top-3）。
永远不要删除 logs、manifest、result、quality_check 或 Warehouse receipt。
```

删除范围必须限制在实验生成的 checkpoint 内，不能碰用户数据或源码历史。

## 7. Promotion 门

只有证据明确支持时才能开始 promotion：

```text
promotion_decision: promote
完整 manifest/result/quality/interface evidence
必要时有 repeat 或 confirmation evidence
目标版本已声明
没有未解决硬门
```

promotion 可以按协议创建本地文件、commit 和 tag，但不能 push，除非 owner 明确要求。

## 8. 停止规则

遇到下面情况要停止或降级：

- 必要证据缺失。
- 服务器/runtime 状态不清楚，可能污染结果。
- workflow 要求正式多 agents，但当前没有真实 multi-agent 支持。
- `activation_mode: real_multi_agent` 但没有真实右侧临时 agent 实例、pre-run allow/check 或 `agent_runtime.yaml`。
- owner 改变范围。
- 会跨越安全边界。

停止时只汇报最小 unblock 动作。

## 9. 反膨胀规则

新增 workflow 文件、模板或协议前，必须至少满足一项：

```text
可机器检查
能驱动 evidence_state transition
是权威事实源
是正式 evidence 必需模板
```

如果都不满足，不进入日常 workflow。
