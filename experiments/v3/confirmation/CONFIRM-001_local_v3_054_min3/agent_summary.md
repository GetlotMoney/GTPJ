# Agent Summary

## Activation

Mode: role-only workflow review. No new model agents were launched for this record; the summary consolidates the completed server controllers, diagnostics, and ledger checks.

## Roles

| Role | Scope | Finding |
|---|---|---|
| Coordinator | Decide which candidate has sufficient min3 evidence | `local-v3-054` is the only stable confirmed candidate from the checked set |
| Server Runner | Execute repeats on `lab4090` GPU0 | 3 / 3 `local-v3-054` repeats completed with H metrics |
| Log Analyst | Parse receipts, training logs, and runtime summaries | H values are `74.46 / 74.42 / 74.47`; all best epochs are `34` |
| Quality Checker | Verify evidence chain and ledger boundaries | Raw artifacts remain in Warehouse; Git records artifact ids, URIs, hashes, and sizes |

## Inputs Reviewed

- Server run: `RUN-20260629-1722-server-gpu0-local-top2-min3`
- Source candidate: `RUN-20260629-local-v3-explore-001/local-v3-054`
- Warehouse base: `/data/lby/projects/cv_project/GTPJ_Warehouse/runs/v3/confirmation/RUN-20260629-1722-server-gpu0-local-top2-min3`
- Runtime summary artifact: `summary:v3:confirmation:CONFIRM-001:min3-runtime`
- Source evidence artifact: `diagnostic:v3:confirmation:CONFIRM-001:source-evidence`
- Server receipt correction artifact: `diagnostic:v3:confirmation:CONFIRM-001:server-receipt-corrections`

## Result

`local-v3-054` is confirmed and promoted to `GTPJ-v4`:

```text
H values: 74.46 / 74.42 / 74.47
confirmed_H: 74.47
H_mean: 74.45
best_observed_H: 74.47
reference_H: 74.27
delta_H_vs_reference_mean: +0.18
delta_H_vs_reference_best: +0.20
```

## Decision Boundary

This record does not update the canonical v3 baseline. It creates a new official version result, `GTPJ-v4`, under the owner standing min3 promotion rule. It does not run `activate-version`.
