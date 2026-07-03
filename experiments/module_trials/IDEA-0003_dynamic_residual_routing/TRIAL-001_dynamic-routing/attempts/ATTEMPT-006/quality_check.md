# ATTEMPT-006 Quality Check

```text
decision: allow_keep_as_trial_internal_evidence
evidence_state: tune_promising
confirmation_status: not_confirmed
promotion_decision: blocked
campaign_role: routing_index_only
```

## Checks

- [x] Formal result evidence is written under the parent Trial attempt directory.
- [x] Campaign directory is treated as routing index only.
- [x] `INNOV-*` items are classified as `innovation_probe`, not full paper-derived innovation.
- [x] Runner-local `DR-*` and batch-local `attempt_id` ids are not treated as GitHub formal attempt ids.
- [x] GZSL split, class order, label mapping, metric semantics, and logits contract are unchanged by this ledger correction.
- [x] Result remains single-run / tune-promising evidence only.
- [ ] Exact repeat of TUNE-002 / DR-004.
- [ ] Direction ablation support for this narrow region.

## Blocking Boundaries

This attempt cannot be used for:

```text
confirmed_H
promotion
new vX
paper claim
```

until repeat / stability and ablation gates are satisfied.
