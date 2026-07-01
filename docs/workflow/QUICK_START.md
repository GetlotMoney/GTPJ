# GTPJ Workflow Quick Start

## 默认 agent 模式

真实实验默认使用 `real_multi_agent`，但不再默认要求各角色复用 `persistent_thread`。默认形态是：

```yaml
activation_mode: real_multi_agent
agent_instance_mode: temporary_subagent
lifecycle: workflow_scoped
```

含义：当前 workflow / campaign 期间，每个角色都有独立活上下文；workflow 结束后，正式状态沉淀到
`agent_summary.md`、`result.yaml`、`quality_check.md`、Research、Warehouse 和 GitHub 账本。

`role_only` 只用于纯只读、候选 triage、机械账本格式整理，或明确不进入正式证据的 debug/smoke。Runner 仍然串行；Log Analyst、Quality Checker、Result Analyst、Reviewer 等复核角色应独立上下文并行执行。

长期 agent 不是永久聊天窗口。长期 agent 是 `profile.md`、`memory.md`、by-experiment 调用规则、历史
`agent_summary.md` 和 issues。`persistent_thread` 只是跨 workflow 的可选活上下文；当 owner 明确需要右侧持续可见追踪，或某个角色需要跨多轮 campaign 保留连续上下文时才启用。

全自动长周期目标见 `docs/workflow/autonomous_research_campaign.md`：owner 只给论文来源、评估标准、安全边界和实验标准，workflow 负责从 0 到最终代码和结果的完整调度。

本文件是 owner 日常入口。它把完整 workflow 压成几句人话口令；底层
`WORKFLOW_ROUTER.md`、`TASK_START_CARD.md`、agent、artifact、quality 和 promotion
规则仍然有效，由 Coordinator 自动展开。

只想预览某句口令会怎样展开时，可以运行只读 helper：

```bash
python workflow/gtpj_workflow.py start --phrase "开新模块"
python workflow/gtpj_workflow.py repro-status --version v3
```

这些命令只输出 mini 启动卡或复现状态，不写文件、不建分支、不跑训练。

## 1. 人话口令

| 你说 | 默认含义 |
|---|---|
| `查状态` | 只读检查仓库、当前分支、active baseline 复现状态、队列和阻塞项，不改文件。 |
| `复现` | 默认先判定当前 active baseline 是否已复现；未要求正式确认时走最快 `quick_local` 或准备路径。 |
| `调参` | 默认基于当前 active baseline 生成最多 3 个候选；执行前再确认具体参数和成本。 |
| `消融` | 默认判断是 version-level ablation 还是 trial-internal narrow ablation，并先检查接口门。 |
| `开新模块` | 默认基于当前 active baseline，从该版本 selected ready idea 队列自动选一个新 module trial，不 push。 |
| `开下一个新模块` | 明确按当前版本 selected 队列继续推进下一个 ready idea。 |
| `试这个：<一句话想法>` | 把一句话想法路由为 local heuristic idea、idea inbox 或可开 trial 的候选。 |
| `全自动研究 campaign` | owner 给论文来源、评估标准、安全边界和实验标准；workflow 自行安排 paper intake、idea、tune、ablation、confirmation、trial、promotion 和最终交付。 |
| `继续上一个` | 不新开 idea，继续当前 trial 或 attempt；先确认当前 trial 状态和下一步最小动作。 |
| `别问，给我三个候选` | 只读 `idea_tree` / Research，列 3 个可开候选，不改代码。 |
| `升版本` | 检查 promotion gate；只有证据完整且记录明确时才进入 promotion。 |
| `切版本` | 只在 owner 明确要求时执行 activate-version；set-current-version 只切 idea_tree 视图。 |

## 2. 可复现状态优先

任何状态检查、结果比较、promotion 或打 tag 前，Coordinator 必须先查 baseline 复现状态：

```bash
python workflow/gtpj_workflow.py repro-status --version <vX>
```

判定规则：

```text
confirmation_status: confirmed 且 confirmed_H 不是 pending -> 可以当 confirmed baseline。
只有 best_observed_H、confirmed_H=pending 或 status=owner_activated_unconfirmed -> 只能当未确认参考。
```

mini 启动卡的 `gates` 必须包含 `baseline_repro_status`。未确认版本可以作为 active code 和
实验起点，但不能被说成 confirmed baseline，也不能仅凭它阻断或通过 promotion/tag。

## 3. `开新模块` 的默认展开

当 owner 只说 `开新模块` 或 `开下一个新模块` 时，Coordinator 默认执行：

```text
1. 只读检查仓库状态、active baseline 和当前分支。
2. 读取当前 active baseline 的 idea 视图，例如 idea_tree/versions/v3.md。
3. 找 selected 且无 blocker 的最高优先级 idea。
4. 检查 idea_id、source/ref/status、version_scores、hypothesis、scope、risk 是否齐全。
5. 输出 mini 启动卡，说明能不能开工和下一步最小动作。
6. 如果能开工，创建 dev/vX-idea-xxxx-trial-001-slug 分支和 trial 目录。
7. 进入 Review 0-3、实现、attempt、Warehouse artifact、GitHub 账本闭环。
8. 不 push，除非 owner 明确说提交推送。
```

当前 active mainline 是 `GTPJ-v3 / tag v3` 时，`开新模块` 默认基于 `v3`。未来 active
baseline 改变后，默认跟随新的 active baseline。

## 4. Ready Idea 条件

可以被 `开新模块` 自动选择的 idea 必须同时满足：

```text
status 或队列状态: selected / ready
blockers: empty
source_type: paper / user / observation / cross_domain / hybrid
source_status: verified 或 local_heuristic
source_ref: not empty
version_scores.<active_version>: exists
hypothesis: not empty
implementation_scope: not empty
risk: not empty
```

如果没有 ready idea，Coordinator 只能问一个最小问题，例如：

```text
当前 v3 没有可直接开工的 selected idea。要我先列 3 个候选，还是把你的想法登记成 local heuristic idea？
```

## 5. Owner 不需要说的内部词

下面这些都是后台动作，不应该要求 owner 口头指定：

```text
基于 v3
允许改代码
module trial
innovation workflow
real_multi_agent
Review 0-3
artifact boundary
pre-run freeze
branch name
artifact id
```

Coordinator 必须自动判断这些内容，并在 mini 启动卡里用简短语言说明。

## 6. 最快合规路径

默认选择最快但仍合规的路径：

- 只读、查状态、解释、候选建议：可以 `role_only`。
- 真实 Runner、正式 evidence、结果解释、best/promotion、下一轮高成本实验决策：默认 `real_multi_agent` + workflow-scoped `temporary_subagent`。
- debug/smoke 可以 `role_only`，但结果不能进入 keep / best / promote / confirmation evidence。
- 需要 `real_multi_agent` 时，并行执行只读审查角色；Runner、Implementer、Coordinator 仍串行。
- 跨多天 campaign 可以为 `Workflow Coordinator`、`Runner Monitor` 或 `Result Comparator` 额外启用 `persistent_thread`，但正式证据仍以文件和 artifact 为准。
- 任何时候都不能把隐藏上下文或口头印象当正式证据。

## 7. 收口回答

每次完成后，Coordinator 用短格式汇报：

```text
做了什么：
写了哪里：
验证了什么：
没有做什么，为什么：
下一步：
```
