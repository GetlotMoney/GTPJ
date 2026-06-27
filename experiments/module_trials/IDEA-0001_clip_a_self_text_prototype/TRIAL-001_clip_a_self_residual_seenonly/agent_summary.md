# Agent Summary

```text
experiment_id: TRIAL-001
run_id: RUN-20260626-ATTEMPT-002..006-head-sweep
base_version: v1
code_branch: dev/v1-idea-0001-trial-001-clip-a-self-residual-seenonly
code_commit: da2e295cb15b0d55afdcf4785bce4bc6a4bff80e
activation_mode: role_only
activation_reason: ATTEMPT-002..006 were executed as a single serial head/dropout/ratio sweep before the real-multi-agent activation rule was formalized; results are kept as revise evidence only.
required_roles: Coordinator, Reader/Planner, Runner, Result Analyst, Quality Checker, Reviewer
required_real_agents: []
agent_set: Coordinator, Reader/Planner, Runner, Quality Checker, Result Analyst, Reviewer
serial_agents: Coordinator -> Runner
parallel_agents: Reader/Planner + Quality Checker
disabled_agents: Implementer, Interface Checker (no post-implementation code change during this sweep)
tool_support: real_multi_agent_available=not_checked_for_this_historical_sweep; fallback_mode=role_only; checked_by=Coordinator
memory_policy: repo_state_required=yes; memory_used=no; memory_sources=[]; verified_against_current_repo=README.md, ATTEMPTS.md, manifest.yaml, result.yaml, quality_check.md
memory_used: no
memory_sources: []
verified_against_current_repo: README.md, ATTEMPTS.md, manifest.yaml, result.yaml, quality_check.md
runtime_state:
warehouse_report_artifacts: log:v1:module_trial:TRIAL-001:attempt-002, log:v1:module_trial:TRIAL-001:attempt-003, log:v1:module_trial:TRIAL-001:attempt-004, log:v1:module_trial:TRIAL-001:attempt-005, log:v1:module_trial:TRIAL-001:attempt-006, log:v1:module_trial:TRIAL-001:attempt-007, log:v1:module_trial:TRIAL-001:attempt-008
final_decision: revise; ATTEMPT-003 is historical high, but clean confirmations ATTEMPT-007 and ATTEMPT-008 did not reproduce it
```

## ATTEMPT-007 Confirmation Addendum

```text
run_id: RUN-20260626-225103-module-trial-attempt-007
attempt_id: ATTEMPT-007
pre_run_freeze_commit: 2820b17c222bd2084292d5249d429dce95d1e060
activation_mode: role_only
activation_reason: clean confirmation rerun with no code, interface, loss, eval, split, class order, label mapping, or logits-shape change
required_roles: Coordinator, Runner, Log Analyst, Quality Checker, Result Analyst
required_real_agents: []
tool_support: real_multi_agent_available=not_required_for_clean_confirmation; fallback_mode=role_only
memory_used: yes
memory_sources: C:/Users/Administrator/.codex/memories/MEMORY.md
verified_against_current_repo: WORKFLOW_ROUTER.md, module_trial_protocol.md, ATTEMPTS.md, config.yaml, manifest.yaml, result.yaml, quality_check.md
result: ATTEMPT-007 H=73.69 did not confirm ATTEMPT-003 H=74.27
final_decision: revise; promotion remains blocked
```

## ATTEMPT-008 Confirmation Addendum

```text
run_id: RUN-20260626-231504-module-trial-attempt-008
attempt_id: ATTEMPT-008
pre_run_freeze_commit: 8b6acac45b83cca1a255d00782d4eba7a272c4fb
activation_mode: real_quality_checker_plus_main_runner
activation_reason: disputed anomalous result and user concern about parameter pollution required independent read-only review
required_roles: Coordinator, Runner, Log Analyst, Quality Checker, Result Analyst
required_real_agents: Quality Checker
real_agents: Quality Checker=019f047d-13f1-7b81-820e-ef7fc34fcfc7(Banach)
tool_support: real_multi_agent_available=yes; quality_checker_completed=yes
memory_used: yes
memory_sources: C:/Users/Administrator/.codex/memories/MEMORY.md
verified_against_current_repo: WORKFLOW_ROUTER.md, module_trial_protocol.md, ATTEMPTS.md, config.yaml, manifest.yaml, result.yaml, quality_check.md
result: ATTEMPT-008 H=73.88 did not confirm ATTEMPT-003 H=74.27; it is +0.19 above ATTEMPT-007 but -0.05 below v1
quality_checker_conclusion: no evidence of config, training-code, resume/checkpoint, or artifact pollution; ATTEMPT-003 remains non-promotion-grade because it was dirty and not reproduced by clean confirmations
final_decision: revise; promotion remains blocked
```

