# 执行卡：调参 Tune

正式入口固定为 `experiments/vX/tune/INDEX.md`，人看编号为 `VX-TUNE-xxx`。必须从
`framework/vX` 开 `exp/vX/tune/...` 分支；一个调参问题只有一张参数矩阵，每个参数组合
是一行 `RUN-xxx`。纯调参永远留在当前框架，不注册正式框架，也不创建 Tag。

用于参数、seed、epoch、batch、loss weight 或不改变方法语义的窄配置搜索。

## 必读

```text
START_HERE.md
WORKFLOW_KERNEL.md
docs/workflow/reference/GZSL_HARD_RULES.md
docs/workflow/core/AGENT_RUNTIME_HARD_GATE.md
docs/workflow/protocols/experiment_protocol.md
产生 raw artifact 时读 docs/workflow/protocols/ARTIFACT_REGISTRATION.md
```

如果调参发生在 module trial 内部，还要读：

```text
docs/workflow/protocols/module_trial_protocol.md
```

## 角色

正式 tune 默认使用 `real_multi_agent`：

```text
总控 (Coordinator)
调参规划 (Tune Planner)
运行监控 (Runner Monitor)
日志分析 (Log Analyst)
证据质量检查 (Evidence Quality Checker)
结果比较 (Result Comparator)
```

正式 Runner 启动前必须写 `agent_runtime.yaml`，记录左侧命名 Codex 线程的真实
`agent_instance_id`，并通过 `validate-agent-runtime` 和 `multi-agent-preflight`。
否则正式 tune 必须阻断。只有 owner 明确把目标改成非正式 `debug_smoke` 排障时，
才允许继续；该结果不能进入 keep / best / confirmation / promotion。

## 输出

版本级 tune：

```text
experiments/vX/tune/
```

trial 内部 tune：

新调参一律放在所属框架的 `experiments/vX/tune/TUNE-xxx/`，并登记到同目录的 `INDEX.md`。旧 Trial/Attempt 只用于回查；如果调参来自旧记录，把旧编号写进 `legacy_ref`，不要再创建新的 Attempt。

raw logs 和 checkpoints 留在 Warehouse。

## 决策规则

只调参数带来的提升不能开新的 `vX`。

重要 tuned config 必须经过 `repeat_type: exact_repeat` 后，才能作为正式数据表述：
锁定 `original_seed` 和原始配置，`max_attempts: 5`、`max_attempts_hard_cap: true`、`early_stop_on_best_hit: true`，
并声明 `restore_target_H`、`near_miss_tolerance_H` 和 `near_miss_not_restored`。接近但未达到目标
只能说明有效果、还有希望，不能说还原；同一候选无论是否还原成功都最多 5 次，5 次未还原不能继续加跑复现。换 seed 的 `seed_sweep` / `multi_seed_stability`
必须写 `not_confirmation_evidence: true`，只能作为搜索或稳定性诊断。

tune transition 默认只能进入：

```text
single_run_valid
tune_promising
rerun_required
rejected
stopped_no_gain
```

## 参数矩阵（2026-08-04 起）

每个具体调参任务都必须写入同一批次的 `PARAMETER_MATRIX.csv`，并自动生成给人阅读的 `PARAMETER_MATRIX.md`。一行是一个参数组合，不是一行概括整个 50/100 任务批次。开跑前必须写清相对基线的改动、随机种子、配置指纹和是否复跑；同一指纹已经出现时，必须明确 `repeat_of`，否则不得重复运行。详见 `docs/workflow/protocols/parameter_matrix_protocol.md`。
