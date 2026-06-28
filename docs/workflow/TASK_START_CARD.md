# Task Start Card

本文件是每次 GTPJ 工作开始前由 Coordinator 自动生成的启动卡。它不替代
`WORKFLOW_ROUTER.md`，而是把 Router 的判断落成一张可检查的任务单，避免每次靠口述重新解释。

Owner 不需要说“开启动卡”，也不需要自己填表。Owner 日常只需要使用
`QUICK_START.md` 里的短口令；Coordinator 先输出 `TASK_START_MINI.md` 的 8 字段 mini
启动卡，再在后台展开完整启动卡字段。

启动卡可以先写在当前对话里。纯规划阶段不要为了启动卡提前创建空 run 目录。只有当 owner 明确同意开工，
或本轮请求已经明确包含“开始/你来操作/跑这个实验”时，才把启动卡转成正式文件、分支、实验目录或运行动作。

## 0. Owner 极简输入

Owner 最简单只需要说这些口令：

```text
查状态
复现
调参
消融
开新模块
开下一个新模块
试这个：<一句话想法>
继续上一个
别问，给我三个候选
升版本
切版本
```

常见说法：

```text
复现。
调参，先给三个候选。
消融，把 topo loss 关掉看看。
开新模块。
开下一个新模块。
试这个：把 CLIP-A-self 接进文本 adapter。
继续上一个。
别问，给我三个候选。
```

如果 owner 只说：

```text
开新模块
```

Coordinator 必须默认理解为：基于当前 active baseline，从该版本 selected ready idea 队列自动选一个
new module trial；允许改代码；走 module trial 合规路径；不 push。若没有 ready idea，只问一个最小问题。

Owner 不需要提前判断：

- 是否进入 `idea_tree`；
- 应该写 GitHub 还是本地 Research/Warehouse；
- 需要哪些 agents；
- 需要哪些 hard gates；
- 分支名、目录名、artifact id 怎么写。
- 是否要说 `real_multi_agent`、`Review 0-3`、`artifact boundary` 或 `pre-run freeze`。

这些都由 Coordinator 在启动卡里给出。

## 0.1 对话先行

每次正式开工前，Coordinator 先输出一个简短判断：

```text
能不能开工：
任务类型：
基于版本：
为什么这样归类：
当前缺口：
下一步最小动作：
```

如果能开工，Coordinator 再给启动卡摘要。
如果不能开工，Coordinator 只问最关键的 1 个问题，或给出最小补齐动作。

在下面情况出现前，不要改代码、跑实验、建实验目录或登记结果：

- owner 明确说“开始”“跑”“你来操作”“按这个做”；
- 或者 owner 本轮请求本身已经明确授权实际操作；
- 或者任务只是只读检查、解释或建议，不会写文件也不会跑训练。

## 1. 使用时机

每次出现下面任一动作前，都先填写启动卡：

- 读论文并准备产出 idea；
- 修改模型、forward、loss、eval 或数据流；
- 跑 tune、ablation、confirmation 或 debug/smoke；
- 登记实验结果、日志、checkpoint 或 generated figures；
- promotion、set-current-version 或 activate-version。

如果只是普通聊天解释，可以不写完整启动卡；但只要要改文件、跑实验或登记结果，Coordinator 就必须自动写。

## 2. 最小启动卡

```yaml
task_id:
date:
owner_request:

router:
  task_type:
  enters_idea_tree:
  github_writes:
  local_writes:
  coupled_update:
    required:
    order:
    skip_reason:
  required_protocols:

version:
  base_version:
  base_code_tag:
  current_branch:
  suggested_branch:

inputs:
  paper_or_source:
  idea_id:
  config:
  dataset:
  seed:

agents:
  activation_mode:
  activation_reason:
  decision_basis:
    fastest_valid_path:
      selected:
      why_fastest:
      why_still_valid:
      skipped_agents:
      parallelized_roles:
      serialized_roles:
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
  runner_required:
  gpu_lock_required:
  memory_policy:
    session_context_allowed:
    codex_memory_allowed:
    repo_state_required:
    memory_used:
    memory_sources:
    agent_profile_files:
    agent_memory_files:
    verified_against_current_repo:

hard_gates:
  interface_contract:
  innovation_code_review:
  source_status:
  artifact_boundary:
  metric_semantics:
  evidence_level:
  confirmation_grade:
  promotion_gate:

expected_outputs:
  github:
  research:
  warehouse:
  sync_check:

stop_if: copy the mandatory blocker checklist from section 5; never leave this field empty.
```

