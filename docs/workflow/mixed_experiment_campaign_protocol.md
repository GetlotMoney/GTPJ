# Mixed Experiment Campaign Protocol

本文定义任意组合实验命令的执行规则，例如：

```text
跑10创新+100调参
跑3复现+20调参+5消融
基于当前 best 跑2创新+50 trial 内调参+top5 复现
```

这类命令不是单个实验，而是一个 mixed experiment campaign。Coordinator 必须先把 owner 口令解析成多个 workstream，再按各自协议调度 agents、Runner、证据和收口。

## 1. 命令解析

组合命令按下面结构解析：

```yaml
owner_phrase: 跑10创新+100调参
task_type: mixed_experiment_campaign
base_version: current active baseline unless owner specifies another
requested_mix:
  innovation: 10
  tune: 100
```

支持的实验类型：

| 口令 | task type | 说明 |
|---|---|---|
| `创新` / `新模块` | `innovation / module trial` | 需要 idea/source、接口预审、代码实现、Review 0-3。 |
| `调参` / `tune` | `tune` | 只改 config / 超参，不改模型或评估语义。 |
| `消融` / `ablation` | `ablation` | 关掉、旁路或替换一个因素，必须过 interface gate。 |
| `复现` / `confirmation` | `confirmation` | 对 baseline、candidate 或 best attempt 做 clean rerun。 |
| `debug` / `smoke` | `debug / smoke` | 只定位问题，默认不进入正式证据。 |
| `promotion` / `升版本` | `promotion` | 不能按数量硬跑，只能由 evidence gate 触发。 |

如果 owner 没指定 base version，默认当前 active baseline。若命令同时包含 version-level 实验和 trial-internal 实验，Coordinator 必须拆开记录，不得混写。

## 2. Campaign 层级

组合实验使用下面层级：

```text
mixed_campaign
  -> workstream: innovation
  -> workstream: tune
  -> workstream: ablation
  -> workstream: confirmation
  -> batch
  -> run
  -> attempt
```

GitHub campaign ledger 推荐：

```text
experiments/campaigns/CAMP-YYYYMMDD-xxxx/
  campaign_manifest.yaml
  agent_runtime.yaml
  campaign_plan.md
  WORKSTREAMS.md
  SCHEDULER_STATE.yaml
  RESULT_INDEX.md
  DECISION_LOG.md
  AGENT_LIFECYCLE.md
  agent_summary.md
  quality_check.md
  final_report.md
```

具体实验证据仍写入原本归属目录：

```text
experiments/vX/tune/
experiments/vX/ablation/
experiments/vX/confirmation/
experiments/module_trials/.../TRIAL-xxx/attempts/ATTEMPT-xxx/
```

Campaign 目录只保存 routing index，不保存 authoritative result facts。`RESULT_INDEX.md`
只能引用正式 `result.yaml`、`quality_check.md`、manifest 和 Warehouse artifact。
正式 H/U/S/ZS 不得以 campaign 文件作为权威来源。

每个 campaign task 必须绑定：

```text
subject_id
subject_type
evidence_state
next_allowed_transitions
result_ref
quality_ref
authority: derived_index_only
```

## 3. Agent 生命周期

组合实验不按实验数量开永久 agent。默认只保留少量 campaign/workstream 级活上下文。

| 生命周期 | 存活时间 | 典型角色 | 说明 |
|---|---|---|---|
| `campaign_scoped` | 整个 mixed campaign | Workflow Coordinator, Runner Monitor, Result Comparator, Evidence Quality Checker | 负责全局调度、运行状态、结果比较和质量门。 |
| `workstream_scoped` | 一个实验类型 workstream | Innovation Planner, Tune Planner, Ablation Planner, Confirmation Planner | 负责该类型的候选、约束、队列和阶段性收口。 |
| `task_scoped` | 一个 trial / batch / review | Code Implementer, Interface Contract Checker, Independent Reviewer | 负责具体实现或审查，完成后写回文件。 |
| `run_scoped` | 一个 GPU run / log parse | Experiment Runner, Log Metric Parser, Warehouse Registrar | 负责运行、日志解析、artifact 登记。 |
| `cross_workflow` | 跨多个 campaign | 可选 persistent thread | 只有 owner 明确要求或长期追踪角色需要时启用。 |

默认 agent mode：

```yaml
activation_mode: real_multi_agent
agent_instance_mode: temporary_subagent
lifecycle: campaign_scoped | workstream_scoped | task_scoped | run_scoped
```

