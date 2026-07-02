# Quality Check

```text
runtime:
decision: pending
promotion_decision: not_applicable
evidence_level: pending
confirmation_status: not_applicable
subject_id:
subject_type:
evidence_state:
transition_id:
```

## 范围

## 发现

## 质量检查

- [ ] 代码快照或 base version 明确。
- [ ] 配置副本保存在实验目录。
- [ ] 外部日志 artifact id、URI、sha256、size 和保留位置明确。
- [ ] 结果口径明确。
- [ ] `evidence_level`、`best_observed_H`、`confirmed_H` 和 `confirmation_status` 已区分。
- [ ] 没有未声明的 eval / class order / logits shape 改动。
- [ ] class order、seen/unseen split、label mapping、logits shape、metric calculation 未改变或已按高风险记录。
- [ ] GZSL hard rules 已记录到 `rule_checks`，失败硬门没有进入 advance/promote。
- [ ] `current_state` 能由 `TRANSITIONS.jsonl` 的 chain head 派生。
- [ ] `authority_refs` 指向现有 GitHub 轻量证据或合法 Warehouse/Research URI。
- [ ] 正式 Runner 启动前已有 `agent_runtime.yaml`，并通过 `validate-agent-runtime`。
- [ ] `activation_mode: real_multi_agent` 时已记录真实右侧临时 agent ids；没有用单窗口 Coordinator 冒充多 agents。
- [ ] Runner start 之前 Interface/Quality/Runner Monitor 至少给出 allow/pass；缺失时本轮降级为 debug/smoke 或 blocked。
- [ ] GitHub 目录没有新增 raw logs、checkpoint、generated figures 或 cache。
- [ ] checkpoint retention 已记录：默认最多保留 Top-3 checkpoint；logs、receipts、configs、summaries、manifests、registries 和 artifact id 不随 checkpoint 删除。

## Promotion Gate（仅正式提升 vX 时填写）

- [ ] parent_version / parent_tag 明确。
- [ ] trial tag 指向 README 中记录的 code_commit。
- [ ] baseline H、trial H、delta H 明确。
- [ ] `evidence_level: baseline_grade`；如果只是 owner 激活，已标为 provisional /
  owner_activated_unconfirmed。
- [ ] clean confirmation 或多 run 稳定性证据明确；单次最高 H 不直接 promotion。
- [ ] U/S/ZS、best epoch、seed 明确。
- [ ] 同 seed 对照明确；高风险改动已说明是否需要多 seed。
- [ ] trial config 和新版本 config 路径明确。
- [ ] 外部日志 artifact id、URI、sha256、size 和保留位置明确。
- [ ] class order、seen/unseen split、logits shape、metric calculation 未改变。
- [ ] input/output shape、loss、eval、checkpoint 变化已声明。
- [ ] switch off 能回到 parent_version 行为。
- [ ] VERSION、VERSION_TREE、EXPERIMENT_REGISTRY、PROJECT_STATUS、PROJECT_STRUCTURE、README 已更新。
- [ ] idea_tree current_version 和必要的 version_scores.vX 已更新。
- [ ] 新 baseline tag 准备打在包含正式版本代码和版本材料的明确 commit 上。
- [ ] main 当前代码只有 owner 明确执行 activate-version vX 时才切换；默认不切换。

promotion_decision 只能是：

```text
not_applicable
promote
blocked
rejected
```

## 必须修复项
