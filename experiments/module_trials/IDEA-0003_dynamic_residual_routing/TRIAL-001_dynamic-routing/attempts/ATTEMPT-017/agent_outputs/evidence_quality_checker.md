# Evidence Quality Checker

role_key: evidence_quality_checker
execution_mode: role_only
formal_runtime_backend: server_detached_role_only
decision: allow

files_reviewed:
- task_start_card.md
- pre_run_plan.md
- WORK_ITEMS.md
- attempts/ATTEMPT-015/result.yaml
- attempts/ATTEMPT-015/quality_check.md
- attempts/ATTEMPT-016/manifest.yaml
- tests/test_gtpj_workflow.py

summary: ATTEMPT-017 是 tune_search + narrow_ablation，不是 confirmation。任何 H>=75 都只能作为 best single/tune promising；不能写成 restored、confirmed 或 promotion evidence。ATTEMPT-016 当前只作为 GPU 占用和运行顺序约束，不能作为 ATTEMPT-017 的完成结论。
