# Agent Summary

```text
experiment_id: CONFIRM-001
run_id: RUN-20260626-141736-confirm-v1-seed5
base_version: v1
code_branch: exp/v1-confirm-001-v1-seed5
code_commit: 43122528843d74928ccf3006eab1be80b4c7c885
agent_set: Coordinator, Runner, Log Analyst, Quality Checker
serial_agents: Coordinator -> Runner -> Coordinator
parallel_agents: Log Analyst + Quality Checker after/around run evidence collection
disabled_agents: Reader/Planner, Implementer, Interface Checker, Reviewer, Result Analyst
runtime_state: .gtpj_runtime/runs/RUN-20260626-141736-confirm-v1-seed5/status.json
warehouse_report_artifacts: log:v1:confirmation:CONFIRM-001:attempt-001:runner_stderr
final_decision: keep, with runner warning
```

## Coordinator

```text
role: Route confirmation workflow, create experiment ledger, manage branch/run ids, record final evidence.
inputs_checked: git branch/status, v1 config, experiment directory, Warehouse artifact ids, validation outputs.
actions: Created CONFIRM-001 ledger, launched Runner with GPU lock, recorded metrics and artifacts, merged experiment ledger to main locally.
outputs: README.md, manifest.yaml, result.yaml, result.md, quality_check.md, experiment indexes.
issues: Remote main required push after local merge; no raw artifacts were written to GitHub.
decision: keep
evidence_refs: manifest.yaml, result.yaml, quality_check.md
```

## Runner

```text
role: Run fixed v1 baseline confirmation command and write raw artifacts to Warehouse.
inputs_checked: config.yaml, seed=5, CUB standard_v1 split/cache fingerprint, GPU runner lock.
actions: Ran conda:dvsr_gpu training command and copied log/checkpoints to Warehouse.
outputs: training log, best checkpoint, full checkpoint, runner stdout/stderr, receipts.
issues: conda run wrapper emitted UnicodeEncodeError after training completed.
decision: completed_with_warning
evidence_refs: log:v1:confirmation:CONFIRM-001:attempt-001, checkpoint:v1:confirmation:CONFIRM-001:attempt-001:best, checkpoint:v1:confirmation:CONFIRM-001:attempt-001:full
```

## Log Analyst

```text
role: Parse final training log facts without inventing metrics.
inputs_checked: Warehouse training log and final Best Results block.
actions: Required Training Finished / Best Results block before result recording.
outputs: U=71.35, S=76.35, H=73.77, ZS=81.24, best_epoch=32.
issues: Intermediate epoch metrics were not treated as final evidence.
decision: completed
evidence_refs: result.yaml, result.md
```

## Quality Checker

```text
role: Check evidence completeness, GitHub boundary, split/label/metric comparability, and remote governance status.
inputs_checked: manifest.yaml, result.yaml, quality_check.md, artifact hashes, validate/audit-boundary/validate-remote output.
actions: Confirmed local validate and boundary audit, flagged remote-main mismatch before push, accepted result with warning after final evidence existed.
outputs: PASS_WITH_WARNINGS in quality_check.md.
issues: Runner wrapper warning; remote governance required push after branch/main updates.
decision: pass_with_warnings
evidence_refs: quality_check.md
```