`persistent_thread` 不是默认值。它只用于跨 workflow 可见追踪，不能作为正式证据源。

正式 campaign runner start 前必须通过 `docs/workflow/AGENT_RUNTIME_HARD_GATE.md`：

```bash
python workflow/gtpj_workflow.py validate-agent-runtime --path experiments/campaigns/CAMP-xxx/agent_runtime.yaml
```

如果侧边栏没有真实临时 agents，或 `agent_runtime.yaml` 没有记录真实实例 id，本 campaign
只能作为 debug/smoke 或候选计划，不能启动正式 Runner。

Owner 是 campaign 的默认监控者。混合实验不能在启动 Runner 后静默等待结束；必须维护
`AGENT_ACTIVITY.md`，并在当前对话或明确 Monitor 线程持续汇报：

```text
哪个智能体在做什么
哪个 workstream / run 正在推进
completed / running / pending / failed
当前 best 只是 single 还是 confirmed
证据写入位置
下一步动作
```

如果 Coordinator 需要暂停当前主对话，必须先给出 `monitor_handoff`，包括下一次检查命令、
活动流位置和跑完后接手的 Log / Result / Quality agents。

## 4. Agent 池

组合 campaign 默认启用一个小型 agent 池：

```text
Workflow Coordinator
Campaign Planner
Runner Monitor
Result Comparator
Evidence Quality Checker
Warehouse Registrar
```

按 workstream 增加角色：

| Workstream | 增加角色 |
|---|---|
| innovation | Source Reader, Idea Planner, Code Implementer, Interface Contract Checker, Independent Reviewer |
| tune | Tune Planner, Experiment Runner, Log Metric Parser |
| ablation | Ablation Planner, Code Implementer, Interface Contract Checker, Experiment Runner, Log Metric Parser |
| confirmation | Confirmation Planner, Experiment Runner, Log Metric Parser |
| promotion | Promotion Manager, Evidence Quality Checker, Independent Reviewer, Result Comparator |

同一代码路径只能有一个 `Code Implementer`。Runner 串行持有 GPU lock；多卡时可以有多个 run worker，但每个 worker 只执行冻结后的 run command。

## 5. 调度规则

Coordinator 必须按下面顺序处理任意组合命令：

```text
1. Parse owner phrase into requested_mix.
2. Run baseline/status preflight.
3. Build campaign_manifest and workstreams.
4. Spawn required right-sidebar temporary agents and write agent_runtime.yaml.
5. Validate agent_runtime.yaml before any formal Runner start.
6. Freeze campaign plan before real runs.
7. For each workstream, generate candidates or select ready ideas.
8. Convert candidates into batches with run_commit/config/artifact target.
9. Runner executes only frozen batches.
10. Log Metric Parser extracts metrics.
11. Evidence Quality Checker validates artifacts and boundaries.
12. Result Comparator updates ranking and next actions.
13. Coordinator records decisions and schedules repeat/ablation/promotion only if gates pass.
14. Coordinator keeps owner-visible activity reports until closeout or handoff.
```

组合实验按证据成熟度路由，而不是按 run 数静态排队：

```text
hypothesis_ready
-> interface_precheck_passed
-> smoke_passed
-> single_run_valid
-> tune_promising
-> ablation_supported
-> min3_confirmed
-> promotion_candidate
```

调度原则：

- 不允许 100 个 tune 在没有 baseline repro/status 的情况下直接开跑。
- 不允许 10 个 innovation 同时改同一代码路径。
- tune 可以在 frozen baseline 上批量跑；innovation 必须逐个通过 source、interface、code review 和 smoke。
- innovation 的代码准备可以和 tune 的 frozen runs 并行，但最终 GitHub ledger 只能由 Coordinator 写。
- 任一 workstream 产生异常指标或接口疑点，必须暂停该 workstream，不能污染其它 workstream。
- top candidates 才进入 repeat；默认 min3 repeat 后才允许正式结论。

## 6. “跑10创新+100调参”的默认展开

命令：

```text
跑10创新+100调参
```

默认展开：

