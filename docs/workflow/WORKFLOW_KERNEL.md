# GTPJ 工作流内核

本文件是精简后的硬规则层，应该保持短而稳定。

## 0. 框架与实验对象

- 唯一结构规范：`docs/workflow/FRAMEWORK_EXPERIMENT_STANDARD.md`。
- `main` 管治理；`framework/vX` 管对应框架代码；新实验从对应框架分支开 `exp/vX/<type>/...`。
- 每个正式框架固定有 tune、ablation、innovation、confirmation 四类实验。
- `experiments/vX/EXPERIMENTS.md` 由四个 INDEX 生成，禁止手工维护第二份结果。
- 每个实验的 `PARAMETER_MATRIX.csv` 是逐运行事实源；旧 `ATTEMPT` 只能成为 `legacy_ref`。

## 1. 权威来源

- GitHub 是可复现控制面、治理账本和轻量结果索引。
- `GTPJ_Research` 保存长推理、论文/来源笔记和完整 idea 历史。
- `GTPJ_Warehouse` 保存 raw logs、checkpoints、生成图、运行 receipt 和大型 artifact。
- 聊天上下文、命名线程 上下文、persistent thread 上下文和 Codex memory 只能辅助定位，不能作为正式证据。

## 1.1 文档语言硬规则

- 项目文档、workflow 文档、模板说明和审核报告的正文必须使用中文。
- 不允许新增或改出整段英文说明；英文只能作为必要名词或机器标识保留。
- 允许保留的英文包括：论文标题、方法名、角色名、命令、字段名、文件名、代码标识、指标名、URL，以及 helper 当前依赖的结构 marker。
- 如果标题保留英文 marker，例如 `Framework Diagram`、`Trial Flow`、`Code Flow Diagram`，同一节必须用中文解释含义、用途、填写要求和阻断条件。
- 新增模板必须先通过文档语言检查；历史 archive 可以保持原样，但不能作为新文档的写法模板。

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

正式证据工作必须使用 `real_multi_agent`。
正式 Runner 启动前还必须满足 `docs/workflow/core/AGENT_RUNTIME_HARD_GATE.md`。也就是说，
状态机记录和服务器 runner 都不能替代真实左侧命名 Codex 线程；没有 `agent_runtime.yaml`
和通过的 `validate-agent-runtime` / `multi-agent-preflight`，正式 Runner 必须阻断。
owner 只能把本轮目标改成非正式 `debug_smoke` 排障；`debug_smoke` 不能回填为正式证据。

正式证据对象必须绑定 `subject_id` 和 `subject_type`。`evidence_state` 只能由
tamper-evident append-only `TRANSITIONS.jsonl` 派生，`evidence_routing.yaml`
只是当前状态缓存，不能手写覆盖。

debug/smoke 只能用于排障或环境探针，必须记录：

```yaml
evidence_level: debug_smoke
formal_evidence: false
eligible_for_keep_best_promotion_confirmation: false
```

统一调度入口必须强制选择运行等级：

```yaml
debug_smoke:
  activation_mode: role_only
  formal_evidence: false
  real_agent_instances_started_by_helper: false

formal:
  activation_mode: real_multi_agent
  formal_evidence: true
  agent_runtime_gate_satisfied: true
```

`run-workflow` 还必须显式选择 `workflow_mode`，禁止 Coordinator 猜测：
```yaml
workflow_mode:
  required: true
  allowed:
    - live_multi_agent_monitor
    - server_frozen_runner
  no_default_guess: true
```

Owner 简单口令优先按下列映射解释：
```text
本地正式，干净 -> live_multi_agent_monitor；侧边栏干净；授权创建本轮左侧命名 Codex 线程；禁止启动服务器 runner
开启多agents智能体工作流，开始 / 跑N轮 / 做N轮实验 -> live_multi_agent_monitor；不得反复确认 workflow 模式或启动意图；通过硬门后继续执行
服务器冻结，开始 -> server_frozen_runner；不创建命名线程；允许服务器 detached runner
只做本地规划 -> role_only；不进入正式证据
```

