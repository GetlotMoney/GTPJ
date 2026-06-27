# Agent 编排和长期管理

GitHub 保存长期规则和 agent IO 契约。本地 `gtpj-workflow` skill 保存执行入口。
两边规则必须同步。

## 核心结构

长期 agent 管理采用三层结构：

```text
docs/workflow/agents/
|-- shared_roles/
|   `-- <role>/memory.md
`-- by_experiment/
```

`shared_roles/` 只定义 agent 的长期身份、自我介绍、权限、读写边界、输出和失败条件。
每个长期角色还必须有 `memory.md`，保存该角色反复踩坑、固定检查项和可复用经验。

`by_experiment/` 只定义某类实验如何调用这些共享角色，不重复定义角色本身。

这样可以同时满足两个目标：

- 每个实验类型都有独立 agents 文件夹，层次清楚；
- Coordinator、Runner、Quality Checker 等共享角色只写一份，避免规则漂移。
- 同一个长期 agent 的经验不会散落在聊天里，而是沉淀到对应角色的 `memory.md`。

## GitHub 权威目录

```text
docs/workflow/agents/
|-- README.md
|-- shared_roles/
|   |-- coordinator/profile.md
|   |-- coordinator/memory.md
|   |-- reader_planner/profile.md
|   |-- reader_planner/memory.md
|   |-- runner/profile.md
|   |-- runner/memory.md
|   |-- implementer/profile.md
|   |-- implementer/memory.md
|   |-- interface_checker/profile.md
|   |-- interface_checker/memory.md
|   |-- quality_checker/profile.md
|   |-- quality_checker/memory.md
|   |-- log_analyst/profile.md
|   |-- log_analyst/memory.md
|   |-- result_analyst/profile.md
|   |-- result_analyst/memory.md
|   `-- reviewer/profile.md
|   `-- reviewer/memory.md
`-- by_experiment/
    |-- tune/agents/README.md
    |-- ablation/agents/README.md
    |-- innovation/agents/README.md
    |-- confirmation/agents/README.md
    `-- promotion/agents/README.md
```

## 本地 Skill 镜像目录

本地 skill 必须镜像 GitHub 权威目录：

```text
C:\Users\Administrator\.codex\skills\gtpj-workflow\references\agents/
|-- README.md
|-- shared_roles/
`-- by_experiment/
```

如果 GitHub 文档和本地 skill 冲突，以 GitHub 文档为准。

## 角色长期，实例临时

这里的“长期 agent”不是指一个永远在线的后台进程，而是指一个长期身份包：

```text
profile.md          # 它是谁、能读什么、能写什么、失败条件是什么
memory.md           # 它长期记住的踩坑、检查项、复用经验
by_experiment/...   # 在不同实验类型里怎么被调用
agent_summary.md    # 每次实例执行后留下的工作凭证
```

每次实验启动的 sub-agent / reviewer 实例可以是临时的，但它必须先读取或被显式传入该长期身份包。
因此临时实例结束后，经验仍留在 `memory.md`、`docs/workflow/issues/`、Research/Warehouse/GitHub
账本里，而不是留在聊天窗口里。

长期 agent 的记忆细则见：

```text
docs/workflow/agents/long_term_memory.md
```

新边界下，GitHub 只保存轻量 config / manifest / result / version ledger。Runner 写
Warehouse，Reader / Planner 读 Research，Result Analyst 通过 artifact id 引用结果。
任何 agent 都不能把 raw logs、checkpoint、generated figures、完整论文笔记或完整创意树写入 GitHub。

## Agent 启用模式

Coordinator 不能临场自由决定是否使用多 agents。每次任务启动卡必须显式写入：

```yaml
agents:
  activation_mode: role_only | real_multi_agent
  activation_reason:
  required_roles:
  disabled_roles:
  required_real_agents:
  single_agent_allowed:
  owner_override:
  tool_support:
    real_multi_agent_available:
    fallback_mode:
    checked_by:
  serial:
  parallel:
  writer_roles:
  reviewer_roles:
  memory_policy:
    session_context_allowed:
    codex_memory_allowed:
    repo_state_required:
    memory_used:
    memory_sources:
    verified_against_current_repo:
```

两种模式含义：

- `role_only`：一个主 agent 按多个角色清单串行执行，并在 `agent_summary.md` 里记录各角色检查结果。
- `real_multi_agent`：启动或委派独立 agent / reviewer / checker 执行对应角色，至少保留独立输入、发现和结论。

`activation_mode` 只能是 `role_only` 或 `real_multi_agent`。如果当前 Codex 环境没有真实
sub-agent / multi-agent 工具，不能把 `role_only` 写成 `real_multi_agent`。此时：

```yaml
agents:
  activation_mode: role_only
  tool_support:
    real_multi_agent_available: false
    fallback_mode: role_only_with_independent_sequential_review
