# GTPJ 工作流

本目录不再要求作为一整片协议森林来阅读。

`WORKFLOW_MANIFEST.yaml` 是当前文档瘦身索引：它把 workflow 文件标成
`daily_entry`、`core`、`playbook`、`protocol`、`reference`、`agents` 和
`archive`。日常只看入口和一个 playbook；长协议只按 playbook 点名读取。

日常规则：

```text
先读 START_HERE.md
再读 WORKFLOW_KERNEL.md
再读一个相关 playbook
只有路由不清楚或 playbook 明确要求时，才读 core/protocols/reference/archive
```

## 当前有效入口

| 文件 | 用途 |
|---|---|
| `START_HERE.md` | 人话入口。每个 GTPJ 工作流任务先从这里开始。 |
| `WORKFLOW_KERNEL.md` | 不可破坏的核心规则：证据、agents、版本、保留策略和安全边界。 |
| `WORKFLOW_MANIFEST.yaml` | 机器可读文档索引。 |
| `WORKFLOW_FILE_MAP.md` | 说明哪些文件是有效入口、参考资料、历史记录或模板。 |

## Core 文件

| 文件 | 用途 |
|---|---|
| `core/QUICK_START.md` | 人话短口令备忘。 |
| `core/WORKFLOW_ROUTER.md` | 完整路由表。任务类型模糊或混合时再读。 |
| `core/TASK_START_MINI.md` | 给 owner 看的精简启动摘要。 |
| `core/TASK_START_CARD.md` | 正式写入或运行前的完整 Coordinator 启动卡。 |
| `core/AGENT_RUNTIME_HARD_GATE.md` | 正式 Runner 启动前的左侧命名 Codex 线程硬门。 |

## 执行卡 Playbooks

每种任务只选一个执行卡：

```text
docs/workflow/playbooks/paper_intake.md
docs/workflow/playbooks/paper_to_experiment.md
docs/workflow/playbooks/tune.md
docs/workflow/playbooks/ablation.md
docs/workflow/playbooks/confirmation.md
docs/workflow/playbooks/innovation.md
docs/workflow/playbooks/promotion.md
docs/workflow/playbooks/mixed_campaign.md
docs/workflow/playbooks/autonomous_campaign.md
```

这些 playbook 是很薄的操作卡，只在任务真的需要细节时才指向旧的长协议。

## 当前简化规则

旧的详细文件保留作审计和边界场景参考，不再作为日常必读。

如果多个工作流文件冲突，按下面优先级处理：

```text
本轮 owner 明确要求
WORKFLOW_KERNEL.md
START_HERE.md
core/WORKFLOW_ROUTER.md
core/TASK_START_CARD.md
被选中的 playbook
protocols/reference 文件
archive 历史文件
```

GitHub 仍然是工作流规范的权威来源。本地 Codex skill 只是执行镜像，工作流规则改变后必须同步。

正式实验的最短硬门：

```text
START_HERE.md
-> WORKFLOW_KERNEL.md
-> 相关 playbook
-> core/TASK_START_CARD.md
-> core/AGENT_RUNTIME_HARD_GATE.md
-> validate-agent-runtime
-> multi-agent-preflight
-> Runner
```

正式待跑实验的最短查询链是：

```text
experiments/vX/<type>/INDEX.md
-> experiments/vX/<type>/<TYPE-xxx>/PARAMETER_MATRIX.csv
-> 旧 experiments/module_trials/... 仅由 legacy_ref 回查
-> .gtpj_runtime/batches/<run_id> 只核对执行状态
```

`.gtpj_runtime` 不是正式待跑表；没有正式表格行的运行目录统一视为 `orphan_runtime_plan`。

组合实验用同一个入口自动路由：

```bash
python workflow/gtpj_workflow.py start --phrase "跑2创新+8调参"
```

论文到实验闭环用桥接执行卡，不直接从 paper intake 开训；正式实验必须由 owner 指定 base version：

```bash
python workflow/gtpj_workflow.py start --phrase "基于 v5 从论文开始做实验"
```

最小闭环是：

```text
plan -> agent_runtime -> preflight -> runner -> evidence -> cleanup -> sync
```

不要为了“完整”默认搬运或阅读整个 `docs/workflow/`。

检查当前瘦身索引：

```bash
python workflow/gtpj_workflow.py list-workflow-files
python workflow/gtpj_workflow.py validate-workflow-consistency
```
