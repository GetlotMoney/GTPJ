task_id: CODE-REVIEW-20260709-HISTORICAL-REPEAT-GATE
task_title: 历史复现 source-control gate 最新补丁审核
scope: workflow/gtpj_workflow.py; tests/test_gtpj_workflow.py; formal dynamic-routing historical training commit gate; base config read from training commit
risk_level: high
validation_profile: custom-full-equivalent
owner_participation: not_required
review_required: true
review_tier: strict-3
claude_rounds_required: 3
review_reason: 正式复现入口和训练配置生成语义变化，必须阻断 A helper/B code/B config 混跑
acceptance_gates:
- machine_gates_passed: true
- codex_named_thread_pre_review: pass
- claude_rounds_required: 3
- unresolved_blocking_issues: 0
