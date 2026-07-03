# ATTEMPT-007 Quality Check

```yaml
attempt_id: ATTEMPT-007
run_id: RUN-20260703-0002-dr035-exact-repeat-s5-min3-2gpu
decision: confirmed_candidate
evidence_state: min3_confirmed
formal_evidence: true
promotion_decision: blocked
repeat_type: same_seed_min3_exact_repeat
exact_repeat: true
```

## Pre-Run Checks

- [x] Target is fixed: ATTEMPT-004 DR-035 `direction_sample_h48_w0.525_a0.005`.
- [x] ATTEMPT-005 is not reused as exact repeat because it used seeds 6/7/8.
- [x] ATTEMPT-007 keeps all repeats at source seed 5.
- [x] This is confirmation only: no innovation, no new tuning, no promotion.
- [x] GZSL split, class order, label mapping, and metric semantics are unchanged.
- [x] Logits contract remains `[B (image/sample count), C (class count)]`.
- [x] `dynamic_pse_mode=fixed`; no unsupported `sample` PSE gate is used.
- [x] Dynamic ICSA remains fixed.
- [x] `batch_size=64`.
- [x] Epoch schedule is explicit: config `epochs=30`, planned train epochs = `lr_stages` sum = 50.
- [x] Raw logs/checkpoints stay outside GitHub.
- [x] Helper writes `start_batch.sh` with LF newlines to avoid `batch_status.json\r` status-file pollution.

## Runtime Gate

- [x] Live Runner Monitor output exists and returned allow.
- [x] Live Interface Checker output says allow/pass.
- [x] Live Evidence Quality Checker output says allow/pass.
- [x] Live Result Comparator output says allow/pass.
- [x] `agent_runtime.yaml` records real right-sidebar temporary agent ids.
- [x] v5 strict-template run completed and released GPU slots before launch.
- [x] Server repo synced to frozen DR035 commit `197ed758ed46112373b11de4ea8de5e4b138dba5`.
- [x] `validate-agent-runtime --path agent_runtime.yaml` passed before launch.
- [x] `multi-agent-preflight --path agent_runtime.yaml` passed before launch.
- [x] `agent-cleanup-plan --path agent_runtime.yaml` was reviewed before launch.
- [x] Frozen batch plan was generated without overwriting an existing run dir.
- [x] Generated per-job configs matched seed=5, batch size 64, direction sample, hidden 48, anchor 0.005, `weight_s2v=0.525`, PSE fixed.

## Post-Run Checks

- [x] 3 / 3 jobs completed, 0 failed.
- [x] `summary.csv`, `summary.jsonl`, `batch_status.json`, `plan.json`, and `events.jsonl` are available.
- [x] Runtime artifact hash and size are recorded in `result.yaml`.
- [x] Result table reports H/U/S/ZS for all three runs.
- [x] Stability reports mean/min/max/range.
- [x] Dedicated ATTEMPT-007 warehouse path contains 3 logs, 6 config YAML files, 3 best checkpoints, `FILES.txt`, and `SHA256SUMS.txt`.
- [x] GPU0/GPU1 returned to idle after the run.
- [x] Promotion remains blocked.

## Confirmation Gate

| Check | Threshold | Observed | Verdict |
|---|---:|---:|---|
| mean H | >= 74.60 | 74.61 | pass |
| min H | >= 74.45 | 74.58 | pass |
| range H | <= 0.50 | 0.04 | pass |
| U/S collapse | none obvious | U mean 72.58, S mean 76.75 | pass |

## Warnings

- Server pytest is unavailable in both checked server Python interpreters; local `python -m pytest tests/test_gtpj_workflow.py -q -p no:cacheprovider` passed 95 tests before launch.
- The generated dynamic runner top-level `batch_status.status` remains `planned`, but all job-level statuses are `completed`; `summary.csv/jsonl` and `events.jsonl` agree on 3/3 completed.
- Runtime `warehouse_dir` fields still point to shared historical `attempt-001/002/003` folders. Current ATTEMPT-007 logs/configs/checkpoints were copied to a dedicated warehouse directory to preserve evidence identity.
- Default shared warehouse retention had already removed the current DR-001 checkpoint from `attempt-001`; it was recovered from the runner worktree and copied to the dedicated ATTEMPT-007 warehouse.

Decision: `confirmed_candidate`; promotion remains blocked.