```

该 fallback 不能用于 promotion、正式 best 结论或 owner 已明确要求真实多 agents 的任务，除非
owner 明确接受它只作为 debug/smoke 证据。

`required_real_agents` 是真实多 agent 硬需求角色列表：

- `activation_mode: real_multi_agent` 时，写必须由独立 sub-agent 执行的角色，例如
  `[Quality Checker, Result Analyst, Reviewer]`。
- `activation_mode: role_only` 时，写 `[]`；如果本应有真实多 agent 但工具不可用，必须在
  `tool_support.fallback_mode` 写明 fallback，并触发阻断或 debug-only 降级。

### 最快合规路径

Coordinator 默认必须选择“最快的有效执行路径”，而不是默认选择最重流程。

规则：

- 如果任务只是只读解释、状态检查、配置查看、窄范围 rerun/confirmation 准备、单 Runner frozen-config 执行、debug/smoke，或不改变结论的账本格式整理，默认用 `role_only`。
- 如果 hard gate 或 owner 明确要求 `real_multi_agent`，必须用 `real_multi_agent`，但要把 Reader/Planner、Log Analyst、Quality Checker、Result Analyst、Reviewer 这类只读角色并行执行。
- 不能为了“显得规范”而串行等待不必要 agents；未被 hard gate 要求、也不影响当前结论的角色必须跳过，并在启动卡里写明 `skipped_agents`。
- Runner 永远串行并持有 GPU lock；Implementer 对同一代码路径永远单 writer；Coordinator 是最终 GitHub 账本唯一 writer。
- 如果 real multi-agent 工具不可用，而任务没有 hard gate 要求真实多 agent，走 `role_only` 是最快合规路径；如果任务硬性要求真实多 agent，则阻断或降级为 debug/smoke，不能把正式证据伪装成已独立审查。

启动卡里的 `agents.decision_basis` 必须包含：

```yaml
fastest_valid_path:
  selected:
  why_fastest:
  why_still_valid:
  skipped_agents:
  parallelized_roles:
  serialized_roles:
