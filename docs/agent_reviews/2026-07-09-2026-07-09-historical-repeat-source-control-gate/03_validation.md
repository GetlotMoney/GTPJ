validation_profile: custom-full-equivalent
commands_run:
- command: python workflow\gtpj_workflow.py validate
  exit_code: 0
  stdout: |
    validate-ok
  stderr: |
    (empty)
- command: python workflow\gtpj_workflow.py validate-workflow-consistency
  exit_code: 0
  stdout: |
    validate-workflow-consistency-ok
  stderr: |
    (empty)
- command: python workflow\gtpj_workflow.py audit-boundary
  exit_code: 0
  stdout: |
    audit-boundary-ok
  stderr: |
    (empty)
- command: python -m py_compile workflow\gtpj_workflow.py
  exit_code: 0
  stdout: |
    (empty)
  stderr: |
    (empty)
- command: python -m pytest -q tests/test_gtpj_workflow.py
  exit_code: 0
  stdout: |
    ........................................................................ [ 44%]
    ........................................................................ [ 88%]
    ...................                                                      [100%]
    163 passed in 67.33s (0:01:07)
  stderr: |
    (empty)
- command: python workflow/gtpj_workflow.py validate
  exit_code: 0
  stdout: |
    validate-ok
  stderr: |
    (empty)
- command: python workflow/gtpj_workflow.py validate-workflow-consistency
  exit_code: 0
  stdout: |
    validate-workflow-consistency-ok
  stderr: |
    (empty)
- command: python workflow/gtpj_workflow.py audit-boundary
  exit_code: 0
  stdout: |
    audit-boundary-ok
  stderr: |
    (empty)
- command: git diff --check
  exit_code: 0
  stdout: |
    (empty)
  stderr: |
    warning: in the working copy of 'experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/README.md', CRLF will be replaced by LF the next time Git touches it
    warning: in the working copy of 'experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/agent_summary.md', CRLF will be replaced by LF the next time Git touches it
    warning: in the working copy of 'experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/manifest.yaml', CRLF will be replaced by LF the next time Git touches it
    warning: in the working copy of 'experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/quality_check.md', CRLF will be replaced by LF the next time Git touches it
    warning: in the working copy of 'experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/result.md', CRLF will be replaced by LF the next time Git touches it
    warning: in the working copy of 'experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/result.yaml', CRLF will be replaced by LF the next time Git touches it
    warning: in the working copy of 'experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/review_round_2.md', CRLF will be replaced by LF the next time Git touches it
    warning: in the working copy of 'experiments/module_trials/INDEX.md', CRLF will be replaced by LF the next time Git touches it
    warning: in the working copy of 'idea_tree/INDEX.md', CRLF will be replaced by LF the next time Git touches it
    warning: in the working copy of 'idea_tree/idea_tree.json', CRLF will be replaced by LF the next time Git touches it
machine_gates_passed: true
failed_commands:
- none
