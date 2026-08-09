# Workstreams

| Workstream | Count | Scope | Agent Roles | Status |
|---|---:|---|---|---|
| Innovation probes | 2 | Existing dynamic routing switch combinations inside TRIAL-001 | Campaign Planner, Interface Checker, Evidence Quality Checker | completed; `stop_no_gain` |
| Direction tune | 8 | Narrow direction-gate config search | Campaign Planner, Runner Monitor, Evidence Quality Checker, Result Comparator | completed; repeat candidates found |

All result facts must be derived from run manifests, Warehouse artifacts, and
formal post-run result files under the owning subject. For this campaign, the
formal owning subject is:

```text
experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/attempts/ATTEMPT-006/
```

## Work Item Mapping

Detailed owner-facing work item mapping is recorded in `WORK_ITEMS.md`.

```text
INNOV-001..INNOV-002 -> runner jobs DR-001..DR-002
TUNE-001..TUNE-008   -> runner jobs DR-003..DR-010
```

Runner-local `attempt_id` values are batch-local execution ids and must not be
treated as GitHub formal `ATTEMPT-xxx` records.

## Campaign Run Map

The campaign run map is recorded in:

```text
campaign_run_map.md
campaign_run_map.html
```

## Closeout Routing

| Route | Candidate | Decision |
|---|---|---|
| Overall repeat priority | ATTEMPT-004 DR-035 `direction_sample_h48_w0.525_a0.005` | ATTEMPT-005 was seed sweep, not exact repeat; source-seed exact repeat still required |
| Campaign repeat priority | DR-004 `tune_direction_h48_w0.525_a0.003` | repeat candidate |
| Campaign neighbor repeat | DR-006 `tune_direction_h48_w0.50_a0.005` | repeat candidate |
| Backup | DR-010 `tune_direction_h48_w0.45_a0.004` | backup repeat candidate |
| Innovation probes | DR-001 / DR-002 | stop for this campaign |
