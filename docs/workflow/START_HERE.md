# GTPJ 工作流入口

这是每个 GTPJ 任务的精简入口，用来取代“每次都读完整 workflow 目录”的旧习惯。

## 0. Owner 简单入口

owner 不需要背 `workflow_mode`、`agent_runtime.yaml` 或线程字段。下面三句就是正式入口：

| owner 口令 | Coordinator 必须解释成 | 允许动作 |
|---|---|---|
| `本地正式，干净` | `workflow_mode=live_multi_agent_monitor` | 先确认侧边栏干净；允许创建本轮左侧命名 Codex 线程；不启动服务器 runner。 |
| `开启多agents智能体工作流，开始` / `开启多agents智能体工作流，跑N轮` / `开启多agents智能体工作流，做N轮实验` | `workflow_mode=live_multi_agent_monitor` | owner 已明确选择动态多 agents 工作流；不得反复确认 workflow 模式或启动意图；通过硬门后继续创建角色、生成计划并启动对应 runner。 |
| `服务器冻结，开始` | `workflow_mode=server_frozen_runner` | 不创建命名线程；走本地规划、gate、冻结计划和服务器 detached runner。 |
| `只做本地规划` | `activation_mode=role_only` | 只做状态检查、账本整理、计划和 debug/smoke；不进入正式证据。 |

硬规则：只有 `本地正式，干净` 这句同时表达“侧边栏干净”和“允许创建本轮命名线程”。如果 owner 只说“本地正式”但没有说“干净”，Coordinator 只问一句：`侧边栏干净吗？回复：干净。`

明确入口硬规则：owner 已经说出 `开启多agents智能体工作流`、`多agents智能体工作流，开始`、`跑N轮` 或 `做N轮实验` 时，Coordinator 必须把它当作执行授权，而不是只做规划。只有四类情况允许再问一次：运行模式仍然不明、侧边栏干净状态从未确认且工具无法验证、硬门失败、或动作涉及 push / 删除 / 覆盖数据 / 密钥等安全边界。除此之外，不得反复确认规范、不得把“开始/跑N轮”降级成 `pre_run_planned` 后停止。

代码审核硬规则：代码审核不被 `server_frozen_runner` 豁免。`server_frozen_runner` 只说明训练运行期不创建命名线程；凡是修改代码、workflow、helper、模板或训练配置生成逻辑，仍必须先切专用代码审核分支，再执行命名 Codex 线程预审、Claude Code 只读审核、机器验证和 `validate-ai-cross-review`。在旧脏分支上先改后补切，只能视为草稿，不能进入 `pre-run freeze commit` 或正式 Runner。

通用话规划入口：

