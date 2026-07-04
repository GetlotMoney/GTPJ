task_id: claude-fast-review-optimization
task_title: Claude Code focused review optimization
scope: CLAUDE.md; docs/workflow/CLAUDE_CONTEXT.md; docs/workflow/protocols/ai_cross_review_protocol.md; experiments/templates/ai_cross_review_template.md; workflow/gtpj_workflow.py; tests/test_gtpj_workflow.py
risk_level: high
owner_participation: not_required
review_required: true
review_reason: important workflow/helper change that changes Claude Code review prompt inputs and review evidence pack generation
acceptance_gates:
- machine_gates_passed: true
- rounds_completed: 3
- unresolved_blocking_issues: 0
