# Task Start Card: IDEA-0002 / TRIAL-002

task_id: TASK-20260628-idea0002-trial002
date: 2026-06-27
owner_request: Implement the FAE-memory JEPA idea, run training, and follow the full GTPJ workflow.

## Router

task_type: innovation / module trial
enters_idea_tree: yes
github_writes: idea_tree, experiments/module_trials, workflow-lightweight evidence
local_writes: GTPJ_Research idea notes, GTPJ_Warehouse run artifacts, .gtpj_runtime run status
coupled_update: required
coupled_order: Research idea context -> GitHub idea/trial ledger -> Warehouse raw run artifacts -> GitHub result ledger
required_protocols: WORKFLOW_ROUTER.md, TASK_START_CARD.md, idea_tree_protocol.md, module_trial_protocol.md, code_interface_contract.md, innovation_code_review_protocol.md, ARTIFACT_REGISTRATION.md, progress_dashboard.md

## Version

base_version: v2
base_code_tag: v2
current_branch: dev/v2-idea-0002-trial-002-strict-conditional-jepa
suggested_branch: dev/v2-idea-0002-trial-002-strict-conditional-jepa
pre_run_freeze_commit: pending
run_commit: pending
post_run_result_commit: pending

## Inputs

idea_id: IDEA-0002
source_type: user
source_status: local_heuristic
source_ref: owner:2026-06-27:move AG-JEPA visual context after FAE while keeping FAE-pre patch target
config: attempts/ATTEMPT-001/config.yaml
dataset: CUB
seed: 5

## Agents

activation_mode: real_multi_agent
activation_reason: Code changes alter auxiliary loss and forward auxiliary outputs.
decision_basis: GTPJ innovation code review protocol requires real_multi_agent for idea/module trial code changes.
required_roles: Coordinator, Reader/Planner, Implementer, Interface Checker, Runner, Log Analyst, Result Analyst, Quality Checker, Reviewer
required_real_agents: Reader/Planner, Interface Checker, Quality Checker, Reviewer
single_agent_allowed: false for formal review; Implementer remains the only writer.
tool_support: multi_agent_v1 available
serial: Implementer, Runner, Coordinator ledger writer
parallel: Reader/Planner, Interface Checker, Quality Checker, Reviewer, Log Analyst, Result Analyst when inputs are ready
writer_roles: Coordinator for ledger, Implementer for code, Runner for Warehouse/runtime only
reviewer_roles: Reader/Planner, Interface Checker, Quality Checker, Reviewer, Result Analyst

## Memory Policy

session_context_allowed: yes, orientation only
codex_memory_allowed: yes, orientation only
repo_state_required: yes
memory_used: yes
memory_sources: C:/Users/Administrator/.codex/memories/MEMORY.md, docs/workflow/agents/shared_roles/*/memory.md
verified_against_current_repo: workflow docs, idea_tree, model/MyModel.py, config/GTPJ_cub_gzsl.yaml, train_GTPJ_CUB.py

## Hard Gates

interface_contract: required
innovation_code_review: Review 0-3 required
source_status: local_heuristic accepted by Review 0
artifact_boundary: raw logs/checkpoints to GTPJ_Warehouse only
metric_semantics: must remain GZSL U/S/H/ZS with unchanged evaluator
evidence_level: ATTEMPT-001 target is valid_single_run if complete
confirmation_grade: not targeted by ATTEMPT-001
promotion_gate: not triggered unless future evidence reaches baseline_grade

## Expected Outputs

github: trial README, implementation.md, code.diff, idea_intent_check.md, interface_precheck.md, review_round_1.md, interface_check.md, quality_check.md, ATTEMPTS.md, attempts/ATTEMPT-001/*
research: D:/backup/Documents/Myself/GTPJ_Research/ideas/IDEA-0002_fae_memory_jepa/idea_full.md
warehouse: run log, best checkpoint, full checkpoint, runner receipt
sync_check: GitHub records must point back to Research and Warehouse artifacts by path/URI/hash/size.

## Stop If

- Review 1 or Review 2 has unresolved blocking issues.
- `jepa_context_mode` lacks a baseline-off path.
- selected patch, mask, target, and context alignment is unclear.
- positive JEPA gradient does not reach `cross_tf.fae.*`.
- label mapping, seen/unseen split, class order, logits shape, or metric semantics change.
- worktree is dirty at Runner start.
- GPU lock is unavailable.
