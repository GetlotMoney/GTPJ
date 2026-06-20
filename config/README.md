# Config Policy

`config/versions/v1.yaml` is the fixed config for `GTPJ-v1`.

Rules:

- `config/versions/vX.yaml` stores the reusable baseline config for version `vX`.
- `experiments/vX/config.yaml` is the archived copy for that version.
- A tune, ablation, or confirmation run must copy the version config into its own experiment folder.
- Do not edit the version config to run a one-off experiment.
- Version configs only contain active baseline fields. Inactive module
  candidates are tracked in `idea_tree/` and must be added only to a trial-local
  config after an `IDEA-xxxx` node is selected.
- Old inert keys and runtime-only switches are not kept in version configs.

Current aliases:

```text
config/VGSR_cub_gzsl.yaml -> same content as config/versions/v1.yaml
```
