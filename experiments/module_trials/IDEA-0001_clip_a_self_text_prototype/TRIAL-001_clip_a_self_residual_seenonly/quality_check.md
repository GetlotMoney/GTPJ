# Quality Check

```text
runtime:
quality_check_mode: STRICT
decision: PASS_REVISE
promotion_decision: rejected
```

## 范围

- 代码层：`train_GTPJ_CUB.py`, `model/MyModel.py`
- 账本层：`experiments/module_trials/IDEA-0001_clip_a_self_text_prototype/TRIAL-001_clip_a_self_residual_seenonly/`
- 不修改：`config/versions/v1.yaml`, `experiments/v1/config.yaml`, eval 脚本, dataset split。

## 发现

- Interface Checker 只读预审确认：当前 baseline 文本输入是 class-level `[C（类别数量）, D（文本特征维度）]`，TRIAL-001 必须补 sentence-level `[C（类别数量）, M（每类句子数量）, D（文本特征维度）]` 输入，且最终 scorer 前仍回到 `[C, D]`。
- Reader/Planner 只读预审确认：论文 PDF 和官方 `VDT-Adapter` 代码均可复核，`source_status: verified` 合理。
- TRIAL-001 没有新增 loss；L2SP 不是本 trial 主变量。
- `clip_a_self_apply_unseen: false`，unseen prototype 默认保持 raw sentence mean。

## 质量检查

- [x] 代码快照或 base version 明确。
- [x] 配置副本保存在实验目录。
- [x] 外部日志 artifact URI、sha256、size 明确。
- [x] 结果口径明确。
- [x] 没有未声明的 eval / class order / logits shape 改动。
- [x] seen/unseen split、label mapping、class order 和 metric calculation 未改变或已按高风险记录。
- [x] GitHub 目录中没有新增 raw log、checkpoint、generated figures。

## 接口预检

```text
shape_probe_ok
switch_off_max_abs_diff: 0.0
switch_on_logits: [2（图片/样本数量）, 150（seen 类数量）]
switch_on_logits_200: [2（图片/样本数量）, 200（总类别数量）]
loss_keys: loss, loss_CE, loss_consist, loss_jepa, loss_jepa_neg, loss_msdn, loss_msdn_gate, loss_topo
```

当前结论：接口预检通过，Runner 已完成，raw artifacts 已进入 Warehouse，manifest/result 已回写。

## Artifact Check

- [x] `log:v1:module_trial:TRIAL-001:attempt-001` exists in Warehouse registry.
- [x] `checkpoint:v1:module_trial:TRIAL-001:attempt-001:best` exists in Warehouse registry.
- [x] `checkpoint:v1:module_trial:TRIAL-001:attempt-001:full` exists in Warehouse registry.
- [x] `receipt:v1:module_trial:TRIAL-001:attempt-001:runner_console` exists in Warehouse registry.
- [x] GitHub only records artifact ids, URIs, sha256, and size.

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

PASS_REVISE。

The trial is valid evidence but not a promotion candidate: H=73.72 is below the authoritative v1 baseline H=73.93.
