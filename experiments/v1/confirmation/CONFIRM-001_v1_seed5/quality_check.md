# Quality Check

```text
runtime: RUN-20260626-141736-confirm-v1-seed5
quality_check_mode: STRICT
decision: PASS_WITH_WARNINGS
promotion_decision: not_applicable
```

## 范围

GTPJ-v1 baseline confirmation on CUB with seed=5. This run does not change model code, config values, data split, class order, label mapping, logits shape, or metric semantics.

## 发现

- 训练完成并出现最终 `Training Finished!` / `Best Results @ Epoch 32` 汇总。
- 指标从 Warehouse 训练日志解析：U=71.35, S=76.35, H=73.77, ZS=81.24。
- `conda run` 包装器在训练结束后触发 GBK `UnicodeEncodeError`，runner stderr 已作为 warning artifact 登记；指标以训练日志为准。
- 本地 `validate` / `audit-boundary` 通过；远端闭环需要后续 push 后再跑 `validate-remote`。

## 质量检查

- [x] 代码快照或 base version 明确。
- [x] 配置副本保存在实验目录。
- [x] 外部日志 artifact URI、sha256、size 明确。
- [x] 结果口径明确。
- [x] 没有未声明的 eval / class order / logits shape 改动。
- [x] seen/unseen split、label mapping、class order 和 metric calculation 未改变或已按高风险记录。
- [x] GitHub 目录中没有新增 raw log、checkpoint、generated figures。

## Promotion Gate（仅正式提升 vX 时填写）

- [ ] parent_version / parent_tag 明确。
- [ ] trial tag 指向 README 中记录的 code_commit。
- [ ] baseline H、trial H、delta H 明确。
- [ ] U/S/ZS、best epoch、seed 明确。
- [ ] 同 seed 对照明确；高风险改动已说明是否需要多 seed。
- [ ] trial config 和新版本 config 路径明确。
- [ ] 外部日志 artifact URI、sha256、size、保留位置明确。
- [ ] class order、seen/unseen split、logits shape、metric calculation 未改变。
- [ ] input/output shape、loss、eval、checkpoint 变化已声明。
- [ ] switch off 能回到 parent_version 行为。
- [ ] VERSION、VERSION_TREE、EXPERIMENT_REGISTRY、PROJECT_STATUS、PROJECT_STRUCTURE、README 已更新。
- [ ] idea_tree current_version 和必要的 version_scores.vX 已更新。
- [ ] 新 baseline tag 准备打在包含正式版本代码和版本材料的明确 commit 上。
- [ ] main 当前代码只有 owner 明确执行 activate-version vX 时才切换；默认不切换。

## 决策

PASS_WITH_WARNINGS. Baseline confirmation is usable as a local reproduced result. Treat remote governance as incomplete until this branch and the required main commit are pushed and `validate-remote` passes.
