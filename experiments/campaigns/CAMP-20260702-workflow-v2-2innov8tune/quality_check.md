# Quality Check

```text
runtime: pre_run
decision: allow_after_freeze_sync
promotion_decision: not_applicable
evidence_level: formal_pre_run
subject_id: CAMP-20260702-workflow-v2-2innov8tune
subject_type: campaign
evidence_state: planning
agent_runtime_gate: agent_runtime.yaml
```

## Checks

- [x] Campaign uses real right-sidebar temporary agents.
- [x] `agent_runtime.yaml` records real agent ids.
- [x] Candidate profile is limited to existing dynamic routing config switches.
- [x] `dynamic_pse_mode` is limited to `fixed` or `class`.
- [x] Campaign `RESULT_INDEX.md` is derived-index only.
- [x] Runner Monitor final allow after old batch completion.
- [ ] Clean freeze commit synced to lab4090. This must be verified after this pre-run freeze commit exists.
- [ ] Warehouse artifact identities recorded after run.
- [ ] Top-3 checkpoint retention verified after run.

## Blocking Issues

No local pre-run evidence blocker remains. Formal server start still requires verifying that the freeze commit is present on lab4090.
