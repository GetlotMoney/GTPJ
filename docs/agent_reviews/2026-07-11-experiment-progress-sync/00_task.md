task_id: EXP-SYNC-20260711
task_title: 同步实验进度与高分候选
scope: 同步 README、PROJECT_STATUS、Dynamic Routing trial 根摘要、模块索引、idea tree、queue_state 与 NEXT_ACTIONS；核对 ATTEMPT-004/011/014/015/016/017/018 的 75.11、75.04、75.02、75.00 与 74.8x/74.9x 候选；保持 confirmed reference=74.47、promotion blocked、队列日期一致和 checkpoint Top-3。
risk_level: high
validation_profile: default-core
owner_participation: not_required
review_required: true
review_tier: strict-3
claude_rounds_required: 3
review_reason: 本次修改会影响正式实验进度、best single、复现状态、队列动作和 GitHub 项目 claim，必须 strict-3。
acceptance_gates:
- machine_gates_passed: true
- codex_named_thread_pre_review: pass
- claude_rounds_required: 3
- unresolved_blocking_issues: 0
