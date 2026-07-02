# Workstreams

| Workstream | Count | Scope | Agent Roles | Status |
|---|---:|---|---|---|
| Innovation probes | 2 | Existing dynamic routing switch combinations inside TRIAL-001 | Campaign Planner, Interface Checker, Evidence Quality Checker | completed; `stop_no_gain` |
| Direction tune | 8 | Narrow direction-gate config search | Campaign Planner, Runner Monitor, Evidence Quality Checker, Result Comparator | completed; repeat candidates found |

All result facts must be derived from run manifests, Warehouse artifacts, and post-run result files.

## Closeout Routing

| Route | Candidate | Decision |
|---|---|---|
| Overall repeat priority | ATTEMPT-004 DR-035 `direction_sample_h48_w0.525_a0.005` | min3 repeat first |
| Campaign repeat priority | DR-004 `tune_direction_h48_w0.525_a0.003` | repeat candidate |
| Campaign neighbor repeat | DR-006 `tune_direction_h48_w0.50_a0.005` | repeat candidate |
| Backup | DR-010 `tune_direction_h48_w0.45_a0.004` | backup repeat candidate |
| Innovation probes | DR-001 / DR-002 | stop for this campaign |
