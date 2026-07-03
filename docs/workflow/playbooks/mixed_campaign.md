# 执行卡：混合实验 Campaign

用于 `跑10创新+100调参` 这类任意组合实验命令。

先用 helper 自动路由，不要手工拆任务：

```bash
python workflow/gtpj_workflow.py start --phrase "跑2创新+8调参"
```

## 必读

```text
START_HERE.md
WORKFLOW_KERNEL.md
WORKFLOW_ROUTER.md
mixed_experiment_campaign_protocol.md
AGENT_RUNTIME_HARD_GATE.md
每个 requested workstream 对应的 playbook
```

## 结构

```text
campaign
  -> workstream: innovation / tune / ablation / confirmation / debug
    -> task
      -> run
```

不要给每个 run 创建一个永久 agent。

但 campaign / workstream / task 级正式角色必须是真实右侧临时 agents，并在
`agent_runtime.yaml` 中记录实例 id。没有通过 `validate-agent-runtime` 和
`multi-agent-preflight` 的 campaign 不能启动正式 Runner；不能用 sequential review
替代正式 campaign evidence。

每个 campaign task 必须有：

```text
subject_id
subject_type
evidence_state
next_allowed_transitions
result_ref
quality_ref
authority: derived_index_only
```

`RESULT_INDEX.md` 只能做派生索引，不能自建正式 H/U/S/ZS。

Campaign 目录不能成为单独的正式结果分支。每个 work item 必须回写到所属 subject：
version-level 写入 `experiments/vX/<type>/`，trial-internal 写入
`experiments/module_trials/.../TRIAL-xxx/attempts/ATTEMPT-xxx/`，真正新创新写入对应
IDEA/TRIAL，并由 campaign 只保存链接和调度索引。

`WORK_ITEMS.md` 必须把 owner-facing 编号和 runner job 编号拆开：

```text
INNOV-001 -> runner job DR-001
TUNE-001  -> runner job DR-003
```

不要直接用 `DR-003` 解释成第三个 tune，也不要把 runner-local `attempt_id`
解释成 GitHub 正式 `ATTEMPT-003`。

`campaign_run_map.md` 必须说明本 campaign 的调度和归属：哪些 work item、哪些 runner job、
正式写回哪个 subject、哪些只是 derived summary。不要把它叫作新方法
`framework_diagram.md`；新创新 / 新 Trial 自己必须有 trial-level framework diagram。

## 角色

campaign 级默认角色：

```text
工作流总控 (Workflow Coordinator)
Campaign 规划 (Campaign Planner)
运行监控 (Runner Monitor)
结果比较 (Result Comparator)
证据质量检查 (Evidence Quality Checker)
Warehouse 登记 (Warehouse Registrar)
```

再按对应 playbook 加入 workstream 专属角色。

## 调度规则

总控 (Coordinator) 负责优先级和边界。

运行监控 (Runner Monitor) 负责 GPU/服务器执行和失败隔离。

结果比较 (Result Comparator) 根据 evidence 决定哪些方向需要 3-repeat confirmation。

调度按 evidence state machine，不按 run 数硬排：

```text
hypothesis_ready -> interface_precheck_passed -> smoke_passed -> single_run_valid -> tune_promising -> ablation_supported -> min3_confirmed
```

## 必要 Campaign 汇报

```text
请求组合 requested mix
实际规划 runs
completed/running/pending/failed
最佳单次 best single
进入复现的 top candidates
confirmed/rejected directions
下一轮 10-50 run 计划
checkpoint retention 结果
work item id -> runner job id 映射
campaign run map 路径
formal subject result/quality 路径
```
