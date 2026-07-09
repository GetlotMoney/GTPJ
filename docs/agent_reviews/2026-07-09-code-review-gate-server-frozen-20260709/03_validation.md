validation_profile: default-core
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
machine_gates_passed: true
failed_commands:
- none
