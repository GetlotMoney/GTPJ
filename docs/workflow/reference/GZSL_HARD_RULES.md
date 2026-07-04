# GZSL Hard Rules

本文是所有正式 GTPJ experiments 的共享 hard gate。

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

每个新 module 必须记录：

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

如果任何 hard rule 不清楚，该 subject 只能是：

```text
blocked
rerun
reject
```

它不能是：

```text
keep
best
promote
confirmed
baseline-grade evidence
```

## Evidence Routing

GZSL checks 必须出现在 `rule_checks` 中，并包含 `rule_id`、`verdict`、`checked_by`
和 `authority_ref`。失败的 GZSL checks 不能 advance 或 promote 一个 subject。
