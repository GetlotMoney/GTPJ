# ATTEMPT-007 Quality Check

```yaml
attempt_id: ATTEMPT-007
run_id: RUN-20260703-0002-dr035-exact-repeat-s5-min3-2gpu
decision: pending_runner
evidence_state: hypothesis_ready
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
- [x] Checkpoint retention rule is Top-3 after closeout.

## Required Before Runner

- [x] Live Runner Monitor output exists.
- [x] Live Interface Checker output says allow/pass.
- [x] Live Evidence Quality Checker output exists.
- [x] Live Result Comparator output says allow/pass.
- [ ] Live Runner Monitor output says allow/pass. Current decision: block until v5 cleanup.
- [ ] Live Evidence Quality Checker output says allow/pass. Current decision: block until runtime gate and v5 cleanup.
- [ ] `agent_runtime.yaml` records real right-sidebar temporary agent ids.
- [ ] `validate-agent-runtime --path agent_runtime.yaml` passes.
- [ ] `multi-agent-preflight --path agent_runtime.yaml` passes.
- [ ] `agent-cleanup-plan --path agent_runtime.yaml` is reviewed.
- [ ] v5 strict-template run has completed or released the GPU slots.
- [ ] Server repo syncs to the frozen DR035 commit.
- [ ] Frozen batch plan is generated without overwriting any existing run dir.

## Required After Runner

- [ ] 3 / 3 jobs completed, 0 failed.
- [ ] `summary.csv`, `summary.jsonl`, `batch_status.json`, `plan.json`, and `events.jsonl` are available.
- [ ] Runtime artifact hash and size are recorded in `result.yaml`.
- [ ] Result table reports H/U/S/ZS for all three runs.
- [ ] Stability reports mean/min/max/range.
- [ ] Warehouse paths are recorded in runtime summaries.
- [ ] Only Top-3 model checkpoints are retained, or an explicit exception is documented.

## Confirmation Gate

Pass only if:

```text
mean H >= 74.60
min H >= 74.45
max H - min H <= 0.50
no obvious U/S collapse
```

If these fail, the correct state is `not_confirmed`, not promotion.
