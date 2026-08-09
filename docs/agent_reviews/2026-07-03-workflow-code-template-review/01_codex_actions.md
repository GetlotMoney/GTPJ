codex_role: implementer
changed_files:
- AGENTS.md
- docs/workflow/START_HERE.md
- docs/workflow/WORKFLOW_KERNEL.md
- docs/workflow/WORKFLOW_MANIFEST.yaml
- docs/workflow/protocols/agent_report_policy.md
- docs/workflow/protocols/innovation_code_review_protocol.md
- docs/workflow/protocols/module_trial_protocol.md
- experiments/templates/TRIAL_README_template.md
- experiments/templates/agent_summary_template.md
- experiments/templates/quality_check_template.md
- tests/test_gtpj_workflow.py
- workflow/gtpj_workflow.py
- docs/workflow/protocols/ai_cross_review_protocol.md
- experiments/templates/ai_cross_review_template.md
intended_behavior: 审核 workflow 代码和模板改动
out_of_scope:
- 不启动训练
- 不启动子 agents
- 不 push
- 不删除用户数据
risk_notes: 由 AI 交叉审核和机器验证共同控制风险。