```

### 启用矩阵

| 场景 | 默认模式 | 触发理由 |
|---|---|---|
| 只读解释、定位文件、查看配置、普通状态汇报 | `role_only` | 不产生实验事实，不改代码，不改变结论。 |
| 窄范围 rerun / confirmation 准备 | `role_only` | 只准备冻结配置、启动卡或账本，不启动争议 run。 |
| 单一 Runner 按 frozen config 串行训练 | `role_only` 可用 | 只执行已冻结配置，Runner/GPU 本来必须串行。 |
| debug/smoke | `role_only` | 结果不作为 keep / best / promote / confirmation evidence。 |
| 账本格式整理 | `role_only` | 不改变实验结论和证据语义。 |
| owner 明确要求“多 agents”“多 agents 验证”“独立 review” | `real_multi_agent` | owner 已要求独立分工。 |
| 修改模型结构、forward、loss、eval 或数据流 | `real_multi_agent` | 代码语义变化需要实现、接口、质量独立复核。 |
| 涉及 label mapping、seen/unseen split、class order、logits shape 或 metric semantics | `real_multi_agent` | 这些是 GZSL 有效性硬门。 |
| 新 module trial 的实现、接口检查或 promotion 前复核 | `real_multi_agent` | 会影响 trial 结论或版本提升。 |
| idea / 创新 / module trial 将落成代码改动 | `real_multi_agent` | 必须执行 `innovation_code_review_protocol.md` 的多轮独立审查。 |
| 结果异常、争议大、owner 质疑解释 | `real_multi_agent` | 需要独立复核日志、配置、代码和质量证据。 |
| 准备写 `promotion_decision: promote`、创建 `vX` 或打 tag | `real_multi_agent` | 版本事实不可由单一视角确认。 |
| 任务需要同时读论文、源码、日志和质量证据 | `real_multi_agent` | 输入天然可拆，适合独立检查。 |
| 结论会影响论文实验路线、baseline 选择或下一轮大成本实验 | `real_multi_agent` | 决策成本高，需要可审计分工。 |

即使使用 `role_only`，也不能省略角色记录。`agent_summary.md` 必须写清：

- 为什么没有启动 `real_multi_agent`；
- 哪些角色由主 agent 代执行；
- 哪些 hard gate 已检查；
- 哪些情况会升级为 `real_multi_agent`。

如果 owner 对 `activation_mode` 提出异议，Coordinator 必须暂停真实 run，先修正启动卡或升级为
`real_multi_agent`，不能继续按原模式执行。

### 按任务选角色

| 任务 | 必需角色 | 默认模式 | 说明 |
|---|---|---|---|
| 只读状态 / 配置检查 | Coordinator，必要时 Reader/Planner | `role_only` | 不跑训练，不写实验结论。 |
| 调参建议 | Coordinator、Reader/Planner、Result Analyst | `role_only` | 只提出候选，不启动 Runner。 |
| 调参真实运行 | Coordinator、Runner、Log Analyst、Result Analyst、Quality Checker | `role_only` 或 `real_multi_agent` | 单配置冻结复跑可 `role_only`；多候选、争议或正式 best 选择用 `real_multi_agent`。 |
| confirmation / rerun | Coordinator、Runner、Log Analyst、Result Analyst、Quality Checker | `role_only` 或 `real_multi_agent` | 普通干净复跑可 `role_only`；争议确认、promotion 前确认用 `real_multi_agent`。 |
| ablation | Coordinator、Runner、Log Analyst、Interface Checker、Result Analyst、Quality Checker | `real_multi_agent` | 如果只改配置开关但不改代码，也要保留 Interface Checker 角色。 |
| innovation / module trial | Coordinator、Reader/Planner、Implementer、Interface Checker、Runner、Log Analyst、Result Analyst、Quality Checker、Reviewer | `real_multi_agent` | 新模块默认真实多 agent。 |
| promotion | Coordinator、Quality Checker、Reviewer、Result Analyst，必要时 Interface Checker | `real_multi_agent` | promotion 不允许只靠 `role_only` 给最终通过结论。 |
| debug / smoke | Coordinator、Runner、Log Analyst，必要时 Interface Checker | `role_only` | 只定位问题；若发现代码或评估语义问题，升级。 |

### 串行和并行

- Runner 永远串行，必须独占 GPU lock。
- Implementer 是同一代码路径的唯一 writer；不能让多个 agents 同时改同一模型、loss、eval 或 dataset 文件。
- Coordinator 是最终 GitHub 账本唯一写入者。
- Reader/Planner、Log Analyst、Quality Checker、Result Analyst、Reviewer 默认只读，可并行。
- Interface Checker 对接口语义有阻断权；一旦阻断，Runner 和 Result Analyst 不能把结果当有效证据。

### Agent 记忆规则

Agent 不能把隐藏聊天记忆当作实验事实源。GTPJ 的可审计事实源按优先级排序：

1. 当前仓库文件、commit、tag、实验账本、config、manifest、result、quality check。
2. Warehouse / Research 中被 artifact id、URI、hash、size 引用的外部证据。
3. 当前对话中 owner 明确给出的任务约束。
4. Codex 全局 memory 或历史会话摘要，只能用于快速定位和背景提醒，必须回到当前仓库或 artifact 验证后才能入账。

真实多 agent 下，每个 agent 只自动拥有自己收到的任务说明、被显式传入的文件和当前工具可见上下文。
它们不应假定自己拥有主 agent 的全部隐藏记忆。Coordinator 如果依赖历史记忆，必须在任务说明里显式写出，
并要求 agent 回到当前仓库验证。

长期 agent 记忆的读取顺序：

```text
shared_roles/<role>/profile.md
shared_roles/<role>/memory.md
by_experiment/<task_type>/agents/README.md
docs/workflow/issues/README.md 和最近相关问题文档
当前 task start card
```

长期 agent 记忆的写入规则：

- 新问题只出现一次：先写入本次 `agent_summary.md` 或当日 issue 文档。
- 同一类问题重复出现两次：写入对应角色 `memory.md` 的 failure mode。
- 同一类后处理动作重复三次：优先升级成 `workflow/gtpj_workflow.py` helper 或 sync check。
- `memory.md` 只能保存检查规则和经验，不保存 raw logs、长推理、完整论文笔记或实验大文件。

`agent_summary.md` 必须记录：

- `memory_used: yes | no`
- `memory_sources:` 使用了哪些历史摘要、memory 文件或 conversation context；
- `verified_against_current_repo:` 哪些事实已经用当前 repo / log / artifact 验证；
- `agent_instance_type:` `main_agent`、`sub_agent`、`sequential_reviewer` 或 `role_checklist`；
- `independence_scope:` 该角色独立检查了哪些输入。

没有经过当前仓库或 artifact 验证的 memory-derived fact，不能写入 `result.yaml`、`quality_check.md`、
promotion 证据或正式结论。

### 创新代码改动多轮审查

凡是 idea、创新机制或 module trial 会改变模型、forward、loss、eval、data flow、scoring 或配置语义，
必须同时遵守：

```text
docs/workflow/innovation_code_review_protocol.md
```

最低审查顺序是：

```text
Review 0: Reader/Planner + Coordinator 检查 idea/source intent
Review 1: Interface Checker 在写代码前检查设计和接口
Review 2: Interface Checker + Quality Checker + Reviewer 在正式 run 前检查 code diff
Review 3: Log Analyst + Quality Checker + Result Analyst + Reviewer 在 run 后检查证据和结论
```

临时 sub-agent 可以启用，但必须加载对应长期角色的 `profile.md`、`memory.md` 和
`by_experiment/innovation/agents/README.md`。临时实例不自带可采信的长期记忆，必须把发现写入
`review_round_*.md`、`agent_summary.md`、`docs/workflow/issues/` 或对应 role memory。

Implementer 是同一代码路径唯一 writer。Reader/Planner、Interface Checker、Quality Checker、
Reviewer、Log Analyst 和 Result Analyst 默认只读。代码修复后必须重跑相关 review，不得沿用旧通过结论。

### 决定权

- Coordinator 按本矩阵选择 `activation_mode`，不是按个人偏好选择。
- Owner 可以随时要求向上升级为 `real_multi_agent`。
- 如果硬门要求 `real_multi_agent`，不能向下降级为普通 `role_only`；除非本次明确标记为 debug/smoke，且结果不进入正式证据。
- 如果工具不可用但任务硬门要求 `real_multi_agent`，Coordinator 必须在
  `tool_support.real_multi_agent_available: false` 和
  `tool_support.fallback_mode: role_only_with_independent_sequential_review` 中记录阻断原因，并在 owner 审核前不得跑正式实验或 promotion。

### 当前 CLIP-A-self ATTEMPT-007 适用结论

ATTEMPT-007 是对 ATTEMPT-003 配置的干净 confirmation run，但 owner 已经质疑流程、结果解释和多 agent 使用边界。
因此本轮应按 `real_multi_agent` 处理。启用角色：

```text
Coordinator
Runner
Log Analyst
Quality Checker
Result Analyst
Reviewer
```

不启用 Implementer 和 Interface Checker，除非 ATTEMPT-007 前修改训练代码、loss、eval、数据流、label mapping、
seen/unseen split、class order、logits shape 或 metric semantics。

## Agent 工作凭证

真实实验必须保存 agent 工作凭证，而不是保存完整聊天流水。最小 GitHub 记录是：

```text
agent_summary.md
```

它记录参与 agents、禁用 agents、输入、检查范围、发现、结论和证据引用。长报告、完整
日志分析、runner 细节和大型审查材料放入 Warehouse，并在 `agent_summary.md` 里引用
artifact id。具体规则见：

```text
docs/workflow/agent_report_policy.md
```

## 四类实验编排

调参：

```text
Coordinator -> Reader/Planner -> 用户选择 -> Runner -> Log Analyst + Quality Checker -> Coordinator
```

消融：

```text
Coordinator -> Reader/Planner -> Implementer -> Interface Checker -> Runner -> Log Analyst + Quality Checker + Result Analyst -> Coordinator
```

创新：

```text
Coordinator -> Reader/Planner -> Implementer -> Interface Checker -> Runner -> Quality Checker + Result Analyst + Reviewer -> Coordinator
```

重新复现：

```text
Coordinator -> Runner -> Log Analyst + Quality Checker -> Coordinator
```

Promotion：

```text
Coordinator -> Quality Checker + Interface Checker + Result Analyst -> Coordinator
```

## 禁止事项

- 多个 agents 同时写同一个 `INDEX.md`。
- 多个 agents 同时改同一实验代码路径。
- Runner 并行抢同一块 GPU。
- 非 Coordinator 删除分支、合并分支、创建 tag。
- 非用户明确要求时 push 到 GitHub。

## 进度看板联动

真实实验运行时，Coordinator 负责按 `docs/workflow/progress_dashboard.md` 创建和更新：

```text
.gtpj_runtime/runs/<run_id>/status.json
.gtpj_runtime/runs/<run_id>/events.jsonl
```

各 agent 在关键阶段向 Coordinator 汇报状态；Coordinator 收口写入 runtime 状态。
网页看板只读这些状态和 GitHub 账本，不直接启动训练、删除分支、打 tag、执行 promotion 或 push。

## 同步规则

修改 workflow agent 规范时：

1. 先更新 `docs/workflow/agents/` 和本文件。
2. 如果影响 agent 工作凭证，同步更新 `docs/workflow/agent_report_policy.md` 和模板。
3. 同步更新本地 `gtpj-workflow` skill 的 `references/agents/` 与相关 reference 文件。
4. 运行 skill 校验。
5. 运行仓库验证。
6. 提交 GitHub 文档；只有 owner 明确要求时才 push。
