# First Closed Loop

本文件规定 GTPJ 工作流第一次真正开跑时的最小闭环。目标不是马上做大实验，而是验证：

```text
Router -> Task Start Card -> agents/gates -> Warehouse artifact -> GitHub ledger -> quality check
```

## 1. 当前建议

第一条闭环建议使用低风险任务，不从 VDT/self-attn trial 开始。

推荐顺序：

1. `debug / smoke` readiness check：不写长期实验结果，只确认环境、Git、路径和 helper 可用。
2. `tune-suggest`：只读配置和 tune 索引，不启动训练，不写实验结果。
3. `confirmation` 或一个极小 tune：用户确认后才启动 Runner。

这样可以先验证工作流通路，再回头补复杂的 innovation / module trial。

## 2. Readiness Check

在 `main` 上执行：

```bash
git status --short
python workflow/gtpj_workflow.py validate
python workflow/gtpj_workflow.py audit-boundary
python workflow/gtpj_workflow.py validate-remote
python workflow/gtpj_workflow.py tune-suggest --version v1
```

预期：

```text
working tree clean
validate-ok
audit-boundary-ok
validate-remote-ok
tune-suggest 只输出候选，不改文件
```

这个阶段不需要创建 `.gtpj_runtime/`，也不需要创建 experiment run 目录。

## 3. 第一张启动卡

如果 readiness check 通过，下一步由 Coordinator 输出启动卡。

建议第一张真实启动卡：

```yaml
task_id: START-001
owner_request: first workflow closed loop
router:
  task_type: confirmation
  enters_idea_tree: false
  github_writes:
    - experiments/v1/confirmation/<CONFIRM-ID>/
  local_writes:
    - GTPJ_Warehouse/runs/v1/confirmation/<CONFIRM-ID>/
  required_protocols:
    - experiment_protocol.md
    - artifact_policy.md
    - ARTIFACT_REGISTRATION.md
    - quality_gate.md
version:
  base_version: v1
  base_code_tag: v1
agents:
  serial:
    - Coordinator
    - Runner
  parallel:
    - Log Analyst
    - Quality Checker
  runner_required: true
  gpu_lock_required: true
hard_gates:
  interface_contract: unchanged
  artifact_boundary: raw artifacts only in Warehouse
  metric_semantics: protected evaluator
```

Runner 只有在 owner 明确同意跑实验后才启动。

## 4. 第一条正式证据链

真实运行结束后，必须完成：

```text
Warehouse raw log/checkpoint/cache
Warehouse ARTIFACT_REGISTRY.yaml
GitHub manifest.yaml
GitHub result.yaml
GitHub result.md
GitHub quality_check.md
experiments/EXPERIMENT_REGISTRY.md
experiments/v1/<kind>/INDEX.md
```

如果只是 debug/smoke，默认不形成有效实验结果。只有补齐上述证据链后，才可以升级成正式实验记录。

## 5. 回到 VDT/self-attn Trial 的条件

只有第一条闭环验证通过后，再恢复 VDT/self-attn stash，并按新规范补：

- 正式 `IDEA-xxxx`；
- source review 或 local heuristic 说明；
- `version_scores.v1`；
- module trial root `IDEA.md`；
- `interface_check.md`；
- Warehouse artifact registry；
- manifest/result/quality evidence。

不要直接把 stash 中的 trial 当作已合规证据。
