# ATTEMPT-005 Quality Check

```yaml
attempt_id: ATTEMPT-005
run_id: RUN-20260703-0001-dr035-min3-confirm-2gpu
decision: pre_run_warn_until_agent_runtime_passes
evidence_state: interface_precheck_passed
formal_evidence: true
promotion_decision: blocked
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
- [ ] `validate-agent-runtime` passes.
- [ ] Server repo syncs to the frozen commit.
- [ ] GPU0/GPU1 are idle and no old dynamic runner is active.
- [ ] Frozen batch plan is generated without overwriting any existing run dir.

## Required After Runner

- [ ] 3 / 3 jobs completed, 0 failed.
- [ ] `summary.csv`, `summary.jsonl`, `batch_status.json`, `plan.json`, and `events.jsonl` are available.
- [ ] Runtime artifact hash and size are recorded.
- [ ] Result table reports H/U/S/ZS for all three repeats.
- [ ] Stability reports mean/min/max/range.
- [ ] Warehouse copy/receipt is available.
- [ ] Only Top-3 model checkpoints are retained, or an explicit exception is documented.

## Confirmation Gate

Pass only if:

```text
mean H >= 74.60
min H >= 74.45
max H - min H <= 0.50
no obvious U/S collapse
```

If these fail, the correct state is `stopped_repeat_unstable` or `rerun_required`, not promotion.
