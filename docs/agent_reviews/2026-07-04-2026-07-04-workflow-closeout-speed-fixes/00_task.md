task_id: workflow-closeout-speed-fixes
task_title: workflow closeout speed fixes
scope: workflow/gtpj_workflow.py; tests/test_gtpj_workflow.py
risk_level: high
owner_participation: not_required
review_required: true
review_reason: important workflow/helper change for formal experiment closeout, warehouse routing, and confirmation semantics
acceptance_gates:
- machine_gates_passed: true
- rounds_completed: 3
- unresolved_blocking_issues: 0
