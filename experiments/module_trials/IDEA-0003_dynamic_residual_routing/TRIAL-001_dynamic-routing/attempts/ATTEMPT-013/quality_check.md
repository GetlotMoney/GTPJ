# ATTEMPT-013 Quality Check

## 当前结论

启动 gate 曾通过，但 owner 纠正复现定义后，本轮被标记为 `stopped_invalid_confirmation_scope`。
当前只登记已发生的服务器事实，不登记 confirmed、keep、best 或 promotion。

原因：ATTEMPT-013 是 `multi_seed_stability` / seed sweep，改变了 seed，没有保留
`original_seed`。严格复现必须写 `repeat_type: exact_repeat`、原配置、原 seed、
`max_attempts: 5`、`early_stop_on_best_hit: true`、`restore_target_H`，且只有达到目标后停止。
接近但未达到只能写 `near_miss_not_restored`，不能说还原。
本轮必须写 `not_confirmation_evidence: true`。

## 已检查

- `validate-agent-runtime` 通过，`agent_instance_mode` 为 `named_owner_thread`。
- `multi-agent-preflight` 通过，`formal_runner_allowed=true`，`formal_evidence_allowed=true`。
- frozen batch 已生成并上传到 `lab4090`。
- `plan.json` 包含 50 jobs，全部 `attempt_id=ATTEMPT-013`，`warehouse_attempt_id=ATTEMPT-013`。
- GPU0/GPU1 初始分配各 25 jobs。
- 服务器预检显示目标 run 目录启动前不存在、同 run id 无旧进程、GPU0/GPU1 空闲。
- 启动后确认两个 controller 进程存在，两个 `train_GTPJ_CUB.py` 训练进程进入 GPU。
- `summary.csv` 已收口为 44 completed / 6 skipped：DR047 seed 6-15、DR020 seed 6-15、DR041 seed 6-15、A011DR042 seed 6-15 已完整完成，A011DR020 只完成 seed 6/7/8/9。
- DR047 结果为 mean H=74.134，min H=73.89，max H=74.37，range H=0.48，暂未出现 H>=75。
- DR020 已完整完成 seed 6-15，mean H=74.131，暂未出现 H>=75。
- DR041 已完整完成 seed 6-15，mean H=74.127，min H=73.66，max H=74.53，range H=0.87，未出现 H>=75。
- A011DR042 已完整完成 seed 6-15，mean H=74.095，min H=73.80，max H=74.30，range H=0.50，未出现 H>=75。
- A011DR020 seed 6/7/8/9 mean H=73.973，未出现 H>=75；seed 10-15 因 `STOP_REQUESTED` skipped。
- 当前 best single 是 DR-028 H=74.53；没有 H>=75。

## 尚未检查

- 尚未检查 checkpoint、artifact hash、最终 `summary.csv/jsonl` 完整性。
- 尚未做完整 result analysis、promotion-facing quality review 或 post-run multi-agent result comparison。
- 不再补做 confirmation 判断；本轮不是 exact repeat，不能作为 confirmation evidence。

## Gate

- runner_start_allowed_by_current_instruction: superseded_by_owner_correction
- formal_result_evidence_exists: false_for_confirmation
- not_confirmation_evidence: true
- promotion_decision: blocked