## 3. 必填判断

`router.task_type` 只能从 Router 支持的任务类型中选择：

```text
paper intake / idea discovery
local heuristic idea
tune
ablation
confirmation
debug / smoke
innovation / module trial
promotion
set-current-version
activate-version
progress dashboard
```

`enters_idea_tree` 使用总判断规则：

```text
实验是为了调/查/验证已有正式 baseline -> experiments/vX，不进 idea_tree。
实验是为了调/查/确认某个 module trial 内部模块 -> experiments/module_trials/.../attempts/ATTEMPT-xxx，不另进 idea_tree。
实验是为了证明一个新方法值得存在 -> idea_tree + module_trials。
```

`router.coupled_update` 必须写清 GitHub、Research、Warehouse 是否需要联动：

- 读论文、提取 idea、新机制设计：通常 `required: true`，先 Research，后 GitHub 轻量索引。
- 真实实验运行：通常 `required: true`，先 Warehouse raw artifact，后 GitHub 账本。
- 普通 tune / ablation / confirmation：如果只改变结果账本，不改变 idea 结论，可写 `required: false`，
  但必须在 `skip_reason` 说明为什么不更新 Research。
- trial 结论、version score、promotion 或 next_action 改变：必须同步 GitHub idea index 和
  Research decision/history。

`expected_outputs.sync_check` 必须回答：

```text
GitHub 轻量记录能否找到 Research 长版材料？
GitHub 结果记录能否找到 Warehouse artifact？
人类版记录和机器版记录是否一致？
哪些同步被跳过，原因是什么？
```

`agents.activation_mode` 只能选择：

```text
role_only
real_multi_agent
```

`role_only_with_independent_sequential_review` 不是第三种 `activation_mode`。它只能写在：

```yaml
agents:
  activation_mode: role_only
  tool_support:
    real_multi_agent_available: false
    fallback_mode: role_only_with_independent_sequential_review
```

该 fallback 只能说明当前环境无法启动真实 sub-agent 后的顺序独立复核状态；不能用于
promotion、正式 best 结论或 owner 已明确要求真实多 agents 的任务，除非 owner 明确接受
debug/smoke 降级。

必须选择 `real_multi_agent` 的情况：

- owner 明确要求多 agents、独立 review 或多方验证；
- 任务修改模型结构、forward、loss、eval、数据流、label mapping、seen/unseen split、class order 或 logits shape；
- 新 module trial 的实现、接口检查、promotion 前复核；
- 结果异常、指标争议较大，或 owner 明确质疑当前解释；
- 准备写 `promotion_decision: promote`、创建新 `vX` 或打 version tag；
- 任务需要同时阅读论文、源码、日志和质量证据，且这些输入可以被不同角色独立检查。

允许选择 `role_only` 的情况：

- 只读解释、状态检查、配置查看；
- 不改代码、不改实验语义的窄范围 rerun / confirmation 准备；
- 单一 Runner 按 frozen config 串行训练；
- 结果只作为 debug/smoke；
- 只做账本格式整理且不改变实验结论。

如果选择 `role_only`，启动卡必须写明为什么不启用真实多 agents，以及哪些角色由主 agent 代执行。

`agents.decision_basis.fastest_valid_path` 必须说明本次为什么选择最快合规路径：

- 简单只读、debug/smoke、单 Runner frozen config、账本格式整理等任务，默认选择 `role_only`，不启动不必要 agents。
- 如果 hard gate 或 owner 要求 `real_multi_agent`，默认并行执行只读审查角色，只串行 Implementer、Runner 和 Coordinator 写账本。
- 被跳过的角色必须写入 `skipped_agents`，并说明跳过后为什么仍然满足 hard gates。

`agents.required_real_agents` 是真实 sub-agent 硬需求角色列表：

- `activation_mode: real_multi_agent` 时，填写必须独立执行的角色列表；
- `activation_mode: role_only` 时，填写 `[]`；
- 如果按规则应使用真实多 agents 但工具不可用，填写 `[]`，并在 `tool_support.fallback_mode` 写
  `role_only_with_independent_sequential_review`，同时触发阻断或 debug-only 降级。

