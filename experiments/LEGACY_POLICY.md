# Legacy Policy

This file records how evidence created before the boundary refactor is handled.

## Principles

- Do not rewrite Git history.
- Do not move the confirmed `v1` tag.
- Do not lose baseline evidence while removing raw artifacts from GitHub.
- From this boundary refactor onward, GitHub stores only code, configs, manifests, result indexes, schemas, and governance documents.

## Migrated Legacy Artifact

The historical `GTPJ-v1 / tag v1 / H=73.93` baseline log has been copied to the local warehouse:

```text
artifact_id: log:legacy:v1_baseline:GTPJ-v1_CUB_seed5_20260613-145232
artifact_uri: warehouse://logs/legacy/v1_baseline/GTPJ-v1_CUB_seed5_20260613-145232.txt
sha256: 850a01a5c1500f75fef3d9729b8e89b47c78aa40203792341b03515ddc5edfb9
size_bytes: 139148
local_path: D:\backup\Documents\Myself\GTPJ_Warehouse\logs\legacy\v1_baseline\GTPJ-v1_CUB_seed5_20260613-145232.txt
```

The Git repository should no longer track `experiments/**/logs/*`, including legacy baseline logs. The warehouse copy is the raw evidence; the repo keeps only artifact pointers and hashes.

## New Experiment Rule

New tune, ablation, confirmation, innovation, and promotion records must not add raw logs, checkpoints, generated figures, caches, or other bulky artifacts to GitHub. They must reference external artifacts through `manifest.yaml`, `result.yaml`, and review documents.