| owner 说 | Coordinator 必须解释成 | 允许动作 |
|---|---|---|
| `规划下一轮实验` / `下一轮怎么跑` | `experiment_planning` | 只读自动生成 Evidence Summary、Candidate Decision、Current Run Plan；不启动 Runner。 |
| `批量规划50轮实验` / `给我规划50轮` | `experiment_planning` with budget 50 | 只读规划批量候选、预算、阻塞和 ledger_target；不创建 batch。 |
| `规划10创新+100调参` / `跑10创新+100调参` | `mixed_experiment_campaign` planning | 拆成 workstreams；先过 planning gate，再进入 campaign gate。 |
| `按这个计划开多agents工作流` | `live_multi_agent_monitor` | 需要真实左侧命名线程、`agent_runtime.yaml` 和 preflight；通过后才能启动正式 Runner。 |
| `按这个计划服务器冻结跑` | `server_frozen_runner` | 训练运行期不创建命名线程；若计划涉及代码/helper/template 改动，先完成代码审核门；通过 server-detached gate 后才能启动 detached Runner。 |

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
agent_instance_mode: named_owner_thread
lifecycle: workflow_scoped
formal_runner_allowed: true
formal_evidence_allowed: true
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
docs/workflow/core/AGENT_RUNTIME_HARD_GATE.md
agent_runtime.yaml
python workflow/gtpj_workflow.py validate-agent-runtime --path <agent_runtime.yaml>
```

创建命名线程 前必须先确认左侧栏干净。若 owner 报告左侧栏已有历史 agents，
或者当前工具只能关闭本轮已知 id、不能枚举 UI 中全部旧 agent，则不能继续开新的
`real_multi_agent`。正确动作是先 cleanup；无法 cleanup 的旧 UI agent 必须记为
`unknown_ui_agent`，正式 Runner 阻断。只有 owner 明确接受非正式排障时，才可走
`debug_smoke`，且结果不能进入 keep / best / confirmation / promotion。

没有左侧命名 Codex 线程、没有真实 agent id、没有 pre-run allow/check，就不能启动正式 Runner。
这种情况必须阻断正式工作；只有 owner 明确接受非正式排障时，才可以另开 `debug_smoke`
路径，且结果不能进入 keep / best / confirmation / promotion / version 判断。

统一调度入口必须显式区分两种运行等级，不能默认猜：

```text
debug_smoke：测试代码、服务器、GPU 和 helper 链路；activation_mode=role_only；formal_evidence=false。
formal：正式证据实验；允许 `activation_mode=real_multi_agent`，或 `activation_mode=role_only + formal_runtime_backend=server_detached_role_only`；两者都必须先通过 agent_runtime gate。
```

因此 `run-workflow` 这类统一入口必须二选一：

```bash
python workflow/gtpj_workflow.py run-workflow ... --workflow-mode live_multi_agent_monitor --debug-smoke
python workflow/gtpj_workflow.py run-workflow ... --workflow-mode live_multi_agent_monitor --formal --agent-runtime-gate <agent_runtime.yaml>
python workflow/gtpj_workflow.py run-workflow ... --workflow-mode server_frozen_runner --formal --agent-runtime-gate <agent_runtime.yaml>
```

正式实验必须显式选择 `workflow_mode`，不能由 Coordinator 默认猜测：

| `workflow_mode` | 中文含义 | 适用场景 | gate 要求 |
|---|---|---|---|
| `live_multi_agent_monitor` | 动态多 agents 监控工作流 | owner 要求边跑边监控、质量检查、结果解释、best/promotion 判断，且接受命名 Codex 线程参与 | `activation_mode=real_multi_agent`，`agent_instance_mode=named_owner_thread` |
| `server_frozen_runner` | 本地规划 + 服务器冻结训练工作流 | owner 要求本地只做规划/gate/账本/frozen plan，训练在 `lab4090` detached 跑，本地可以关机 | `activation_mode=role_only`，`formal_runtime_backend=server_detached_role_only`，`thread_creation_allowed=false` |

owner 只说“用工作流”但没有指定模式时，Coordinator 必须先确认：

```text
这次用 workflow_mode=live_multi_agent_monitor，还是 workflow_mode=server_frozen_runner？
```

如果 owner 已经明确说“多agents智能体工作流”，它不属于“只说用工作流”的模糊入口，直接解释为 `live_multi_agent_monitor`。

不能把 `server_frozen_runner` 的底层 `plan-dynamic-routing-batch + scp + screen` 当成 `live_multi_agent_monitor`，也不能把 `live_multi_agent_monitor` 降级成服务器离线训练。

没有 `--formal` 和通过的 `agent_runtime.yaml`，即使服务器真的跑了训练，也只能算 runner/debug 事实，不能算正式工作流证据。

## 1.1 文档语言边界

项目文档、workflow 文档、模板说明和审核报告的正文必须使用中文，不允许整段英文说明。

英文只保留为必要名词或机器标识，例如论文标题、方法名、角色名、命令、字段名、文件名、代码标识、指标名、URL 和 helper 依赖的结构 marker。

如果必须保留 `Framework Diagram`、`Trial Flow`、`Code Flow Diagram` 这类英文结构 marker，同一节必须用中文说明它是什么、为什么需要、应该填写什么。新模板不得只给英文标题和英文正文。

## 2. 最小阅读顺序

除非任务需要更多细节，否则只读这条链：

```text
1. START_HERE.md
2. WORKFLOW_KERNEL.md
3. docs/workflow/playbooks/ 下的相关 playbook
4. 只有路由模糊时才读 docs/workflow/core/WORKFLOW_ROUTER.md
5. 正式写入或运行前读 docs/workflow/core/TASK_START_CARD.md
6. 正式 Runner 前读 docs/workflow/core/AGENT_RUNTIME_HARD_GATE.md
```

不要默认深读所有旧协议。

如果只是确认文档层级，不要人工扫完整目录，使用：

```bash
python workflow/gtpj_workflow.py list-workflow-files
```

## 3. 用户人话路由

| 用户说 | 默认路由 | 执行卡 |
|---|---|---|
| `汇报`, `查状态`, `现在怎么样` | 只读状态检查 | 无，使用 `WORKFLOW_KERNEL.md` |
| `读论文`, `找创新点` | 论文读取 / idea discovery | `playbooks/paper_intake.md` |
| `基于 vX 从论文开始做实验`, `论文到实验闭环`, `读论文并验证创新` | paper -> idea -> module trial 闭环；缺 `vX` 时只做候选创新 | `playbooks/paper_to_experiment.md` |
| `调参` | 调参 Tune | `playbooks/tune.md` |
| `消融` | 消融 Ablation；只允许关闭/旁路/替换既有因素，不新增方法模块 | `playbooks/ablation.md` |
| `复现`, `确认这个结果` | 复现确认 Confirmation | `playbooks/confirmation.md` |
| `开新模块`, `试这个想法` | 创新 / module trial | `playbooks/innovation.md` |
| `升版本` | 升版 Promotion | `playbooks/promotion.md` |
| `跑10创新+100调参` 或任意数量组合 | 混合实验 campaign | `playbooks/mixed_campaign.md` |
| `全自动研究campaign`, `从论文到最终结果都接管` | 全自动研究 campaign | `playbooks/autonomous_campaign.md` |

helper 会自动解析 `跑2创新+8调参` 这类组合短语：

```bash
python workflow/gtpj_workflow.py start --phrase "跑2创新+8调参"
```

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
runner_scope：
formal_runner_allowed：
formal_evidence_allowed：
必须读的 playbook：
硬门：
agent_runtime_gate：
multi_agent_preflight：
owner_monitor_mode：
agent_activity_stream：
当前阻塞：
下一步最小动作：
```