如果 owner 只说 `本地正式` 但没有说 `干净`，Coordinator 只问一次侧边栏是否干净；不能展开成长授权模板。

- `live_multi_agent_monitor` 表示动态多 agents 监控工作流。它必须使用 `activation_mode: real_multi_agent`、`agent_instance_mode: named_owner_thread`，并通过左侧命名 Codex 线程 gate。
- `server_frozen_runner` 表示本地规划、冻结计划、服务器 detached 训练工作流。它必须使用 `activation_mode: role_only`、`formal_runtime_backend: server_detached_role_only`、`thread_creation_allowed: false`，不能自动创建线程。
- 如果 owner 只说“用工作流”但没有说明是哪一种，必须先问清楚；不能把服务器冻结训练当成动态多 agents 工作流，也不能把动态多 agents 工作流偷偷降级成离线训练。
- 如果 owner 已经说“开启多agents智能体工作流”“多agents智能体工作流，开始”“跑N轮”或“做N轮实验”，它不是模糊的“用工作流”。Coordinator 必须按 `live_multi_agent_monitor` 执行，不得反复确认规范，不得只写 planning gate 后停止。只有运行模式仍冲突、侧边栏干净状态未确认且无法验证、硬门失败、或 push / 删除 / 覆盖数据 / 密钥等安全边界动作，才允许再问一次。

代码审核不被 `server_frozen_runner` 豁免。`server_frozen_runner` 只豁免训练运行期的命名线程创建；它不能豁免代码、workflow、helper、模板或训练配置生成逻辑的 AI 交叉审核。此类改动必须先在专用代码审核分支完成，审核包通过后才能进入 `pre-run freeze commit`。如果改动已经在旧脏分支上发生，本轮正式启动必须阻断，除非重新从干净基线切分支并迁移最小 diff。

没有显式 `--debug-smoke` 或 `--formal` 时必须阻断。选择 `--formal` 时必须提供并通过
`agent_runtime.yaml`；选择 `--debug-smoke` 时结果只能证明工程链路可运行，不能回填为正式证据。

## 2.1 正式待跑 ledger 硬规则

正式待跑实验由正式 ledger 决定，不由运行缓存决定。任何“待跑”结论必须先读对应类型的表格：

```text
framework tune            -> experiments/vX/tune/INDEX.md
framework ablation        -> experiments/vX/ablation/INDEX.md
framework innovation      -> experiments/vX/innovation/INDEX.md
framework confirmation    -> experiments/vX/confirmation/INDEX.md
legacy Trial/Attempt      -> compatibility evidence only; map back with legacy_ref
mixed campaign            -> experiments/campaigns/.../WORK_ITEMS.md / RESULT_INDEX.md，只作 derived index
```

正式表格中的一行只有同时满足下面条件，才算 `formal_pending`：

```text
有 subject_id 或实验 id
有实验类型
有 run_id、计划目录或 attempt 目录；正式批次中的 run_id 必须与参数表逐行一致
状态是 planned / pending / pre_run / pre_run_gated / ready_to_run
不属于 debug_smoke，或明确 formal_evidence: true
```

`.gtpj_runtime/` 只保存运行中状态和 runner 执行包。目录存在、`batch_status.status=planned`
或旧 `events.jsonl` 为空，不能单独构成待跑实验。若 runtime 目录没有正式 ledger 行，统一记为
`orphan_runtime_plan`；它可以用于历史参考或排障，但不得自动续跑、不得写入 keep / best /
confirmation / promotion。

## 2.1.1 参数矩阵硬规则（2026-08-04 起）

