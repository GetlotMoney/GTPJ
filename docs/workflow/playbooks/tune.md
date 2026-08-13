# 执行卡：调参 Tune

用于不改变模型、数据和评估语义的参数、seed、epoch、batch 或 loss weight 搜索。

## 最短闭环

1. 从 `TEMPLATE.yaml` 锁定的准确母版 commit 建立 `exp/vX/tune/...` 分支。
2. 在唯一 `PARAMETER_MATRIX.csv` 中逐行写清基线、变量、seed、配置指纹和 `repeat_of`。
3. 确认 clean worktree、数据/划分身份、GPU 和新输出目录后，直接运行现有训练入口。
4. 每个 `RUN-xxx` 独立保存日志、U/S/H/ZS 和需要保留的最佳模型。
5. 回填全部结果；失败也记录。纯调参不能注册新框架或 Tag。

## 复现边界

重要 tuned config 进入正式表述前，使用 `repeat_type: exact_repeat`，固定 `original_seed` 和原始配置，并写明：

```yaml
max_attempts: 5
max_attempts_hard_cap: true
early_stop_on_best_hit: true
restore_target_H:
near_miss_tolerance_H:
near_miss_not_restored:
```

`seed_sweep`、`score_search` 和 `multi_seed_stability` 必须写 `not_confirmation_evidence: true`，不能冒充严格复现。

当前通用规则见 `START_HERE.md` 和 `WORKFLOW_KERNEL.md`；详细复现判定见 `docs/workflow/protocols/experiment_protocol.md` 与 `docs/workflow/protocols/promotion.md`。
