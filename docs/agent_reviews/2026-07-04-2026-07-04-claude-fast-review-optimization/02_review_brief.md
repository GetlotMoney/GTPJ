# Claude Code 快速审核 Brief

```text
task_id: claude-fast-review-optimization
task_title: Claude Code focused review optimization
scope: CLAUDE.md; docs/workflow/CLAUDE_CONTEXT.md; docs/workflow/protocols/ai_cross_review_protocol.md; experiments/templates/ai_cross_review_template.md; workflow/gtpj_workflow.py; tests/test_gtpj_workflow.py
risk_level: high
prompt_profile: focused
review_mode: blocking-only
machine_gates_passed: true
owner_participation: not_required
claude_code_read_only: true
```

## 默认读取顺序

- `CLAUDE.md`
- `docs/workflow/CLAUDE_CONTEXT.md`
- `00_task.md`
- `01_codex_actions.md`
- `02_focused_diff.md`
- `03_validation.md`
- `04_claims.md`

## 备用证据

- `02_diff.patch` 是完整 diff，只在 focused diff 无法定位问题时读取。
- 旧轮次的 Claude/Codex 文件只在第 2/3 轮需要比对剩余问题时读取。

## Changed Files

- `docs/workflow/protocols/ai_cross_review_protocol.md`
- `experiments/templates/ai_cross_review_template.md`
- `tests/test_gtpj_workflow.py`
- `workflow/gtpj_workflow.py`
- `CLAUDE.md`
- `docs/workflow/CLAUDE_CONTEXT.md`

## Validation Commands

- `python workflow\gtpj_workflow.py validate`
- `python workflow\gtpj_workflow.py validate-workflow-consistency`
- `python workflow\gtpj_workflow.py audit-boundary`
- `python -m py_compile workflow\gtpj_workflow.py`
- `python -m pytest tests/test_gtpj_workflow.py -q -p no:cacheprovider`
- `python workflow/gtpj_workflow.py validate-agent-runtime`
- `python workflow/gtpj_workflow.py validate-evidence-routing`
- `git diff --check`

## 审核要求

- 只读审核，不改文件，不启动训练，不 push，不删除用户数据。
- `blocking-only` 模式只报告会导致行为错误、证据污染、验证失败、正式实验结论不可靠的问题。
- 非阻断命名、风格、微小测试建议不要展开；可写 `non_blocking_issues: omitted_by_blocking_only_mode`。
