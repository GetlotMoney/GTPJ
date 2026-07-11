# Claude Code 快速审核 Brief

```text
task_id: EXP-SYNC-20260711
task_title: 同步实验进度与高分候选
scope: 同步 README、PROJECT_STATUS、Dynamic Routing trial 根摘要、模块索引、idea tree、queue_state 与 NEXT_ACTIONS；核对 ATTEMPT-004/011/014/015/016/017/018 的 75.11、75.04、75.02、75.00 与 74.8x/74.9x 候选；保持 confirmed reference=74.47、promotion blocked、队列日期一致和 checkpoint Top-3。
risk_level: high
validation_profile: default-core
prompt_profile: full
review_mode: full
review_tier: strict-3
claude_rounds_required: 3
machine_gates_passed: true
owner_participation: not_required
claude_code_read_only: true
```

## 默认读取顺序

- `CLAUDE.md`
- `docs/workflow/CLAUDE_CONTEXT.md`
- `00_task.md`
- `01_codex_actions.md`
- `02_codex_named_thread_pre_review.md`
- `02_review_brief.md`
- `02_focused_diff.md`
- `03_validation.md`
- `04_claims.md`

## 备用证据

- `02_diff.patch` 是完整 diff，只在 focused diff 无法定位问题时读取。
- 旧轮次的 Claude/Codex 文件只在第 2/3 轮需要比对剩余问题时读取。

## Changed Files

- `NEXT_ACTIONS.md`
- `README.md`
- `docs/PROJECT_STATUS.md`
- `experiments/README.md`
- `experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/README.md`
- `experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/quality_check.md`
- `experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/result.md`
- `experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/result.yaml`
- `experiments/module_trials/INDEX.md`
- `idea_tree/idea_tree.json`
- `idea_tree/ideas/IDEA-0003_dynamic_residual_routing/IDEA.md`
- `idea_tree/queues/queue_state.yaml`
- `idea_tree/versions/v5.md`
- `workflow/README.md`

## Validation Commands

- `python workflow\gtpj_workflow.py validate`
- `python workflow\gtpj_workflow.py validate-workflow-consistency`
- `python workflow\gtpj_workflow.py audit-boundary`
- `python -m py_compile workflow\gtpj_workflow.py`
- `python -m pytest -q`

## 审核要求

- 只读审核，不改文件，不启动训练，不 push，不删除用户数据。
- `blocking-only` 模式只报告会导致行为错误、证据污染、验证失败、正式实验结论不可靠的问题。
- 非阻断命名、风格、微小测试建议不要展开；可写 `non_blocking_issues: omitted_by_blocking_only_mode`。