`agents.required_roles` 必须写角色名，不写“按需”。常用角色集合：

| 任务 | 必需角色 |
|---|---|
| 只读状态 / 配置检查 | Coordinator，必要时 Reader/Planner |
| 调参建议 | Coordinator、Reader/Planner、Result Analyst |
| 调参真实运行 | Coordinator、Runner、Log Analyst、Result Analyst、Quality Checker |
| confirmation / rerun | Coordinator、Runner、Log Analyst、Result Analyst、Quality Checker |
| ablation | Coordinator、Runner、Log Analyst、Interface Checker、Result Analyst、Quality Checker |
| innovation / module trial | Coordinator、Reader/Planner、Implementer、Interface Checker、Runner、Log Analyst、Result Analyst、Quality Checker、Reviewer |
| promotion | Coordinator、Quality Checker、Reviewer、Result Analyst，必要时 Interface Checker |
| debug / smoke | Coordinator、Runner、Log Analyst，必要时 Interface Checker |

`real_multi_agent` 下，Reader/Planner、Log Analyst、Quality Checker、Result Analyst、Reviewer 默认可以并行。
Runner 永远串行并锁 GPU。Implementer 是同一代码路径的唯一 writer。Coordinator 是最终 GitHub 账本唯一写入者。

`agents.memory_policy` 必须写清：

- session context 只能作为任务上下文，不能直接当证据；
- Codex 全局 memory 或历史会话摘要只能用于定位，必须回到当前仓库、日志或 artifact 验证；
- 长期 agent 记忆必须来自 `docs/workflow/agents/shared_roles/<role>/memory.md`，并记录实际读取文件；
- repo state 和 artifact 是正式实验事实源；
- 使用 memory 时，必须记录 `memory_sources` 和 `verified_against_current_repo`。

## 4. 各任务补充字段

### Paper Intake / Idea Discovery

必须记录：

- paper id 或 source id；
- `_inbox` 输入文件；
- `PAPERS_INDEX.md` 当前状态和目标状态；
- Research 写入位置；
- 论文是否包含官方 GitHub / code URL；
- 若包含，`official_code_url`、`official_code_path`、clone commit、是否排除了数据/权重；
- 是否只进 inbox；
- 是否已经 source review；
- 何时允许升级成正式 `IDEA-xxxx`。
- 是否同步 GitHub `idea_tree/sources/`、`idea_tree/inbox.md` 或正式 `IDEA.md`。

### Tune

必须记录：

- base version；
- 这是 version-level tune，还是 trial-internal `param_tune`；
- 调哪个参数；
- old value / new value；
- 预期成本；
- 是否已经试过；
- 为什么不改变模型结构、forward、loss 语义或 eval 语义。

如果是 trial-internal `param_tune`，写入该 trial 的 `ATTEMPTS.md` 和
`attempts/ATTEMPT-xxx/`，并遵守 `module_trial_protocol.md`，不要写入 `experiments/vX/tune/`。

### Ablation

必须记录：

- 这是 version-level ablation，还是 trial-internal narrow ablation；
- disabled module / disabled factor；
- switch key；
- baseline-off path；
- interface_check 是否阻塞；
- 一次只消融的主因素。

如果是 trial-internal narrow ablation，只能解释当前 trial 的局部因素；如果改变实现假设、
forward 路径、新 loss 或评估语义，就新开 `TRIAL-002`。

### Confirmation

必须记录：

- 这是 version-level confirmation，还是 trial-internal clean confirmation；
- 要确认的 baseline tag；
- config；
- seed；
- 数据 split、class order、label mapping；
- 预期对齐的旧结果；
- 证据等级目标：`quick_local`、`valid_single_run`、`confirmation_grade` 或 `baseline_grade`；
- `best_observed_H` 和 `confirmed_H` 的当前状态；
- confirmation target、tolerance 和失败时的降级规则；
- 将被锁定的 `run_commit`；
- 这次 confirmation 是从哪个 `pre-run freeze commit` 启动。

如果是 trial-internal clean confirmation，目标是确认当前 `best_attempt_id`，写入该 trial 的
`ATTEMPTS.md` 和 `attempts/ATTEMPT-xxx/`。

### Debug / Smoke

必须记录：

- debug 目标；
- 是否会产生长期证据；
- 如果要引用结果，转入哪个正式实验目录；
- debug 结果默认不能作为有效实验结论。