如果只是状态汇报，保持简短即可。

## 5. 最小闭环

不要把简单任务做成大工程。正式实验只要求这条闭环：

```text
人话路由 -> campaign/attempt 计划 -> agent_runtime -> preflight -> runner
-> manifest/result/quality/agent_summary -> cleanup -> sync/closeout
```

中间的证据成熟度由状态机管理：

```text
subject_id + subject_type -> TRANSITIONS.jsonl -> evidence_state -> evidence_routing.yaml
```

`TRANSITIONS.jsonl` 是只追加的权威历史；`evidence_routing.yaml` 只是当前状态视图，必须能由
chain head 推导出来。聊天结论、服务器状态和 `agent_summary.md` 都不能手写覆盖状态机。

从论文获得创新时，多一段前置闭环，但仍然只接入同一个实验闭环：

```text
paper_inbox -> source_review -> idea_candidate -> formal_IDEA -> selected_queue
-> trial_preflight -> runner_evidence -> idea_feedback
```

进入 `trial_preflight` 前必须由 owner 明确指定 `base_version` / `base_code_tag`，例如
`基于 v5 从论文开始做实验`。不能默认使用当前 active version。

混合实验目录只做调度索引；正式结果必须写回各自归属的 attempt / version / trial。

框架记录只跟“方法框架变动”绑定，不跟每个代码文件绑定：

```text
调参 / 复现 / 只关闭既有组件的窄消融 -> 不新增 framework_diagram，只记录结果证据。
新增或改写 module / forward / loss / eval / data view / 接口语义 -> 创新 / module trial，必须记录框架和模块来源。
```

## 6. 证据优先

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

## 6.0 参数矩阵入口（2026-08-04 起）

从今天起，任何新实验都不能只写“这一批跑了 50/100 个”。必须为每个具体任务建立 `PARAMETER_MATRIX.csv` 和阅读版 `PARAMETER_MATRIX.md`：一行对应一套参数、一个种子和一次结果。先生成参数矩阵、查重、提交 pre-run freeze commit，再进入正式 Runner；训练完成后把每个任务的结果回填原表。版本级的 `record-result` 和模块内的 `record-module-attempt` 会拒绝草稿、过期阅读版或找不到对应行的表。详见 `docs/workflow/protocols/parameter_matrix_protocol.md`。

## 6.1 正式待跑实验入口

Owner 问“现在有哪些待跑实验”时，只读正式 ledger，不从 `.gtpj_runtime/` 反推。正式待跑实验必须能在对应类型的正式表格里看到：

