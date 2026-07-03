# Runner Monitor Output

role: runner_monitor
agent_instance_id: 019f287c-a108-7031-ba5c-6e1ae6c1c91d
display_name: Pauli / shared Runner Monitor
decision: allow
post_run_close_allowed: true

## Checked Scope

- ATTEMPT-007 / `RUN-20260703-0002-dr035-exact-repeat-s5-min3-2gpu`
- server branch `codex/dr035-exact-repeat-20260703` at `197ed758ed46112373b11de4ea8de5e4b138dba5`
- runtime files: `batch_status.json`, `summary.csv`, `summary.jsonl`, `events.jsonl`
- dedicated ATTEMPT-007 warehouse evidence directory
- GPU/process state after Runner completion

## Findings

- Runner completed 3 / 3 jobs with 0 failures.
- H values: 74.58 / 74.62 / 74.62.
- mean H=74.61, min H=74.58, range H=0.04.
- Gate passes: mean H >= 74.60, min H >= 74.45, range H <= 0.50.
- GPU0/GPU1 returned to idle: 6 MiB, 0% utilization, no compute apps.
- Dedicated warehouse exists and contains 3 logs, 6 config YAML files, 3 best checkpoints, and `SHA256SUMS.txt`.

## Warnings

- Runtime `batch_status.json` top-level `status` remains `planned`, while all three job statuses are `completed`.
- Runtime `warehouse_dir` values still point to shared historical `attempt-001/002/003` folders; dedicated ATTEMPT-007 warehouse evidence is complete and should be used for this attempt.

## Close Result

Runner Monitor can be closed after Coordinator records post-run result, quality, artifact identity, and cleanup.