```yaml
campaign_type: mixed_experiment_campaign
requested_mix:
  innovation: 10
  tune: 100
base_version: current active baseline
agent_lifecycle:
  campaign_scoped:
    - Workflow Coordinator
    - Runner Monitor
    - Result Comparator
    - Evidence Quality Checker
  workstream_scoped:
    innovation:
      - Source Reader
      - Idea Planner
  tune:
    - Tune Planner
  task_scoped:
    innovation:
      - Code Implementer
      - Interface Contract Checker
      - Independent Reviewer
  run_scoped:
    - Experiment Runner
    - Log Metric Parser
    - Warehouse Registrar
```

Agent 权限：

```text
Log/Result roles propose transition.
Interface/Quality/Reviewer roles check transition.
Coordinator applies transition.
```

默认执行阶段：

```text
Phase 0: preflight
  检查 repo、baseline repro status、GPU lock、server path、artifact boundary、checkpoint retention。

Phase 1: planning
  选择 10 个 ready innovation ideas；生成 100 个 tune candidates；写 campaign plan。

Phase 2: freeze
  提交 campaign plan / configs / queues 的 pre-run freeze commit。

Phase 3: execution
  tune workstream: 分批运行 100 个 frozen config。
  innovation workstream: 对每个 idea 执行 Review 0-3，代码实现、smoke、正式 run。

Phase 4: consolidation
  每完成一个 batch 或一个 innovation attempt，解析日志、登记 artifact、更新 RESULT_INDEX。

Phase 5: selection
  选 top candidates，安排 min3 repeat、必要 ablation 或 confirmation。

Phase 6: closeout
  写 final_report、quality_check、agent_summary、decision log。
```

如果 10 个 innovation 中某个 idea 不 ready，Coordinator 可以从 selected queue 补位；没有补位时必须把该 slot 标成 blocked，不得编造 idea。

如果 100 个 tune 中某些候选明显重复、无效或越界，Tune Planner 可以合并或拒绝，但必须在 `DECISION_LOG.md` 写明原因。

## 7. Workstream 之间的优先级

默认优先级：

1. Hard gate 和 reproducibility diagnosis。
2. 已冻结、低风险、不会改代码的 tune / confirmation runs。
3. 已通过 Review 2 的 innovation runs。
4. 新 innovation implementation。
5. Promotion。

原因：

- GPU 不应闲置，但不能让未审查代码抢先进入正式 run。
- tune 是 code-frozen，可批量执行。
- innovation 是 code-changing，必须先审查再运行。
- promotion 是结果，不是输入命令；只由证据触发。

## 8. 证据规则

每个 workstream 必须分别有：

```text
config / candidate list
manifest
result
quality
agent_summary entry
artifact reference
decision
```

Campaign 总账本必须能回答：

- owner 请求了哪些实验类型和数量；
- 实际启动了多少、完成多少、失败多少、阻断多少；
- 每类实验的 top result；
- 哪些结果进入 repeat；
- 哪些结果被 reject / rerun / keep / promote；
- 每个正式结论对应哪个 commit、config、artifact 和 quality check。

## 9. 失败隔离

一个 workstream 失败不能污染整个 campaign：

- tune batch 中单个 run 失败，只标记该 run failed，继续其它 frozen runs。
- innovation 的 Review 1/2 blocked，只阻断该 idea，不阻断 tune workstream。
- interface 或 metric semantics 全局不清楚，阻断所有依赖该语义的 workstream。
- server/GPU/storage 失败，Runner Monitor 暂停新 run，已完成证据照常入账。

## 10. Stop / Pause Conditions

满足任一条件时，Coordinator 必须暂停或收口：

- 达到 owner 指定的数量、时间或算力预算；
- 连续 N 个 batch 没有产生超过 reference 的候选；
- top candidates 已完成 min3 repeat；
- hard gate 阻断；
- GPU / server / data / artifact 状态不可恢复；
- campaign 已达到 final deliverable 标准。

## 11. Checkpoint Retention

组合 campaign 仍遵守统一 retention：

```text
每个 campaign 或 batch 完成后，只保留最好的 3 个 checkpoint。
其余 checkpoint 删除或移入非默认保留区。
GitHub 只记录保留 checkpoint 的 artifact id、URI、sha256、size 和指标。
```

## 12. 最小汇报格式

组合 campaign 汇报必须按实验类型分块：

```text
Campaign:
  requested_mix:
  completed / running / failed / blocked:

Innovation:
  selected ideas:
  implemented:
  blocked:
  best:

Tune:
  planned:
  completed:
  top5:

Repeat / Confirmation:
  repeated candidates:
  min / mean / max:

Quality:
  hard blockers:
  artifact issues:

Next:
  smallest valid next action:
```
