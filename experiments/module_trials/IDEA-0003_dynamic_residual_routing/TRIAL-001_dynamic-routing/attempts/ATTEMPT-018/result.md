# ATTEMPT-018 Result

ATTEMPT-018 completed the DR-095 exact-repeat restore attempt: 5/5 jobs completed, 0 failed, 0 skipped.

The source single from ATTEMPT-017 was `DR-095 / A017DR095`, `a015dr035_weight_plus_0.01`, with `H=75.11`. ATTEMPT-018 repeated the same seed-5 configuration five times with restore target `H>=75.11`.

| job | repeat | H | U | S | ZS | epoch |
|---|---:|---:|---:|---:|---:|---:|
| DR-001 | 1 | 74.71 | 72.19 | 77.40 | 81.95 | 48 |
| DR-002 | 2 | 74.62 | 73.03 | 76.28 | 81.75 | 37 |
| DR-003 | 3 | 74.51 | 72.77 | 76.33 | 81.38 | 50 |
| DR-004 | 4 | 74.60 | 72.86 | 76.42 | 81.68 | 37 |
| DR-005 | 5 | 74.45 | 72.29 | 76.76 | 81.68 | 50 |

Aggregate:

- best_H: 74.71
- mean_H: 74.58
- min_H: 74.45
- max_H: 74.71
- range_H: 0.26

Decision:

- restored: false
- confirmation_decision: not_restored
- evidence_state: stopped_repeat_unstable
- promotion_decision: blocked

The best repeat is below both `restore_target_H=75.11` and the near-miss threshold `74.91`, so this is not `near_miss_not_restored`; it is a completed max-5 exact-repeat non-restore result.

Source-control caveat: this run was planned before the later helper hardening that enforces clean post-fix source-control checks. It is valid as ATTEMPT-018 observed repeat evidence, but any future restored/promotion claim must use the post-fix strict gate and clean server worktree.