### Innovation / Module Trial

必须记录：

- 正式 `IDEA-xxxx`；
- `source_type`、`source_ref`、`source_status`；
- `version_scores.<base_version>`；
- source idea file；
- module insertion point；
- input/output contract；
- shape invariants；
- baseline-off switch；
- trial branch 和 trial tag 计划；
- attempt 级 `config.yaml` 和 `ATTEMPTS.md` 计划行是否已经冻结到 `pre-run freeze commit`；
- 本次真实 run 将使用的 `run_commit`。
- 是否触发 `innovation_code_review_protocol.md`；
- `idea_intent_check.md`、`interface_precheck.md`、`review_round_1.md`、
  `review_round_2.md` 的计划位置；
- 临时 agents 是否允许，哪些角色必须由真实独立 agents 执行；
- Review 0-3 的阻断条件和当前状态。

### Promotion

必须记录：

- parent version / parent tag；
- trial code tag；
- baseline H、trial H、delta H；
- U/S/ZS、seed、best epoch；
- complete manifest/result/quality/interface evidence；
- `evidence_level: baseline_grade`；
- `confirmation_status: confirmed`；
- `best_observed_H` 和 `confirmed_H` 已区分；
- owner override 是否只是激活主线代码，且是否需要标成 `owner_activated_unconfirmed`；
- target version；
- 是否只是生成版本账本，还是 owner 明确要求 activate-version。

## 5. 启动卡阻断条件

遇到以下情况，先停止，不跑实验：

- 工作区 dirty 且未说明哪些改动属于当前任务；
- 启动卡没有填写 `agents.activation_mode`、`activation_reason`、`decision_basis`、`single_agent_allowed` 或 `required_real_agents`；
- 启动卡没有填写 `agents.required_roles`、`tool_support` 或 `memory_policy`；
- 按规则应使用 `real_multi_agent`，但启动卡写成 `role_only`；
- owner 明确要求多 agents，但启动卡没有写 `real_multi_agent`；
- 工具不可用但任务硬门要求 `real_multi_agent`，且没有阻断或明确标成 debug/smoke 降级；
- `agents.activation_mode` 写成了 `role_only_with_independent_sequential_review`；
- 使用了 memory-derived fact，却没有说明 memory 来源和当前仓库 / artifact 验证方式；
- 这是一个真实训练 / confirmation / tune / trial run，但工作区不是 clean；
- 运行前新增了 attempt config、`ATTEMPTS.md`、启动卡或其他预跑账本，但还没有先提交成 `pre-run freeze commit`；
- 预期运行 commit 不明确，或无法把本次 run 唯一映射到一个冻结后的 `run_commit`；
- module trial 没有正式 idea；
- idea 来源是 `unknown` 或 `unverified` 却要开 trial；
- idea / 创新 / module trial 将改代码，但没有写明
  `innovation_code_review_protocol.md` 的 Review 0-3 计划；
- 创新代码改动没有使用 `real_multi_agent`，或没有把 Reader/Planner、Interface Checker、
  Quality Checker、Reviewer 等必须独立复核角色写入 `required_real_agents`；
- Review 0-3 任一轮存在 blocking issue，却要启动 Runner、选择 best 或 promotion；
- label mapping、seen/unseen split、class order、logits shape 或 metric semantics 不清楚；
- 没有填写 `evidence_level`，或把 `quick_local` / `valid_single_run` 结果写成 confirmed baseline；
- `best_observed_H` 和 `confirmed_H` 混写，导致无法判断复现失败影响哪个结论；
- 启动卡涉及状态、复现、结果比较、promotion 或 tag，但没有先检查 `baseline_repro_status`；
- raw logs、checkpoint、generated figures 会写进 GitHub；
- Runner 需要 GPU，但 lock 状态未知；
- promotion 只看 H 提升，没有完整证据链。

## 6. 最小开工输出

每次任务启动时，Coordinator 至少输出：

```text
任务类型：
是否进入 idea_tree：
GitHub 写入：
本地写入：
必读协议：
启用 agents：
agents.activation_mode：
agents.activation_reason：
agents.decision_basis.fastest_valid_path：
agents.required_roles：
agents.required_real_agents：
agents.tool_support：
硬门：
当前阻塞：
pre-run freeze commit：
run_commit：
post-run result commit：
sync_check：
```

这段输出就是后续 agent 的共同入口。
