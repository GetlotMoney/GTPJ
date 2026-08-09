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
- command: python -m pytest tests/test_gtpj_workflow.py -q -p no:cacheprovider
  exit_code: 0
  stdout: |
    ........................................................................ [ 73%]
    ..........................                                               [100%]
    98 passed in 30.32s
  stderr: |
    (empty)
- command: python workflow/gtpj_workflow.py validate-agent-runtime
  exit_code: 0
  stdout: |
    validate-agent-runtime-ok gates=3
  stderr: |
    (empty)
- command: python workflow/gtpj_workflow.py validate-evidence-routing
  exit_code: 0
  stdout: |
    validate-evidence-routing-ok subjects=5
  stderr: |
    (empty)
- command: git diff --check
  exit_code: 0
  stdout: |
    (empty)
  stderr: |
    (empty)
machine_gates_passed: true
failed_commands:
- none
