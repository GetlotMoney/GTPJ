# Result Index Protocol

This file defines the minimum lightweight evidence structure that GitHub stores for GTPJ experiments.

## Experiment Files

New experiment directories contain:

```text
config.yaml
manifest.yaml
result.yaml
result.md
quality_check.md
README.md
```

They must not create or commit raw `logs/`, checkpoints, generated figures, feature caches, or tensor dumps.

## `manifest.yaml`

`manifest.yaml` is the reproducibility map for programs and agents. It records:

- experiment id, kind, attempt id, status
- base version, base code tag, code branch, code commit, dirty state
- config path and config sha256
- run command, seed, dataset, split id, class order id, label mapping id, metric contract id
- idea summary, when the experiment changes code or method
- external artifact identity: `artifact_id`, `uri`, `sha256`, `size_bytes`, `role`, `status`
- whether interface contract review and boundary audit are required

For tune experiments, the idea summary can be empty, but the hypothesis must state that this is parameter tuning only and does not change code. For ablation, innovation, and module trial experiments, the idea summary must exist.

## `result.yaml`

`result.yaml` is the machine-readable result file for helpers, tests, registries, and promotion gates. It records:

- U, S, H, ZS, best epoch
- baseline version and baseline H
- delta H
- seed
- decision
- `promotion_decision` and `promote_to`, when applicable
- `evidence.log_artifact_id`
- `evidence.manifest`
- `evidence.manifest_verified`
- `evidence.boundary_audit_passed`
- metric source and metric semantics

`result.yaml` intentionally does not duplicate every artifact field. Promotion resolves the raw artifact as:

```text
artifact_id = result.evidence.log_artifact_id
artifact    = manifest.artifacts[artifact_id]
uri         = artifact.uri
sha256      = artifact.sha256
size_bytes  = artifact.size_bytes
```

If the manifest cannot resolve the artifact id to URI, sha256, and size, the result is not promotable.

## `result.md`

`result.md` is the human-readable interpretation. It is not the machine-parsed source of truth. It explains:

- whether metrics improved
- where the improvement may come from
- what the tradeoff is
- whether the result is `keep`, `reject`, `rejected`, `rerun`, `needs_confirmation`, `blocked`, or `promote`

## Protected Evaluation Semantics

Experiments must not silently change:

- class order
- seen/unseen split
- label mapping
- logits shape
- calibration path
- metric calculation
- output fields consumed by the evaluation script

If the experiment itself changes evaluation, it must be explicitly marked high risk and blocked for dual review by `Interface Checker` and `Quality Checker`. Otherwise, the result cannot be compared with the baseline.

## Promotion Mapping

Promotion reads:

```text
code_commit      = manifest.version.code_commit
run_config       = manifest.reproducibility.config_file
run_command      = manifest.reproducibility.command
run_log_artifact = result.evidence.log_artifact_id
run_log_uri      = manifest.artifacts[run_log_artifact].uri
run_log_sha256   = manifest.artifacts[run_log_artifact].sha256
run_log_size     = manifest.artifacts[run_log_artifact].size_bytes
metrics          = result.metrics
decision         = result.decision
```

`record-result` only records evidence. It does not grant promotion. `promotion_decision: promote` triggers the promotion hard gate, but does not by itself create a formal version.
