# Experiment Protocol

Tune, ablation, and confirmation runs belong to a baseline version.

Examples:

```text
experiments/v1/tune/TUNE-001_topo008/
experiments/v1/ablation/ABL-001_disable_jepa/
experiments/v1/confirmation/CONFIRM-001_clean_seed5/
```

Each experiment folder must contain:

```text
README.md
config.yaml
review.md
logs/
```

Rules:

- Do not change model code in tune or ablation branches.
- Put parameter searches only under `tune/`; do not put tuning runs under `confirmation/`.
- Copy the version config into the experiment folder before editing.
- Record command, seed, config, log path, U/S/H/ZS, best epoch, and conclusion.
- Failed runs are evidence and must be recorded.