一轮 batch 只是很多具体任务的容器，不能替代参数表。任何新建正式实验必须把每个 job 写进 `PARAMETER_MATRIX.csv`，并提供自动生成的 `PARAMETER_MATRIX.md` 阅读版。相同配置指纹必须明确标注为 `repeat_of`，否则视为误重复；参数矩阵必须与 pre-run freeze commit 一起冻结，再用 `prepare-run-start-receipt` 由 helper 生成收据并直接拉起训练。helper 会把真实进程号、开始、退出和输出追加到收据哈希之后，结束时记录退出码和整份日志哈希，不能只生成收据再手工开跑，也不能在结束标记后补写指标。跑完后只允许回填状态和结果，所有参数表改写动作共用同一把锁。阅读版与 CSV 不一致、启动收据缺失、真实进程标记缺失、日志未封口或收据与日志不匹配时，`record-result` 和 `record-module-attempt` 都会拒绝正式入账。动态路由正式批次还会逐行核对矩阵 `run_id` 与冻结计划，并要求取回真实 Warehouse manifest 和逐任务启动收据后再同步。完整规范：`docs/workflow/protocols/parameter_matrix_protocol.md`。

## 2.2 实验规划门（Experiment Planning Gate）

正式 batch、Runner、server frozen run 或 promotion-prep run 生成前，必须先通过 `experiment_planning`。
这个阶段必须自动读取当前项目状态，而不是让 owner 手填计划。

最小自动扫描：

```text
repo branch / HEAD / dirty
current_version 和 baseline_repro_status
正式待跑 ledger：只认 experiments/vX/{tune,ablation,innovation,confirmation}/INDEX.md；旧 TRIAL-xxx/ATTEMPTS.md 与 campaign 只作兼容映射
已完成 result / quality / agent_summary
.gtpj_runtime 只作 debug context，不作规划权威
```

输出只保留三张表：

```text
Evidence Summary：证据从哪里来，能支持什么，不能支持什么。
Candidate Decision：哪些候选值得跑，阻塞是什么，允许声称什么。
Current Run Plan：本轮 work item、fingerprint_policy、预算、停止条件和 ledger_target。
```

每个 planned job 必须引用正式 `evidence_ref`，声明 `claim_scope`、`fingerprint_policy`、`budget`、
`stop_condition` 和 `ledger_target`。没有 planning gate，不得生成 batch、启动 Runner 或写入
formal evidence。只读 helper 入口：

```bash
python workflow/gtpj_workflow.py plan-experiments --phrase "<owner 口令>"
```

单项和批量规划使用同一个入口。显式组合口令如 `跑10创新+100调参` 会拆成多个 workstream；
只给总量如 `做50轮实验` 时，planning gate 只能根据当前证据给出候选分配、阻塞和预算建议，
不得在缺少实验类型和 evidence_ref 时直接生成 Runner batch。

## 3. Agent 规则

正式任务默认：

```yaml
activation_mode: real_multi_agent
agent_instance_mode: named_owner_thread
lifecycle: workflow_scoped
owner_monitor_mode: true
owner_role: monitor
owner_visible_reporting: true
```

含义：

- Owner 是默认监控者。正式 Runner 启动后，工作流必须持续给 owner 可见汇报，
  不能把服务器离线训练、状态机文件或 agent_summary 当作 owner 已经看见过程。
- 每次可见汇报必须说明：哪个智能体在做什么、当前状态、证据位置、下一步动作。
- 如果 Coordinator 需要结束当前主对话，必须先给出监控交接位置、下一次检查条件和恢复命令。
- 每个角色在当前 workflow 或 campaign 阶段拥有独立活上下文。
- 正式运行必须记录真实 `agent_instance_id` 或可见 thread id；`named_owner_thread` 这类占位词不能冒充实例。
- 需要长期保留的经验必须写回 `agent_summary.md`、角色 `memory.md`、workflow issues、result 文件或 campaign 账本。
- `persistent_thread` 只是跨 workflow 可见追踪的可选上下文，不是 evidence。
- 不要给每个实验 run 创建一个永久 agent/thread。
- 每轮 workflow 结束或阶段结束时，Coordinator 必须先确认已完成 agents 的结论写入
  `agent_summary.md` / `AGENT_ACTIVITY.md` / result / quality / issues / memory 等正式位置，
  然后关闭这些已完成 agents。左侧栏默认只保留当前阶段仍在工作的 active agents。
