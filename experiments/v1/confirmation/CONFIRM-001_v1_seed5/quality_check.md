# Quality Check

```text
runtime: RUN-20260626-141736-confirm-v1-seed5
quality_check_mode: STRICT
decision: PENDING
promotion_decision: not_applicable
```

## 范围

GTPJ-v1 baseline confirmation on CUB with seed=5. This run does not change model code, config values, data split, class order, label mapping, logits shape, or metric semantics.

## 发现

Pending until the training log is registered from Warehouse.

## 质量检查

- [x] 代码快照或 base version 明确。
- [x] 配置副本保存在实验目录。
- [ ] 外部日志 artifact URI、sha256、size 明确。
- [x] 结果口径明确。
- [x] 没有未声明的 eval / class order / logits shape 改动。
- [x] seen/unseen split、label mapping、class order 和 metric calculation 未改变或已按高风险记录。
- [ ] GitHub 目录中没有新增 raw log、checkpoint、generated figures。

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

PENDING
