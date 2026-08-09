task_id: workflow-code-template-review
task_title: 审核 workflow 代码和模板改动
scope: current git diff
risk_level: high
owner_participation: not_required
review_required: true
review_reason: 用户要求用 Claude Code 与 Codex 三轮交叉审核 workflow 代码、模板和规范改动。
acceptance_gates:
- machine_gates_passed: true
- rounds_completed: 3
- unresolved_blocking_issues: 0
