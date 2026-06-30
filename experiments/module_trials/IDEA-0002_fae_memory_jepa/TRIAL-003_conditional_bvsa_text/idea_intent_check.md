# Review 0: Idea / Intent

```text
decision: allow
agent_instance_type: coordinator_role_only
activation_mode: role_only_code_preparation
```

## Intent

Owner request on 2026-06-29:

```text
Based on v3, let all_text_cond enter BVSA and replace the original all_text.
```

## Interpretation

This is a new forward-path hypothesis based on `GTPJ-v3`. It keeps IDEA-0002 as the parent idea family but opens a new trial because the BVSA text input semantics change.

## Boundary

- This is not a v3 baseline rewrite.
- `config/versions/v3.yaml` remains frozen.
- No training result exists yet.