## ATTEMPT-009..020 Formal Best Addendum

```text
run_id: RUN-20260626-235934-trial001-009-028
attempt_range: ATTEMPT-009..020 completed; ATTEMPT-021 startup failed before epochs
best_attempt_id: ATTEMPT-019
best_attempt_record_commit: 3a7945a
attempt_git_tag_policy: not_used_for_trial_internal_attempts
pre_run_freeze_commit: 453acc0
activation_mode: role_only
activation_reason: frozen trial-internal parameter sweep with no code, loss, eval, split, class order, label mapping, or logits-shape change
required_roles: Coordinator, Runner, Log Analyst, Quality Checker, Result Analyst
required_real_agents: []
tool_support: real_multi_agent_available=not_required_for frozen serial runner; fallback_mode=role_only
memory_used: yes
memory_sources: C:/Users/Administrator/.codex/memories/MEMORY.md
verified_against_current_repo: ATTEMPTS.md, attempts/ATTEMPT-009..020/result.yaml, manifest.yaml, result.yaml, quality_check.md
result: ATTEMPT-019 U=71.32 S=77.52 H=74.29 ZS=81.59 best_epoch=33
quality_conclusion: formal best recorded, but seen-heavy and not promotion-grade without clean confirmation
final_decision: revise; promotion remains blocked
```

## Promotion To GTPJ-v2 Addendum

```text
promotion_date: 2026-06-27
target_version: v2
owner_request: make the current best experiment formal and turn it into the mainline
source_attempt: ATTEMPT-019
source_trial_run_commit: 453acc0
source_attempt_record_commit: 3a7945a
metrics: U=71.32 S=77.52 H=74.29 ZS=81.59 best_epoch=33
baseline: GTPJ-v1 H=73.93
delta_H: +0.36
activation_mode: real_multi_agent_required_by_policy_but_role_only_with_available_evidence
activation_reason: promotion and active mainline decision affect baseline selection
required_roles: Coordinator, Interface Checker, Quality Checker, Result Analyst, Reviewer
required_real_agents: []
tool_support: real_multi_agent_available=limited_in_current_turn; fallback_mode=role_only_with_independent_sequential_review
memory_used: yes
memory_sources: C:/Users/Administrator/.codex/memories/MEMORY.md
verified_against_current_repo: README.md, result.yaml, manifest.yaml, quality_check.md, attempts/ATTEMPT-019/result.yaml, attempts/ATTEMPT-019/manifest.yaml
decision: promote_to_v2_and_activate_mainline_by_owner
known_risks: clean confirmation missing; seen-heavy S-U=6.20
follow_up: run v2 confirmation and U/S gap analysis before manuscript-grade claims
```

## Coordinator

```text
role: workflow coordinator
agent_instance_type: main_agent
independence_scope: routing, run sequencing, artifact registration, ledger updates
inputs_checked: current trial ledger, attempt queue, branch cleanliness before sweep, Runner lock discipline
actions: created ATTEMPT-002..006 configs, fixed the conda Unicode wrapper issue, ran five serial sweeps, copied artifacts to Warehouse, updated trial ledgers
outputs: ATTEMPTS.md, per-attempt manifests/results, updated root trial summary
issues: the sweep was executed before the new attempt configs were committed, so the worktree was dirty during the runs
decision: keep ATTEMPT-003 as the leading setting
evidence_refs: README.md, ATTEMPTS.md, result.yaml
memory_used: no
memory_sources: []
verified_against_current_repo: README.md, ATTEMPTS.md, result.yaml
```

## Reader/Planner