- 多 agents 必须分文件复核：每个只读角色都要记录 `files_reviewed`、独立输出文件、allow/block/propose 结论和未覆盖范围。Coordinator 不能用一个上下文一次性“看过所有文件”来冒充独立复核，也不能漏掉 skill 镜像、active docs、helper 测试三类同步面。
- 左侧栏命名线程 显示名必须严格按 `<subject_id> | <Role Label>` 命名，例如 `ATTEMPT-007 | Runner Monitor`、`ATTEMPT-007 | Interface Checker`、`ATTEMPT-007 | Evidence Quality Checker`。
- 禁止使用与任务无关的随机英文昵称，例如 `Herschel`、`Galileo`、`Feynman`、`Bohr`；只写 `Runner` / `Quality` 这种泛名也不合格。
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
- `exact_repeat` 必须固定 `original_seed`、原始 config、代码 commit、data/cache、epoch schedule、batch size 和评估口径；改变 seed 或任何参数的多次运行只能叫 `seed_sweep` /
  `score_search` / `multi_seed_stability`，必须写 `not_confirmation_evidence: true`，不能叫严格复现。
- confirmation 默认 `repeat_type: exact_repeat`、`max_attempts: 5`、`max_attempts_hard_cap: true`、`early_stop_on_best_hit: true`。必须声明
  `restore_target_H`；`near_miss_tolerance_H` 只用于标记接近但未还原。复现判定分三层：
  `best_hit` 只看任一 clean repeat 是否达到 `restore_target_H`，用来回答“有没有还原”；`near_miss_not_restored`
  表示接近目标、有希望，但不能停止、不能作为 confirmation；`stable_confirm`
  看同一 `original_seed`、同一配置的 mean/min/max/range 是否满足预设门槛，用来回答“能不能作为稳定 confirmed / promotion / baseline 证据”。
- `max_attempts_hard_cap` 表示同一候选无论是否还原成功最多跑 5 次；达到 `restore_target_H` 可以提前停止，5 次未达到则收口为 not restored / near miss，不能继续追加复现轮数。
- 复现通过 `best_hit` 后，必须记录 `best_single_H` / `best_observed_H`；如果 `stable_confirm` 未通过，
  结论只能是命中候选或继续复现，不能写成稳定确认。
- promotion 和 baseline claim 默认比较 `confirmed_H` / repeat mean，不能只凭 best repeat。
- 不能把未确认的 `best_observed_H` 说成 confirmed baseline。
- 每个正式版本 `experiments/vX/` 必须有版本级 `framework_diagram.md` 和 `MODULES.md`；`VERSION.md` 必须链接它们并包含 `## Framework Diagram`。模块说明不能只列名字，必须解释 purpose、input、output、config switch 和 baseline-off behavior。
- 框架记录绑定“方法框架”，不是绑定每个代码文件。调参、复现、只关闭或旁路既有组件的窄消融不新增框架图；它们只记录 config、manifest、result、quality 和 agent summary。
- 凡是新增或改写 module、forward、loss、evaluation、data view、input/output、tensor flow、接口语义或模块分支逻辑，都视为创新 / module trial 代码变动，而不是普通 tune/ablation。此时必须记录 `module_source.md`、`implementation.md`、`framework_diagram.md`，并说明每个模块来源、接入点、输入输出、baseline-off 行为和 GZSL 语义边界。
- 上述创新代码变动所属 Trial 的 `README.md` 必须包含 `## Code Flow Diagram`，用简洁流程图说明代码实际输入、输出、关键张量流向、分支开关和最终 logits/metric 出口；完整变量/方法说明仍放在 `framework_diagram.md`。
- 批量实验 / mixed campaign 不能单独成为正式结果分支。它只能保存 routing index、run map、work item 映射和监控状态；正式结果必须自动回写到 `experiments/vX/<type>/`。旧 Trial/Attempt 路径只能作为 `legacy_ref`，真正的新创新写所属正式框架的 innovation 账本；候选无 Tag，确认晋级后才注册为新的同级正式框架。

