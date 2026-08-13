# 执行卡：复现 / 确认 Confirmation

用于判断一个结果能否在同一代码、配置、数据和评估条件下重现。

## 最短闭环

1. 在 `EXPERIMENT.yaml` 固定准确 commit、config、`original_seed`、data/split、训练日程和评估口径。
2. 在唯一 `PARAMETER_MATRIX.csv` 中预先列完最多 5 次 repeat。
3. 确认 clean worktree、数据身份、GPU 和新输出目录后，从同一冻结提交直接运行。
4. 每个 `RUN-xxx` 独立保留日志、U/S/H/ZS、best epoch 和必要模型。
5. 回填逐次值与 mean/min/max/range；失败也保留，不追加第 6 次。

若修改模型、训练、数据、评估、workflow、helper、模板或生成逻辑，先完成机器测试和两轮依次进行的只读审核；只复跑既有冻结提交时做开跑检查即可。

## 判定

正式复现使用 `repeat_type: exact_repeat`：

```yaml
original_seed:
max_attempts: 5
max_attempts_hard_cap: true
early_stop_on_best_hit: true
restore_target_H:
near_miss_tolerance_H:
near_miss_not_restored:
```

达到 `restore_target_H` 才是 best hit，并立即停止后续 pending repeat。落入容差但未达到目标只能记为 `near_miss_not_restored`。达到 5 次仍未还原就停止。

`seed_sweep`、`score_search` 和 `multi_seed_stability` 必须写 `not_confirmation_evidence: true`，不能冒充严格复现。promotion 或 baseline 结论还要依据稳定性规则，不能只挑最高单次。

当前通用规则见 `START_HERE.md` 和 `WORKFLOW_KERNEL.md`；详细判定见 `docs/workflow/protocols/experiment_protocol.md` 与 `docs/workflow/protocols/promotion.md`。
