# GZSL Hard Rules

This file is the shared hard gate for all formal GTPJ experiments.

## Non-Negotiable Evaluation Rules

| Rule | Required state | If unclear |
|---|---|---|
| seen/unseen split | unchanged | blocked/rerun/reject |
| class order | unchanged | blocked/rerun/reject |
| label mapping | unchanged | blocked/rerun/reject |
| metric semantics | unchanged GZSL U/S/H/ZS | blocked/rerun/reject |
| unseen label leakage | forbidden | reject/block |

## Tensor And Interface Rules

| Object | Required meaning |
|---|---|
| image batch | `B` = image/sample count |
| logits | `[B（图片/样本数量）, C（类别数量）]` |
| class axis | `C` = protected evaluation class count |
| text/visual features | exact shape, dtype, device, train/eval behavior documented |

Every new module must document:

```text
input tensors
output tensors
gradient path
train behavior
eval behavior
config switch
baseline-off equivalence
metric impact
```

## Blocking Rule

If any hard rule is unclear, the subject can only be:

```text
blocked
rerun
reject
```

It cannot be:

```text
keep
best
promote
confirmed
baseline-grade evidence
```

## Evidence Routing

GZSL checks must appear in `rule_checks` with `rule_id`, `verdict`, `checked_by`, and `authority_ref`. Failed GZSL checks cannot advance or promote a subject.
