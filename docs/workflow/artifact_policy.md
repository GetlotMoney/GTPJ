# Artifact Policy

This file defines the GitHub boundary and external artifact boundary for GTPJ. The goal is to keep GitHub lightweight while preserving a complete evidence chain.

## GitHub Boundary

GitHub is the reproducible control plane, governance source, and lightweight result index. It must answer:

```text
How can this result be reproduced?
What is the result?
Why was it kept, rejected, rerun, or promoted?
Which code, config, command, seed, dataset split, label mapping, class order, and evaluation path were used?
Which external artifact is the raw evidence, where is it, and what is its hash?
```

GitHub does not store raw logs, checkpoints, generated experiment figures, full paper-reading material, or complete idea-tree reasoning.

## External Stores

External directories carry complete materials and large assets:

```text
GTPJ_Research
  Paper PDFs, reading notes, full idea trees, source reviews, and long-form reasoning.

GTPJ_Warehouse
  Raw logs, checkpoints, experiment visualizations, experiment tables, failure cases, and run receipts.
```

GitHub references external assets through logical URIs:

```text
warehouse://gtpj/runs/v1/tune/TUNE-001_topo008/attempt-001/logs/train.log
research://ideas/IDEA-0001.md
```

Local physical paths are stored in the ignored local file:

```text
.gtpj/local_paths.yaml
```

## Artifact Identity

Every external artifact that enters the evidence chain must have a stable identity, not just a path:

```text
artifact_id
role
uri
sha256
size_bytes
created_at or recorded_at
producer / produced_by
required_for
status
```

A path only says where the file is. The hash and size prove which exact file it is.

## Forbidden GitHub Artifacts

Do not commit these to GitHub:

- `train_log/`
- `experiments/**/logs/*`
- `experiments/**/checkpoints/*`
- generated experiment figures under `experiments/**/figures/*`
- `*.pt`, `*.pth`, `*.ckpt`, `*.onnx`
- `*.npy`, `*.npz`
- raw datasets, feature caches, tensor dumps
- paper PDFs, complete OCR dumps, complete reading libraries, complete idea trees
- `.gtpj/local_paths.yaml`, `.gtpj/locks/`, `.gtpj_runtime/`

Allowed GitHub artifacts:

- code, config, schema, workflow helper
- `manifest.yaml`
- `result.yaml`
- `result.md`
- `quality_check.md`
- `agent_summary.md`
- version tree, experiment registry, lightweight idea index
- small hand-maintained explanatory figure source files, while generated experiment figures must stay external

## Boundary Audit

Before committing, run:

```bash
python workflow/gtpj_workflow.py audit-boundary
```

`audit-boundary` checks that:

- raw logs, checkpoints, generated figures, and caches are not tracked or commit candidates under `experiments/`
- old `copied_log` evidence does not continue as the new evidence model
- result records point to manifests
- manifests point to external artifact identities
- GitHub does not contain assets that belong in the external stores

## Legacy Migration

The historical `GTPJ-v1 / tag v1 / H=73.93` baseline log was migrated to the local warehouse:

```text
artifact_id: log:legacy:v1_baseline:GTPJ-v1_CUB_seed5_20260613-145232
artifact_uri: warehouse://logs/legacy/v1_baseline/GTPJ-v1_CUB_seed5_20260613-145232.txt
sha256: 850a01a5c1500f75fef3d9729b8e89b47c78aa40203792341b03515ddc5edfb9
size_bytes: 139148
```

The repository should not keep any Git-tracked raw log exception. Historical evidence remains reproducible through the external artifact pointer, hash, config snapshot, result record, and quality record.
