# ATTEMPT-007 Task Start Card

```yaml
owner_phrase: "run formal exact repeat for previous H=75.02 after local workflow freeze"
task_type: confirmation / trial-internal exact repeat
base_version: v5
base_code_tag: v5
code_branch: codex/dr035-exact-repeat-20260703
subject_id: ATTEMPT-007
subject_type: attempt
target: ATTEMPT-004 DR-035 direction_sample_h48_w0.525_a0.005
source_run: RUN-20260702-0002-dr018-confirm-ablate50-2gpu
source_seed: 5
source_H: "75.02"
repeat_type: same_seed_min3_exact_repeat
formal_runner_allowed: blocked_until_agent_gate_and_gpu_slot
formal_evidence_allowed: blocked_until_agent_gate_and_gpu_slot
agent_mode: real_multi_agent
agent_instance_mode: temporary_subagent
owner_monitor_mode: true
writes:
  github: experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/attempts/ATTEMPT-007
  warehouse: /data/lby/projects/cv_project/GTPJ_Warehouse/runs/v5/module_trial/TRIAL-001/
current_blockers:
  - v5 strict-template run is still active on lab4090 GPU0/GPU1
  - DR035 live agent allow outputs are pending
  - server must not switch branches until the active v5 run is complete
next_action: finish local pre-run gate, then wait for v5 cleanup before syncing and starting DR035
```

## Scope

ATTEMPT-007 corrects the ATTEMPT-005 classification issue. ATTEMPT-005 used seeds 6/7/8, so it is only a seed_sweep / stability run. ATTEMPT-007 keeps the source seed fixed at 5 for all three repeats.

This run does not add a new module, does not tune parameters, does not create a new version, and does not open promotion.