```text
role: experiment planner
agent_instance_type: role_checklist
independence_scope: parameter plan only
inputs_checked: ATTEMPT-001 result, baseline H=73.93, confirmation H=73.77, parameter roles for heads/dropout/ratios
actions: planned the five-attempt sequence and ranked the candidate knobs by expected impact
outputs: ATTEMPT-002..006 plan
issues: none
decision: test pure head count first, then head-aware follow-ups
evidence_refs: ATTEMPTS.md
memory_used: no
memory_sources: []
verified_against_current_repo: ATTEMPTS.md
```

## Implementer

```text
role: not activated
agent_instance_type: not_applicable
independence_scope: no code changes during ATTEMPT-002..006 sweep
inputs_checked: none
actions: none
outputs: none
issues: none
decision: disabled
evidence_refs: manifest.yaml
memory_used: no
memory_sources: []
verified_against_current_repo: manifest.yaml
```

## Runner

```text
role: experiment runner
agent_instance_type: main_agent
independence_scope: serial execution only
inputs_checked: conda:dvsr_gpu, cache availability, GPU runner lock
actions: ran ATTEMPT-002..006 sequentially with `conda run --no-capture-output`
outputs: five logs, five best checkpoints, five full checkpoints, five runner receipts
issues: the first ATTEMPT-002 launch exposed a `conda run` Unicode wrapper failure; the successful rerun used `CONDA_NO_PLUGINS=true` and `--no-capture-output`
decision: completed
evidence_refs: GTPJ_Warehouse/runs/v1/module_trial/TRIAL-001/
memory_used: no
memory_sources: []
verified_against_current_repo: manifest.yaml
```

## Result Analyst

```text
role: metric parser
agent_instance_type: role_checklist
independence_scope: parse metrics and compare ATTEMPT-002..006 only
inputs_checked: five Warehouse logs
actions: parsed the best-result blocks for ATTEMPT-002..006 and ranked them by H
outputs: ATTEMPT-003 best at H=74.27; ATTEMPT-002 second at H=73.99; ATTEMPT-006 third at H=73.96
issues: ATTEMPT-004 and ATTEMPT-005 both underperformed the current best setting
decision: ATTEMPT-003 is the only clear keep-best result from this sweep
evidence_refs: result.yaml, ATTEMPTS.md
memory_used: no
memory_sources: []
verified_against_current_repo: result.yaml, ATTEMPTS.md
```

## Quality Checker

```text
role: evidence checker
agent_instance_type: role_checklist
independence_scope: artifact boundary, manifest/result consistency, promotion gate
inputs_checked: artifact ids, Warehouse copies, manifest/result consistency, raw artifact boundary, unchanged interface semantics
actions: registered artifacts, verified hashes and sizes, checked that no raw outputs were tracked in Git
outputs: valid evidence for all five attempts; promotion blocked at the trial root
issues: clean confirmation still missing for the ATTEMPT-003 setting
decision: PASS_REVISE
evidence_refs: quality_check.md, manifest.yaml
memory_used: no
memory_sources: []
verified_against_current_repo: quality_check.md, manifest.yaml
```

## Interface Checker

```text
role: not activated
agent_instance_type: not_applicable
independence_scope: no post-implementation interface change during ATTEMPT-002..006 sweep
inputs_checked: manifest.yaml, config.yaml
actions: confirmed this sweep did not intentionally change label mapping, seen/unseen split, class order, logits shape, or metric semantics
outputs: no interface-change review required for this historical parameter sweep
issues: none
decision: disabled
evidence_refs: manifest.yaml, config.yaml
memory_used: no
memory_sources: []
verified_against_current_repo: manifest.yaml, config.yaml
```

## Reviewer

```text
role: promotion reviewer
agent_instance_type: role_checklist
independence_scope: promotion readiness and process risk
inputs_checked: result.yaml, quality_check.md, ATTEMPTS.md
actions: checked whether ATTEMPT-003 can be promoted from this sweep
outputs: promotion blocked pending clean confirmation
issues: ATTEMPT-002..006 were run from a dirty worktree after configs/ledger files were added, so they cannot be final promotion evidence
decision: PASS_REVISE
evidence_refs: result.yaml, quality_check.md, ATTEMPTS.md
memory_used: no
memory_sources: []
verified_against_current_repo: result.yaml, quality_check.md, ATTEMPTS.md
```
