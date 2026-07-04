# AI 交叉审核证据包模板

## 00_task.md

```text
task_id:
task_title:
scope:
risk_level: low | medium | high
validation_profile: default-core | custom-debug | custom-full-equivalent
owner_participation: not_required
review_required: true
review_tier: fast | review-1 | strict-3
claude_rounds_required: 0 | 1 | 3
review_reason:
acceptance_gates:
- machine_gates_passed: true
- codex_temp_agent_pre_review: pass
- claude_rounds_required:
- unresolved_blocking_issues: 0
```

## 01_codex_actions.md

```text
codex_role: implementer
changed_files:
intended_behavior:
out_of_scope:
risk_notes:
```

## 02_diff.patch

```text
填写 git diff 或 git diff --cached 输出。
```

## 02_codex_temp_agent_pre_review.md

```text
codex_temp_agent_pre_review: pass | blocked
temporary_agent_required: true
agent_instance_id:
ui_display_name:
lifecycle: completed_closed
closed_before_claude: true
close_result_confirms_completion: true
close_result:
verdict: pass | needs_fix | blocked
blocking_issues:
notes:
```

## 02_focused_diff.md

```text
prompt_profile: focused
完整 diff 保留在 02_diff.patch；Claude Code 默认读取本文件。
```

## 02_review_brief.md

```text
prompt_profile: focused | full
review_mode: blocking-only | full
review_tier: fast | review-1 | strict-3
claude_rounds_required: 0 | 1 | 3
validation_profile: default-core | custom-debug | custom-full-equivalent
changed_files:
machine_gates_passed:
default_inputs:
```

## 03_validation.md

```text
commands_run:
machine_gates_passed: true | false
failed_commands:
not_run:
reason_if_not_run:
```

## 04_claims.md

```text
claim:
status: verified | supported | assumption | unproven | false
evidence_ref:
```

## 05_claude_review_round_1.md

```text
round: 1
reviewer: claude_code
claude_code_read_only: true
inputs_checked:
verdict: pass | needs_fix | blocked
blocking_issues:
non_blocking_issues:
unsupported_claims:
missing_validation:
```

## 06_codex_response_round_1.md

```text
round: 1
reviewer: codex
addressed_claude_findings:
fixes_applied:
rejected_findings_with_evidence:
validation_rerun:
remaining_blocking_issues:
```

## 07_claude_review_round_2.md

```text
round: 2
reviewer: claude_code
claude_code_read_only: true
inputs_checked:
verdict: pass | needs_fix | blocked
blocking_issues:
non_blocking_issues:
unsupported_claims:
missing_validation:
```

## 08_codex_response_round_2.md

```text
round: 2
reviewer: codex
addressed_claude_findings:
fixes_applied:
rejected_findings_with_evidence:
validation_rerun:
remaining_blocking_issues:
```

## 09_claude_review_round_3.md

```text
round: 3
reviewer: claude_code
claude_code_read_only: true
inputs_checked:
verdict: pass | needs_fix | blocked
blocking_issues:
non_blocking_issues:
unsupported_claims:
missing_validation:
```

## 10_final_decision.md

```text
ai_cross_review_status: pass | blocked
owner_participation: not_required
review_tier: fast | review-1 | strict-3
rounds_completed: 0 | 1 | 3
claude_rounds_required: 0 | 1 | 3
claude_rounds_completed: 0 | 1 | 3
claude_code_read_only: true
codex_temp_agent_pre_review: pass
codex_temp_agent_lifecycle: completed_closed
codex_fixes_or_rebuttals_recorded: true
machine_gates_passed: true | false
unresolved_blocking_issues: 0
accepted_by: machine_gates_plus_ai_cross_review
blocked_reason:
```
