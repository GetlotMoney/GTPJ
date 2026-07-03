# ATTEMPT-005 Quality Check

```yaml
attempt_id: ATTEMPT-005
run_id: RUN-20260703-0001-dr035-min3-confirm-2gpu
decision: not_confirmed
evidence_state: stopped_repeat_unstable
formal_evidence: true
promotion_decision: blocked
repeat_type: seed_sweep
exact_repeat: false
```

## Pre-Run Checks

- [x] Target is fixed: ATTEMPT-004 DR-035 `direction_sample_h48_w0.525_a0.005`.
- [x] This is confirmation only: no innovation, no new tuning, no promotion.
- [x] GZSL split, class order, label mapping, and metric semantics are unchanged.
- [x] Logits contract remains `[B（图片/样本数量）, C（类别数量）]`.
- [x] `dynamic_pse_mode=fixed`; no unsupported `sample` PSE gate is used.
- [x] Dynamic ICSA remains fixed.
- [x] `batch_size=64`.
- [x] Epoch schedule is explicit: config `epochs=30`, planned train epochs = `lr_stages` sum = 50.
- [x] Raw logs/checkpoints stay outside GitHub.
- [x] Checkpoint retention rule is Top-3 after closeout.

## Required Before Runner

- [x] `agent_runtime.yaml` records real right-sidebar temporary agent ids.
- [x] `validate-agent-runtime` passes.
- [x] Server repo syncs to the frozen commit `4eb948c237ffc79a64f8cd4bed151c813a79bbcc`.
- [x] GPU0/GPU1 were idle and no old dynamic runner was active before launch.
- [x] Frozen batch plan is generated without overwriting any existing run dir.

## Required After Runner

- [x] 3 / 3 jobs completed, 0 failed.
- [x] `summary.csv`, `summary.jsonl`, `batch_status.json`, `plan.json`, and `events.jsonl` are available.
- [x] Runtime artifact hash and size are recorded in `result.yaml`.
- [x] Result table reports H/U/S/ZS for all three runs.
- [x] Stability reports mean/min/max/range.
- [x] Warehouse paths are recorded in runtime summaries.
- [ ] Only Top-3 model checkpoints are retained, or an explicit exception is documented.

## Classification Correction

- [x] Seed changed from source seed 5 to seeds 6/7/8.
- [x] Therefore this is not `exact_repeat`.
- [x] Correct type is `seed_sweep` / `multi_seed_stability`.
- [x] Multi-seed best cannot be used as exact-repeat confirmed evidence.

## Confirmation Gate

Pass only if:

```text
mean H >= 74.60
min H >= 74.45
max H - min H <= 0.50
no obvious U/S collapse
```

If these fail, the correct state is `stopped_repeat_unstable` or `rerun_required`, not promotion.

Observed:

```text
H mean = 74.15
H min = 73.91
H max = 74.39
H range = 0.48
```

Decision: `not_confirmed`; promotion remains blocked.