## 5. 运行安全

正式运行前必须记录：

```text
branch 和 commit
git dirty 状态
冻结后的 config
agent_runtime.yaml 及 validate-agent-runtime 结果
multi_agent_preflight 结果
formal_runner_allowed、formal_evidence_allowed
agent_instance_status、agent_status_refs、agent_output_refs
owner_monitor_mode、report_channel、agent_activity_stream
thread_archive_policy、archive_completed_threads_on_stage_end、archived_threads_record
agent-cleanup-plan 输出和 archive_result 记录
dataset/split/label mapping 假设
GPU 或 runner slot 锁
result/artifact 写入位置
checkpoint retention 规则
```

如果 label mapping、seen/unseen split、class order、logits shape 或 metric semantics 不清楚，必须硬阻断。
所有正式实验必须满足 `docs/workflow/reference/GZSL_HARD_RULES.md`。

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
- `activation_mode: real_multi_agent` 但没有真实左侧命名 Codex 线程实例、pre-run allow/check 或 `agent_runtime.yaml`。
- `multi_agent_preflight` 未通过，或 `formal_runner_allowed` / `formal_evidence_allowed` 不是 true。
- owner 改变范围。
- 会跨越安全边界。

停止时只汇报最小 unblock 动作。

## Live Monitor 运行期规则

`live_multi_agent_monitor` 的正式定义是：左侧命名 Codex 线程参与，Runner 可在服务器执行，但当前 owner 线程持续作为监控入口。Runner 仍在 running/pending 时，不得把本轮 active named threads 归档；归档只能发生在 closeout/handoff 后。

每轮监控必须调用或等价执行：

```powershell
python workflow\gtpj_workflow.py monitor-workflow --run-dir <run_dir> --report-new-completions --activity-log <attempt_dir>\AGENT_ACTIVITY.md
```

新增 completed job 必须逐条报告并写入 agent activity。报告至少包含 `job_id`、H/U/S/ZS、当前 best、H>=75/H>=76 命中情况、证据文件和下一步。只看到 server screen 存在或目录存在，不等于监控完成。

## 9. 反膨胀规则

瘦身优先：新增规范、流程或文档前，先检查能否合并、删减或复用现有入口；默认写最小可执行规则，不为完整感新增层级。

新增 workflow 文件、模板或协议前，必须至少满足一项：

```text
可机器检查
能驱动 evidence_state transition
是权威事实源
是正式 evidence 必需模板
```

如果都不满足，不进入日常 workflow。

## 免 owner 日常参与的 AI 交叉审核

Owner 不参与日常代码审核。重要代码、workflow/helper/template、训练入口、评估语义、实验结论、promotion
或论文 claim 相关改动，必须按 `review_tier` 完成 Claude Code 与 Codex 分层交叉审核，并通过：

```text
python workflow/gtpj_workflow.py validate-ai-cross-review --path <review_pack>
```

`fast` 只允许低风险轻量修补；普通 workflow/helper/template 修补走 `review-1`；会污染正式实验结论、
训练入口、评估语义、promotion、baseline 或 paper claim 的改动必须走 `strict-3`。
机器验证永远必跑，Claude Code 必须只读；Codex 可以实现、修复、重跑验证和记录 rebuttal。
Claude Code 因连接拒绝、超时或空输出没有形成结论时，该调用不算审核轮次；允许按相同 tier 使用彼此独立的只读 Codex Reviewer 作为备用。备用证据必须记录真实 reviewer instance id、独立上下文和 `claude_code_unavailable` 原因，不能把 Codex 伪装成 Claude，也不能降低轮数。
审核包 blocked 时，不能进入正式 Runner、keep/best、confirmation、promotion、baseline 或 paper claim。
push、删除、远端发布和破坏性迁移仍然需要 owner 明确授权。
