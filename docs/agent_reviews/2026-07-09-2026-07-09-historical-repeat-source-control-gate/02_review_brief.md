# Claude Code 快速审核 Brief

```text
task_id: CODE-REVIEW-20260709-HISTORICAL-REPEAT-GATE
task_title: 历史复现 source-control gate 最新补丁审核
scope: workflow/gtpj_workflow.py; tests/test_gtpj_workflow.py; formal dynamic-routing historical training commit gate; base config read from training commit
risk_level: high
validation_profile: custom-full-equivalent
prompt_profile: focused
review_mode: blocking-only
review_tier: strict-3
claude_rounds_required: 3
machine_gates_passed: true
owner_participation: not_required
claude_code_read_only: true
```

## 默认读取顺序

- `CLAUDE.md`
- `docs/workflow/CLAUDE_CONTEXT.md`
- `00_task.md`
- `01_codex_actions.md`
- `02_codex_named_thread_pre_review.md`
- `02_review_brief.md`
- `02_focused_diff.md`
- `03_validation.md`
- `04_claims.md`

## 备用证据

- `02_diff.patch` 是完整 diff，只在 focused diff 无法定位问题时读取。
- 旧轮次的 Claude/Codex 文件只在第 2/3 轮需要比对剩余问题时读取。

## Changed Files

- `AGENTS.md`
- `docs/workflow/CLAUDE_CONTEXT.md`
- `docs/workflow/README.md`
- `docs/workflow/START_HERE.md`
- `docs/workflow/WORKFLOW_KERNEL.md`
- `docs/workflow/agents/README.md`
- `docs/workflow/agents/by_experiment/ablation/agents/README.md`
- `docs/workflow/agents/by_experiment/confirmation/agents/README.md`
- `docs/workflow/agents/by_experiment/innovation/agents/README.md`
- `docs/workflow/agents/by_experiment/promotion/agents/README.md`
- `docs/workflow/agents/by_experiment/tune/agents/README.md`
- `docs/workflow/agents/long_term_memory.md`
- `docs/workflow/core/AGENT_RUNTIME_HARD_GATE.md`
- `docs/workflow/core/CHANGELOG.md`
- `docs/workflow/core/QUICK_START.md`
- `docs/workflow/core/TASK_START_CARD.md`
- `docs/workflow/core/TASK_START_MINI.md`
- `docs/workflow/core/WORKFLOW_ROUTER.md`
- `docs/workflow/core/WORKFLOW_VERSION.md`
- `docs/workflow/playbooks/ablation.md`
- `docs/workflow/playbooks/confirmation.md`
- `docs/workflow/playbooks/innovation.md`
- `docs/workflow/playbooks/mixed_campaign.md`
- `docs/workflow/playbooks/paper_to_experiment.md`
- `docs/workflow/playbooks/tune.md`
- `docs/workflow/protocols/agent_cleanup_protocol.md`
- `docs/workflow/protocols/agent_orchestration.md`
- `docs/workflow/protocols/agent_report_policy.md`
- `docs/workflow/protocols/ai_cross_review_protocol.md`
- `docs/workflow/protocols/autonomous_research_campaign.md`
- `docs/workflow/protocols/experiment_protocol.md`
- `docs/workflow/protocols/innovation_code_review_protocol.md`
- `docs/workflow/protocols/mixed_experiment_campaign_protocol.md`
- `docs/workflow/protocols/module_template_selection.md`
- `docs/workflow/protocols/module_trial_protocol.md`
- `docs/workflow/protocols/promotion.md`
- `experiments/README.md`
- `experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/ATTEMPTS.md`
- `experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/README.md`
- `experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/agent_summary.md`
- `experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/manifest.yaml`
- `experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/quality_check.md`
- `experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/result.md`
- `experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/result.yaml`
- `experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/review_round_2.md`
- `experiments/module_trials/INDEX.md`
- `experiments/templates/TRIAL_ATTEMPTS_template.md`
- `experiments/templates/TRIAL_README_template.md`
- `experiments/templates/VERSION_template.md`
- `experiments/templates/agent_summary_template.md`
- `experiments/templates/ai_cross_review_template.md`
- `experiments/templates/implementation_template.md`
- `experiments/templates/modules/README.md`
- `experiments/templates/modules/architecture_change_template.md`
- `experiments/templates/modules/auxiliary_loss_template.py`
- `experiments/templates/modules/composite_module_template.py`
- `experiments/templates/modules/feature_adapter_template.py`
- `experiments/templates/modules/fusion_gate_template.py`
- `experiments/templates/modules/module_source_template.md`
- `experiments/templates/modules/standard_gzsl_module_framework_template.py`
- `experiments/templates/modules/standard_gzsl_training_template.py`
- `experiments/templates/modules/standard_trial_config_template.yaml`
- `experiments/templates/quality_check_template.md`
- `experiments/templates/run_receipt_template.yaml`
- `idea_tree/INDEX.md`
- `idea_tree/idea_tree.json`
- `tests/test_gtpj_workflow.py`
- `workflow/gtpj_workflow.py`
- `docs/workflow/reference/GENERAL_GZSL_EXPERIMENT_PROTOCOL.md`
- `experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/attempts/ATTEMPT-010/`
- `experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/attempts/ATTEMPT-011/`
- `experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/attempts/ATTEMPT-012/`
- `experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/attempts/ATTEMPT-013/`
- `experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/attempts/ATTEMPT-014/`
- `experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/attempts/ATTEMPT-015/`
- `experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/attempts/ATTEMPT-016/`
- `experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/attempts/ATTEMPT-017/`
- `experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/attempts/ATTEMPT-018/`
- `scripts/`

## Validation Commands

- `python workflow\gtpj_workflow.py validate`
- `python workflow\gtpj_workflow.py validate-workflow-consistency`
- `python workflow\gtpj_workflow.py audit-boundary`
- `python -m py_compile workflow\gtpj_workflow.py`
- `python -m pytest -q tests/test_gtpj_workflow.py`
- `python workflow/gtpj_workflow.py validate`
- `python workflow/gtpj_workflow.py validate-workflow-consistency`
- `python workflow/gtpj_workflow.py audit-boundary`
- `git diff --check`

## 审核要求

- 只读审核，不改文件，不启动训练，不 push，不删除用户数据。
- `blocking-only` 模式只报告会导致行为错误、证据污染、验证失败、正式实验结论不可靠的问题。
- 非阻断命名、风格、微小测试建议不要展开；可写 `non_blocking_issues: omitted_by_blocking_only_mode`。
