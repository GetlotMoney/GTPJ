# Git Policy

## Permanent Objects

- `main`: latest stable project files and lightweight records.
- `v1`, `v2`, `v3`: permanent baseline tags.
- `trial/idea-xxxx/trial-xxx`: permanent trial code snapshots.

## Temporary Branches

```text
dev/idea-0001-trial-001-short-name
dev/v2-short-name
exp/v1-tune-001-short-name
exp/v1-ablation-001-short-name
```

Rules:

- Do not create controller branches.
- Do not run new module work directly on `main`.
- Trial branches start from a baseline tag.
- Tune, ablation, and final branches start from the matching baseline tag.
- Failed trial code is preserved by trial tag, not merged into `main`.
- Successful trial code can be promoted into `main` and tagged as a new `vX`.

Push rule:

- Do not push automatically. Push only after the owner explicitly asks.
