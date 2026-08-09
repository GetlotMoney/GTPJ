# ATTEMPT-018 Pre-Run Plan

## Summary

This is a live multi-agent monitored exact-repeat confirmation attempt for `A017DR095 / DR-095`.

## Source Evidence

- Source attempt: `ATTEMPT-017`
- Source run: `RUN-20260709-0001-h76-escape100-supported-routing-server-frozen-2gpu`
- Source job: `DR-095`
- Source metrics: H=75.11, U=73.00, S=77.36, ZS=82.12, best_epoch=48
- Source status: `valid_single_run`
- Confirmation status before this attempt: `not_confirmation_evidence`
- Source actual training commit: `d505e992492eb6fe7272edf0f0dc1d15a5932434`
- Local ledger/helper commit at plan time: `a884fea429a302fecc42ba8cddf9e6e66f5d07c8`

## Planned Runner

- run_id: `RUN-20260709-0002-a017dr095-restore5-live-multiagent-2gpu`
- profile: `h76-a017dr095-restore5-exact-repeat`
- jobs: 5
- gpus: `0,1`
- base_version: `v5`
- workflow_mode: `live_multi_agent_monitor`
- agent_instance_mode: `named_owner_thread`
- planned_training_commit: `d505e992492eb6fe7272edf0f0dc1d15a5932434`
- trial_dir: `experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing`
- warehouse scope: `runs/v5/module_trial/TRIAL-001/ATTEMPT-018/<run_id>/...`

## Stop Policy

Stop pending repeats after the first clean run reaches `H >= 75.11`. If all five exact repeats finish below `75.11`, close as `not_restored`; runs within `0.2` H below target are only `near_miss_not_restored`.

## Required Pre-Run Checks

- Reviewer: helper profile and tests are acceptable for formal plan generation.
- Runner Monitor: server resources and target run path are safe.
- Interface Checker: no GZSL interface, split, class order, logits shape, metric, or unsupported mode drift.
- Evidence Quality Checker: ATTEMPT-017 source evidence and ATTEMPT-018 ledger plan are sufficient.
- Log Analyst / Result Analyst: ready to independently review run outputs after launch.

## Current Gate State

The first left-sidebar pass produced independent outputs for all six roles. Reviewer, Interface Checker,
Log Analyst, and Result Analyst are `allow`. Runner Monitor and Evidence Quality Checker are currently
`block` because the Coordinator had not yet written `ATTEMPTS.md`, `agent_runtime.yaml`, `TRANSITIONS.jsonl`,
`evidence_routing.yaml`, or the explicit source training commit pin. These files are now present and must be
rechecked by the same named threads before the runner can start.
