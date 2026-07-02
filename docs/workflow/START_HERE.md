# GTPJ 工作流入口

这是每个 GTPJ 任务的精简入口，用来取代“每次都读完整 workflow 目录”的旧习惯。

## 1. 先判断模式

使用仍然合规的最小模式：

| 请求 | 模式 |
|---|---|
| 解释、检查、汇报状态、列候选 | `role_only` |
| 启动或监控真实 runner、记录正式证据、比较 best、影响下一轮高成本实验、改变代码/配置语义、准备 promotion | `real_multi_agent` |
| 不计入证据的 debug/smoke | 可以 `role_only`，但结果不能作为正式 evidence |

正式实验默认：

```yaml
activation_mode: real_multi_agent
agent_instance_mode: temporary_subagent
lifecycle: workflow_scoped
owner_monitor_mode: true
owner_role: monitor
owner_visible_reporting: true
```

`persistent_thread` 只是可选的可见长期上下文，不是正式证据。

Owner 是默认监控者。正式 Runner 启动后，Coordinator 不能只发一次 final 就结束可见流程；
必须持续用当前对话或明确的 Monitor 线程汇报：

```text
哪个智能体在做什么
当前 run/batch 状态
证据写到哪里
下一步动作
如果主对话暂停，去哪里接着看
```

正式 Runner 启动还必须通过：

```text
AGENT_RUNTIME_HARD_GATE.md
agent_runtime.yaml
python workflow/gtpj_workflow.py validate-agent-runtime --path <agent_runtime.yaml>
```

没有右侧临时 agents、没有真实 agent id、没有 pre-run allow/check，就不能启动正式 Runner。
这种情况只能降级为 debug/smoke 或候选线索。

## 2. 最小阅读顺序

除非任务需要更多细节，否则只读这条链：

```text
1. START_HERE.md
2. WORKFLOW_KERNEL.md
3. docs/workflow/playbooks/ 下的相关 playbook
4. 只有路由模糊或混合任务时才读 WORKFLOW_ROUTER.md
5. 汇报启动摘要前读 TASK_START_MINI.md
6. 正式写入或运行前读 TASK_START_CARD.md
```

不要默认深读所有旧协议。

## 3. 用户人话路由

| 用户说 | 默认路由 | 执行卡 |
|---|---|---|
| `汇报`, `查状态`, `现在怎么样` | 只读状态检查 | 无，使用 `WORKFLOW_KERNEL.md` |
| `读论文`, `找创新点` | 论文读取 / idea discovery | `playbooks/paper_intake.md` |
| `调参` | 调参 Tune | `playbooks/tune.md` |
| `消融` | 消融 Ablation | `playbooks/ablation.md` |
| `复现`, `确认这个结果` | 复现确认 Confirmation | `playbooks/confirmation.md` |
| `开新模块`, `试这个想法` | 创新 / module trial | `playbooks/innovation.md` |
| `升版本` | 升版 Promotion | `playbooks/promotion.md` |
| `跑10创新+100调参` 或任意数量组合 | 混合实验 campaign | `playbooks/mixed_campaign.md` |
| `全自动研究campaign`, `从论文到最终结果都接管` | 全自动研究 campaign | `playbooks/autonomous_campaign.md` |

## 4. 启动摘要

在改文件、跑实验、记录结果或选择 best 前，先汇报：

```text
能不能开工：
任务类型：
基于版本/分支：
baseline_repro_status：
comparison_reference：
是否进入 idea_tree：
GitHub 写入：
Research/Warehouse 写入：
agents 模式：
必须读的 playbook：
硬门：
agent_runtime_gate：
owner_monitor_mode：
agent_activity_stream：
当前阻塞：
下一步最小动作：
```

如果只是状态汇报，保持简短即可。

## 5. 证据优先

不要让聊天记忆变成正式证据。

正式证据只来自：

```text
manifest.yaml
result.yaml
result.md
quality_check.md
agent_summary.md
ATTEMPTS.md
batch_status.json
Warehouse logs/checkpoints/receipts
必要时的 Research source notes
```

如果某个结论会影响 keep/drop/best/repeat/promotion/versioning 或下一轮高成本实验，就必须能追溯到文件或 artifact。

debug/smoke 结果必须显式锁定为：

```yaml
evidence_level: debug_smoke
formal_evidence: false
eligible_for_keep_best_promotion_confirmation: false
```
