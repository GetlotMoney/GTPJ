# Long-Term Agent Memory

本文件定义 GTPJ 的长期 agent 记忆机制。目标是让每个角色有可复用的身份、规则和经验，同时不把任何聊天上下文误当正式证据。

## 核心定义

长期 agent 不是永久在线聊天窗口，也不是某个必须常驻的 thread。

正式 GTPJ workflow 中，一个长期 agent 由文件化身份和历史凭证构成：

```text
shared_roles/<role>/profile.md
shared_roles/<role>/memory.md
by_experiment/<task_type>/agents/README.md
agent_summary.md
review_round_*.md
docs/workflow/issues/YYYY-MM-DD-*.md
```

运行期 agent 实例可以是：

```text
temporary_subagent   # 本轮 workflow / campaign 的活上下文
persistent_thread    # 跨 workflow 的活上下文，可选
role_only            # 主 agent 按角色清单执行，没有独立活上下文
```

`temporary_subagent` 可以在整个 workflow 或 campaign 阶段内持续存在。它不是“短到只能做一次性检查”的工具，而是本轮独立上下文。

`persistent_thread` 负责跨 workflow 保留角色自己的连续对话经验和可见追踪过程，但它可能压缩、漂移或丢失局部细节，所以不能单独作为正式证据。

进入 `result.yaml`、`quality_check.md`、promotion 证据或正式结论前，所有 memory/thread/context-derived fact 都必须回到当前 repo、Research、Warehouse artifact 或日志验证。

正式 `real_multi_agent` 默认使用：

```yaml
agents:
  activation_mode: real_multi_agent
  agent_instance_mode: temporary_subagent
  lifecycle: workflow_scoped
```

长周期 autonomous research campaign 可以把 `lifecycle` 写成 `campaign_scoped`。只有跨多个 workflow 的角色才使用：

```yaml
agents:
  agent_instance_mode: persistent_thread
  lifecycle: cross_workflow
```

## 每个角色的长期文件

每个 `shared_roles/<role>/` 至少包含：

```text
profile.md  # 身份、职责、读写边界、失败条件
memory.md   # 长期经验、重复错误、固定检查项
```

`memory.md` 使用下面结构：

```text
# <Role> Memory

## Standing Lessons
长期有效经验。

## Recurrent Failure Modes
重复出错模式和预防规则。

## Required Checks
每次执行该角色都必须检查的事项。

## Update Rules
什么时候更新本文件。
```

## 启动加载规则

Coordinator 激活某个角色时，必须让该角色读取或显式接收：

```text
1. shared_roles/<role>/profile.md
2. shared_roles/<role>/memory.md
3. by_experiment/<task_type>/agents/README.md
4. docs/workflow/issues/README.md 和最近相关问题文档
5. 当前 task start card
6. 如启用 persistent_thread，则提供 thread id / visible label
```

真实多 agent 下，Coordinator 必须在 sub-agent 任务说明里写明这些输入文件，不能假设 sub-agent 自动知道主 agent 的隐藏上下文。

Task Start Card 和 Agent Summary 必须记录：

```text
agent_instance_mode: temporary_subagent | persistent_thread | role_only
lifecycle: workflow_scoped | campaign_scoped | cross_workflow | role_only
persistent_thread_id: <id/label> 或 not_used
persistent_thread_reused: yes | no | not_applicable
temporary_subagent_reason:
output_locations:
```

## 记忆写回规则

每次任务结束时，Coordinator 检查是否需要写回长期记忆：

| 触发 | 写入位置 |
|---|---|
| 本次具体问题、失败、修复 | `docs/workflow/issues/YYYY-MM-DD-*.md` |
| 某角色反复犯同类错误 | `shared_roles/<role>/memory.md` |
| 多角色共同边界问题 | `docs/workflow/agent_orchestration.md` 或 `agent_report_policy.md` |
| 重复后处理动作 | `workflow/gtpj_workflow.py` helper 或 sync check |

规则：

- 新问题出现 1 次，先写 issue 或本次 `agent_summary.md`。
- 同类问题出现 2 次，写入对应角色 memory。
- 同类手工后处理出现 3 次，升级成 helper 或自动校验。
- 临时 agent 关闭前必须把可复用发现写回上述位置之一。

## 证据边界

`memory.md` 是提醒和检查清单，不是实验事实源。进入正式结论前仍必须验证：

```text
当前 repo 文件
commit / tag
config / manifest / result / quality_check
Warehouse artifact
Research source review
server batch_status / logs
```

未验证的 memory-derived fact、persistent-thread-derived fact 或 temporary-context-derived fact 不能写入
`result.yaml`、`quality_check.md`、promotion 证据或正式结论。

## 自动对齐

长期 agent 体系需要被 sync check 覆盖：

- GitHub `docs/workflow/agents/` 中每个角色都有 `profile.md` 和 `memory.md`。
- 本地 `gtpj-workflow` skill 镜像这些文件。
- Task Start Card 和 Agent Summary 记录实际读取了哪些 profile / memory 文件。
- 如果使用 persistent thread，记录 thread id 或 visible label。
- 如果使用 workflow-scoped temporary agents，记录 lifecycle、independence scope 和 output locations。
- 如果 GitHub 和本地 skill 不一致，GitHub 为准，并阻断正式实验或先同步 skill 镜像。
