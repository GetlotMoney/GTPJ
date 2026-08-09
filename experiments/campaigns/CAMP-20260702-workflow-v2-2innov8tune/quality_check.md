# Quality Check

```text
runtime: pre_run
decision: warn_repeat_required
promotion_decision: not_applicable
evidence_level: single_run_valid
subject_id: CAMP-20260702-workflow-v2-2innov8tune
subject_type: campaign
evidence_state: completed_needs_repeat
agent_runtime_gate: agent_runtime.yaml
```

## Checks

- [x] Campaign uses real right-sidebar temporary agents.
- [x] `agent_runtime.yaml` records real agent ids.
- [x] Candidate profile is limited to existing dynamic routing config switches.
- [x] `dynamic_pse_mode` is limited to `fixed` or `class`.
- [x] Campaign `RESULT_INDEX.md` is derived-index only.
- [x] Runner Monitor final allow after old batch completion.
- [x] Clean freeze commit synced to lab4090 for the campaign run.
- [x] Server run completed 10 / 10 jobs with 0 failures.
- [x] Batch summary, status, plan, and events artifact identities are recorded in `FINAL_REPORT.md`.
- [ ] Full per-log traceback/missing-metric audit is not yet recorded.
- [ ] Top-3 checkpoint retention verified after run.
- [ ] Min3 repeat is not complete for any candidate in this campaign.

## Blocking Issues

No hard GZSL/interface blocker is visible from the summary. Promotion and confirmed claims remain blocked until min3 repeat, log audit, artifact checks, and checkpoint retention are complete.

## Post-Run Findings

- Best campaign single: DR-004 H=74.75, U=72.90, S=76.69.
- Related prior strongest single: ATTEMPT-004 DR-035 H=75.02, U=72.69, S=77.51.
- Innovation probes DR-001/DR-002 are weaker than direction-tune cluster and should stop for this campaign.
- Current evidence supports `tune_promising`, not `min3_confirmed`.
