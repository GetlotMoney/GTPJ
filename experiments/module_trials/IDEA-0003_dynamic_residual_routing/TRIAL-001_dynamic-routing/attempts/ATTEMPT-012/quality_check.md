# ATTEMPT-012 Quality Check

## Pre-run

- Interface semantics: unchanged from v5 / TRIAL-001.
- GZSL metric semantics: unchanged.
- Dynamic PSE mode: fixed only.
- ICSA dynamic mode: fixed only.
- Stop mechanism: `STOP_REQUESTED` in server batch directory.
- Formal gate: `agent_runtime.yaml` must pass before upload/start.

## Post-run Requirements

- Server run was stopped by owner after 6/50 jobs.
- `batch_status.json` final mirror shows 6 completed and 44 skipped by `STOP_REQUESTED`.
- Only DR047 seeds 6-11 completed, so the result is partial-only.
- Do not treat this as complete multi-seed stability, confirmation, best selection, or promotion evidence.
- Promotion remains blocked.
