# Automatic Promotion

Promotion means a clean code/config state is accepted as a new formal baseline
version. A promotion creates version materials and a version tag. It does not
automatically run `activate-version`.

## Owner Standing Rule: Min3 Auto Promotion

From 2026-06-29 onward, a candidate is reproducible when all of the following
are true:

- the same `source_job_id` has at least 3 successful repeats;
- each repeat is completed/ok and has valid U/S/H/ZS metrics;
- the repeats use the same code/config/evaluation contract;
- class order, seen/unseen split, label mapping, logits shape, and metric
  semantics are unchanged or explicitly audited.

Such a candidate is upgraded to `baseline_grade` evidence and can be promoted
automatically to the next formal version.

For a min3-confirmed candidate, the formal result row uses the successful repeat
with the highest H. Record that row as `confirmed_H` / official H, and take the
official U/S/ZS from the same repeat. Still record `H_mean`, `H_min`, `H_max`,
and repeat count as stability evidence. A single high run cannot become
`confirmed_H` until the min3 confirmation cluster has passed.

When several min3-confirmed candidates exist, promote the strongest candidate by
`confirmed_H` first, using repeat stability (`H_mean`, `H_min`, spread) as the
guardrail or tie-breaker.

## Standing GitHub Permission

The owner grants standing permission for the Coordinator to push validated
promotion ledger commits and version tags to GitHub after checks pass.

This permission does not allow:

- force-push;
- deleting remote refs;
- rewriting history;
- changing active code aliases;
- running `activate-version`.

## Promotion Does Not Activate Code

`promotion` creates a formal version/tag such as `v4`.

`activate-version vX` is a separate action. It is required before current runtime
aliases such as active configs are switched. If `activate-version` has not been
run, record:

```text
active_main_update: not_activated
```

## Trigger Fields

A result may enter automatic promotion when it records:

```text
promotion_decision: promote
promote_to: vX
evidence_level: baseline_grade
confirmation_status: confirmed
```

For min3 auto promotion, the source confirmation may be upgraded from
`confirmation_grade` to `baseline_grade` when the min3 rule above is satisfied.

If the owner accepts or activates a candidate without `baseline_grade` evidence,
record it as `owner_activated_unconfirmed` or another explicit provisional
status. Do not convert such a candidate into a confirmed formal version until
the promotion gates pass.

## Hard Gates

All gates must pass:

- source experiment/trial records parent version, code source, branch, commit,
  config, command, metrics, and artifact evidence;
- source evidence is not a single high point only;
- `dirty_state: clean` and `git_dirty: false` are recorded or inferable;
- metrics include U, S, H, ZS, seed, best epoch, and comparison reference;
- `best_observed_H`, `confirmed_H`, and `confirmation_status` are distinct;
- external artifact id, URI, sha256, and size are recorded;
- `quality_check.md` has no blocking issue;
- GitHub does not contain raw logs, checkpoints, generated figures, or caches;
- target config can be frozen to `config/versions/vX.yaml`;
- current working tree is clean before tagging/pushing.

If any hard gate fails, do not create the formal version. Record:

```text
promotion_decision: blocked
```

## Automatic Actions

After gates pass, Coordinator should:

1. Create a promotion branch from current `main`.
2. Copy or create the promoted config at `config/versions/vX.yaml`.
3. Create `experiments/vX/` and `experiments/vX/baseline/`.
4. Update `experiments/VERSION_TREE.md`.
5. Update `experiments/EXPERIMENT_REGISTRY.md`.
6. Update `docs/PROJECT_STATUS.md`.
7. Update `README.md` and other lightweight indices as needed.
8. Update helper canonical baseline metadata.
9. Run validation.
10. Commit the promotion ledger.
11. Create local tag `vX`.
12. Push the promotion branch and tag to GitHub under the standing permission.
13. Do not change active code aliases unless `activate-version vX` is explicitly
    requested.

## Required Version Record Fields

Every new version must record:

```text
version:
parent_version:
parent_tag:
code_tag:
ledger_source:
ledger_source_commit:
source_experiment:
source_trial:
change_type:
config_snapshot:
baseline_result:
known_risks:
confirmation_requirement:
evidence_level:
best_observed_H:
confirmed_H:
confirmation_status:
active_main_update: not_activated | activated_by_owner | owner_accepted_current_tag
```