| 实验类型 | 正式待跑表格 | 说明 |
|---|---|---|
| 版本级 tune | `experiments/vX/tune/INDEX.md` | 只记录正式 baseline 的调参计划和结果。 |
| 版本级 ablation | `experiments/vX/ablation/INDEX.md` | 只记录正式 baseline 的消融计划和结果。 |
| 版本级 confirmation | `experiments/vX/confirmation/INDEX.md` | 只记录正式 baseline 或版本级 candidate 的确认计划和结果。 |
| module trial 内部 attempt | `experiments/module_trials/.../TRIAL-xxx/ATTEMPTS.md` | 记录同一 trial 内的调参、窄消融、rerun、confirmation 和 debug-fix。 |
| mixed campaign | `experiments/campaigns/.../WORK_ITEMS.md` / `RESULT_INDEX.md` | 只做 derived index；每个 work item 仍要回指上面某个正式表格。 |

待跑实验的判定规则：

```text
formal_pending = 正式表格中有 subject 行
              + subject 有明确实验类型、run_id 或计划目录
              + 状态为 planned / pending / pre_run / pre_run_gated / ready_to_run
              + 不是 debug_smoke，或已明确标注 formal_evidence: true
```

`.gtpj_runtime/batches/<run_id>` 只是 runner 执行缓存；它可以证明运行包存在、事件是否发生、summary 是否产出，但不能单独决定“待跑实验”。如果 runtime 目录存在而正式表格没有对应行，统一标为 `orphan_runtime_plan`，只能作为历史参考或排障线索，不能自动续跑、不能进入 keep / best / confirmation / promotion。

## 7. 免 owner 日常参与的 AI 交叉审核

重要代码、workflow/helper/template、训练入口、评估语义、实验结论或 promotion 相关改动，默认不需要 owner 参与日常审核。

改动必须按 `review_tier` 走 Claude Code + Codex 分层交叉审核：

```text
机器验证永远必跑
Codex 命名线程 预审并关闭 -> Claude Code 只读审核 -> Codex 回应/重跑验证
fast: 0 轮 Claude，仅低风险轻量修补
review-1: 1 轮 Claude，普通 workflow/helper/template 修补
strict-3: 3 轮 Claude，训练入口、评估语义、正式实验结论、promotion、baseline 或论文 claim 风险
validate-ai-cross-review -> 通过后才信任改动
```

正式通过条件记录在 `docs/workflow/protocols/ai_cross_review_protocol.md`。通过包必须包含：

```text
owner_participation: not_required
rounds_completed: 3
claude_code_read_only: true
machine_gates_passed: true
unresolved_blocking_issues: 0
```

## 8. 命名线程

正式 `real_multi_agent` 不能使用随机英文昵称。左侧栏命名 Codex 线程必须按任务命名：

```text
<subject_id> | <Role Label>
```

示例：

```text
ATTEMPT-007 | Runner Monitor
ATTEMPT-007 | Interface Checker
ATTEMPT-007 | Evidence Quality Checker
```

命名必须写入 `agent_runtime.yaml` 的 `named_thread_titles`，并由
`validate-agent-runtime` 校验。随机昵称或只写 `Runner` / `Quality` 这种泛名，不能启动正式 Runner。

创建线程前还必须满足：

```text
left_sidebar_named_threads_ready: true
owner_visible_sidebar_count: 0 或只包含本阶段 active threads
unknown_ui_agents: none
```

## 9. Live Monitor 逐实验汇报

`live_multi_agent_monitor` 不是“启动服务器后结束”。在 Runner 仍处于 running/pending 时，本轮左侧命名 Codex 线程必须保持可见，尤其是 Runner Monitor、Log Analyst、Result Analyst、Quality Checker 和 Interface Checker；只有 closeout/handoff 完成、输出写回账本后，才归档这些线程。

监控每个新增 completed job 时使用统一入口：

```powershell
python workflow\gtpj_workflow.py monitor-workflow --run-dir <run_dir> --report-new-completions --activity-log <attempt_dir>\AGENT_ACTIVITY.md
```

每次报告至少写清 `job_id`、H/U/S/ZS、当前 best、是否出现 H>=75/H>=76、证据位置和下一步。`monitor_seen_completed_jobs.json` 只用于去重，不是正式结果源。

如果 owner 看到的左侧栏数量与 `agent-cleanup-plan` 不一致，以 owner 可见 UI 为准；
Coordinator 不得再开新的命名线程来“补 gate”。
