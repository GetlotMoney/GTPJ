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

## 3. Agent 规则

正式任务默认：

```yaml
activation_mode: real_multi_agent
agent_instance_mode: temporary_subagent
lifecycle: workflow_scoped
```

含义：

- 每个角色在当前 workflow 或 campaign 阶段拥有独立活上下文。
- 需要长期保留的经验必须写回 `agent_summary.md`、角色 `memory.md`、workflow issues、result 文件或 campaign 账本。
- `persistent_thread` 只是跨 workflow 可见追踪的可选上下文，不是 evidence。
- 不要给每个实验 run 创建一个永久 agent/thread。
- 角色名要清晰，例如 `运行监控 (Runner Monitor)`、`日志分析 (Log Analyst)`、`证据质量检查 (Evidence Quality Checker)`、`结果比较 (Result Comparator)`。

写入边界：

- 总控 (Coordinator) 是最终 GitHub 账本 writer。
- 运行者 (Runner) 管理服务器/GPU 运行状态。
- 同一个代码路径只能有一个实现者 (Implementer)。
- 阅读/规划 (Reader/Planner)、日志分析 (Log Analyst)、质量检查 (Quality Checker)、结果分析 (Result Analyst)、接口检查 (Interface Checker) 和复核者 (Reviewer) 默认只读，除非明确授权。

## 4. 版本规则

- 只调参数不能开新的 `vX`。
- 新 `vX` 需要 confirmed promoted framework 或 method state，不能只是 tuned config。
- confirmation 默认跑 3 次。复现通过后，正式单值取 3 次中的最高 H，同时保留 mean/min/max 作为稳定性证据。
- 不能把未确认的 `best_observed_H` 说成 confirmed baseline。

## 5. 运行安全

正式运行前必须记录：

```text
branch 和 commit
git dirty 状态
冻结后的 config
dataset/split/label mapping 假设
GPU 或 runner slot 锁
result/artifact 写入位置
checkpoint retention 规则
```

如果 label mapping、seen/unseen split、class order、logits shape 或 metric semantics 不清楚，必须硬阻断。

## 6. Checkpoint 保留规范

工作流规范：

```text
每轮实验结束后删除非保留 checkpoint。
除非 playbook 明确另有规定，否则只保留最好的 3 个模型 checkpoint。
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
- owner 改变范围。
- 会跨越安全边界。

停止时只汇报最小 unblock 动作。
