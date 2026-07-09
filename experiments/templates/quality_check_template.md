# Quality Check（质量检查）

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
- [ ] 标准 GZSL 数据集、split、class order、label mapping、U/S/H/ZS 语义未被模板实现改变。
- [ ] `module_source.md` 记录了 paper/source、template family、attachment point 和 baseline-off 解释。
- [ ] `trial_meta.yaml` 已通过 `validate-trial-meta`，`module_scope` 与 `affects` 没有非法组合。
- [ ] 训练入口已对照 `standard_gzsl_training_template.py`，并记录 config、seed、dataset/split、eval function、checkpoint policy 和 artifact refs。
- [ ] 如果 `training_entry_mode: strict_template_entry`，Runner 使用 trial-local training entry，旧入口中已打开模块已迁移。
- [ ] 如果 `module_scope: composite`，每个 component 的 template family、attachment point、enabled key、composition mode 和 all-off baseline path 已记录。
- [ ] GZSL hard rules 已记录到 `rule_checks`，失败硬门没有进入 advance/promote。
- [ ] `current_state` 能由 `TRANSITIONS.jsonl` 的 chain head 派生。
- [ ] `authority_refs` 指向现有 GitHub 轻量证据或合法 Warehouse/Research URI。
- [ ] 正式 Runner 启动前已有 `agent_runtime.yaml`，并通过 `validate-agent-runtime` 和 `multi-agent-preflight`。
- [ ] `formal_runner_allowed: true` 和 `formal_evidence_allowed: true` 有真实 agent 输出支撑。
- [ ] `agent_status_refs` 和 `agent_output_refs` 指向可读取、非空、能关联 role / agent id 的文件。
- [ ] `activation_mode: real_multi_agent` 时已记录真实左侧命名 Codex 线程 ids；没有用单窗口 Coordinator 冒充多 agents。
- [ ] 阶段结束前已运行 `agent-cleanup-plan`，completed threads 的归档结果已写入 `archived_threads_record`。
- [ ] 未发现一个 agent id 同时承担多个正式独立角色；如存在，已标记为历史限制或降级证据。
- [ ] Runner start 之前 Interface/Quality/Runner Monitor 至少给出 allow/pass；缺失时本轮降级为 debug/smoke 或 blocked。
- [ ] GitHub 目录没有新增 raw logs、checkpoint、generated figures 或 cache。
- [ ] checkpoint retention 已记录：默认最多保留 Top-3 checkpoint；logs、receipts、configs、summaries、manifests、registries 和 artifact id 不随 checkpoint 删除。

## AI 交叉审核

- [ ] 重要代码、workflow/helper/template、训练入口、评估语义、实验结论或 promotion 相关改动已按 `review_tier` 创建分层 AI 交叉审核包。
- [ ] Claude Code 审核保持只读，Codex 的修复、rebuttal 和重跑验证已记录。
- [ ] 已运行 `validate-ai-cross-review --path <review_pack>`，且 `unresolved_blocking_issues: 0`。
- [ ] 若审核包 blocked，本轮未进入正式 Runner、keep/best、confirmation、promotion、baseline 或 paper claim。

## Promotion Gate（升版门槛，仅正式提升 vX 时填写）

- [ ] parent_version / parent_tag 明确。
- [ ] trial tag 指向 README 中记录的 code_commit。
- [ ] baseline H、trial H、delta H 明确。
- [ ] `evidence_level: baseline_grade`；如果只是 owner 激活，已标为 provisional /
  owner_activated_unconfirmed。
- [ ] 复现任务写明 `repeat_type: exact_repeat`、`original_seed`、`max_attempts: 5`、
      `max_attempts_hard_cap: true`、`early_stop_on_best_hit: true`、`restore_target_H`、`near_miss_tolerance_H`、
      `near_miss_not_restored`，且未改 seed 或任何参数。
- [ ] 同一候选无论是否还原成功都没有超过 5 次 exact repeat；5 次未达目标时已停止并记录 not restored / near miss。
- [ ] 接近但未达到 `restore_target_H` 的结果只写为 `near_miss_not_restored`；
      不能写成还原，不能触发 early stop。
- [ ] `seed_sweep`、`score_search` 或 `multi_seed_stability` 已写 `not_confirmation_evidence: true`，
      没有冒充复现或 confirmed evidence。
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
