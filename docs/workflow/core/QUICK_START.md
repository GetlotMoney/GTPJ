# GTPJ 工作流快速入口

## 先认代码起点

- `TEMPLATE.yaml` 登记框架的只读代码母版 `MODEL-VX-TEMPLATE-VN`。
- `EXPERIMENT.yaml` 登记当前实验实际从哪份母版、哪个准确提交开始。
- 没有这两份身份记录，不得启动新的正式实验。

现在的精简入口是：

```text
docs/workflow/START_HERE.md
docs/workflow/WORKFLOW_KERNEL.md
```

本文件只作为 owner 人话短语速查表。

## Owner 三句入口

| owner 口令 | 含义 |
|---|---|
| `本地正式，干净` | 启动 `live_multi_agent_monitor`；确认侧边栏干净，并授权创建本轮左侧命名 Codex 线程；不启动服务器 runner。 |
| `开启多agents智能体工作流，开始` / `开启多agents智能体工作流，跑N轮` | 启动 `live_multi_agent_monitor`；不再反复确认 workflow 模式或启动意图；通过硬门后继续创建角色、生成计划并启动对应 runner。 |
| `服务器冻结，开始` | 启动 `server_frozen_runner`；不创建命名线程，允许走服务器 detached runner。 |
| `只做本地规划` | 使用 `role_only`；只做本地计划、账本、状态和 debug/smoke，不进入正式证据。 |

如果 owner 只说 `本地正式`，Coordinator 只问：`侧边栏干净吗？回复：干净。`

如果 owner 已经说 `开启多agents智能体工作流`、`开始`、`跑N轮` 或 `做N轮实验`，Coordinator 不得再要求长授权模板，也不得把任务停在“只规划”。只有模式不明、侧边栏未确认且无法验证、硬门失败或安全边界动作，才允许再问一次。

## 通用话入口

| 你可以直接说 | Coordinator 必须做 |
|---|---|
| `规划下一轮实验` / `下一轮怎么跑` | 运行 `plan-experiments`，自动读当前 repo、ledger、result/quality 和 runtime context，输出三张规划表。 |
| `批量规划50轮实验` / `给我规划50轮` | 运行 `plan-experiments --max-jobs 50`；只规划，不启动 Runner。 |
| `规划10创新+100调参` / `跑10创新+100调参` | 解析成 mixed campaign workstreams，先出规划表，再进入 campaign gate。 |
| `按这个计划开多agents工作流` | 解释为 `live_multi_agent_monitor`；通过 agent_runtime 和 preflight 后才能启动正式 Runner。 |
| `按这个计划服务器冻结跑` | 解释为 `server_frozen_runner`；训练运行期不创建命名线程，走服务器 detached gate。若涉及代码/helper/template 改动，先完成代码审核门。 |

代码审核不被 `server_frozen_runner` 豁免：改代码、workflow、helper、模板或训练配置生成逻辑时，先跑机器验证，再由两个不同的只读子 Agent 依次做两轮对抗式审核。第 1 轮问题修复、重测并复核通过后才能开始第 2 轮；两轮绑定同一个最终 `reviewed_code_id`，都通过后才允许正式训练。

| 用户短语 | 路由 |
|---|---|
| `汇报`, `查状态` | 只读状态检查。除非明确要求，不写 evidence。 |
| `读论文`, `找创新点` | 论文读取 / idea discovery。 |
| `基于 vX 从论文开始做实验`, `论文到实验闭环` | 论文读取 -> idea_tree -> module trial 的桥接闭环；缺 `vX` 时不能开 trial。使用 `playbooks/paper_to_experiment.md`。 |
| `调参` | 调参 Tune。使用 `playbooks/tune.md`。 |
| `消融` | 消融 Ablation。使用 `playbooks/ablation.md`。 |
| `复现`, `确认结果` | 复现确认 Confirmation。使用 `playbooks/confirmation.md`。 |
| `开新模块`, `试这个想法` | 创新 / module trial。使用 `playbooks/innovation.md`。 |
| `升版本` | 升版门 Promotion gate。使用 `playbooks/promotion.md`。 |
| `跑10创新+100调参` | 混合实验 campaign。使用 `playbooks/mixed_campaign.md`。 |
| `全自动研究campaign` | 全自动研究 campaign。使用 `playbooks/autonomous_campaign.md`。 |

正式任务默认 agent 模式：

```yaml
activation_mode: real_multi_agent
agent_instance_mode: named_owner_thread
lifecycle: workflow_scoped
```

长期 agent 是文件支撑的角色身份和累积证据，不等于必须常驻的聊天窗口。

`persistent_thread` 是可选活上下文，适合可见的长周期监控，但不能替代文件、日志、result、quality check 或 Warehouse artifact。

正式写入或运行前，先按 `START_HERE.md` 输出启动摘要；需要正式证据时再填写完整 task card。

baseline 复现状态仍然是硬门。状态比较、best 选择、复现确认、升版、tag/version 表述前，必须运行或记录：

```bash
python workflow/gtpj_workflow.py repro-status --version <vX>
```

启动摘要必须包含 `baseline_repro_status`。除非 `confirmed_H` 和 `confirmation_status` 支持，否则不能把 `best_observed_H` 当成已确认 baseline。
