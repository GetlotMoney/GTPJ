# Task Start Card: IDEA-0003 / TRIAL-001

task_id: TASK-20260630-idea0003-trial001
date: 2026-06-30
owner_request: Implement dynamic residual routing and prepare a 50-run two-GPU server batch.

## Router

task_type: innovation / module trial
enters_idea_tree: yes
github_writes: idea_tree, experiments/module_trials, tests, model, workflow lightweight evidence
local_writes: .gtpj_runtime batch plan and status
server_writes: lab4090 worktrees, runtime logs, checkpoints, Warehouse artifacts
coupled_update: required
required_protocols: TASK_START_CARD.md, idea_tree_protocol.md, module_trial_protocol.md, code_interface_contract.md, innovation_code_review_protocol.md, artifact boundary

## Version

base_version: v5
base_code_tag: v5
current_branch: dev/v5-idea-0003-trial-001-dynamic-routing
suggested_branch: dev/v5-idea-0003-trial-001-dynamic-routing
pre_run_freeze_commit: pending
run_commit: pending
post_run_result_commit: pending

## Inputs

idea_id: IDEA-0003
trial_id: TRIAL-001
source_type: user
source_status: local_heuristic
source_ref: owner:2026-06-30:make residual and mixture coefficients dynamic routes
config: config.yaml plus generated batch configs
dataset: CUB
seed: 5

## Agents

activation_mode: real_multi_agent
activation_reason: Dynamic gates alter the model forward path, score mixing, conditional text path, and training logs.
required_roles: Coordinator, Implementer, Interface Checker, Quality Checker, Runner, Result Analyst
required_real_agents: Interface Checker, Quality Checker, Result Analyst
single_agent_allowed: false for formal pre-run review
tool_support: multi_agent_v1 available
writer_roles: Coordinator for ledger, Implementer for code, Runner for server runtime only
reviewer_roles: Interface Checker, Quality Checker, Result Analyst
agent_profile_files: docs/workflow/agents/shared_roles/*/profile.md
agent_memory_files: docs/workflow/agents/shared_roles/*/memory.md

## Memory Policy

session_context_allowed: yes, orientation only
codex_memory_allowed: yes, orientation only
repo_state_required: yes
verified_against_current_repo: idea_tree, model/MyModel.py, train_GTPJ_CUB.py, workflow/gtpj_workflow.py, config/versions/v5.yaml

## Hard Gates

interface_contract: class order, seen/unseen split, logits shape, and metric semantics must stay unchanged
switch_off: use_dynamic_routing=false must preserve v5 behavior
innovation_code_review: Review 0-3 required
artifact_boundary: raw logs/checkpoints stay outside GitHub
pre_run_freeze_commit: required before server batch starts
promotion_gate: not triggered in this trial branch

## Expected Outputs

github: IDEA/TRIAL ledger, implementation.md, interface_precheck.md, review files, tests, workflow helper, model code
runtime: .gtpj_runtime/batches/RUN-*-dynroute50-2gpu
warehouse: server-side logs/checkpoints/receipts after runs complete
analysis: best single, top2 repeat mean, U/S stability, failure summary

## Stop If

- all_text_cond no longer enters BVSA when bvsa_text_mode=conditional.
- logits shape changes from train [B, n_seen] or eval [B, num_class].
- class order, seen/unseen split, label mapping, or evaluator changes.
- Review 2 reports a blocking issue.
- worktree is dirty at Runner start except ignored runtime files.
- server is not on the pushed experiment commit.
