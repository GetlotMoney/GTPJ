# Review Gate

Before running an experiment:

1. Check Git status.
2. Confirm the branch starts from the correct version tag.
3. Confirm config changes are scoped to the experiment.
4. Confirm module changes are controlled by an off switch.
5. Confirm logs and result paths are prepared.

Review decision must be one of:

```text
ACCEPTED
REJECTED
```

Risk levels:

- `TUNE-LITE`: config-only tuning.
- `STANDARD`: ablation, dataset transfer, or low-risk switches.
- `STRICT`: new module code, new loss, forward path, data flow, or evaluation changes.

OpenClaw and Codex must write compatible review files.
