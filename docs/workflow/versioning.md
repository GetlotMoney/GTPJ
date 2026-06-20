# Versioning

## Baseline Versions

Each baseline is named:

```text
GTPJ-v1
GTPJ-v2
GTPJ-v3
```

The matching Git tags are:

```text
v1
v2
v3
```

Each version owns its records:

```text
experiments/v1/
experiments/v2/
experiments/v3/
```

## Promotion

Only a successful reviewed trial can become a new baseline.

```text
IDEA-0001 -> TRIAL-001 -> promote -> GTPJ-v2
```

Do not create a new `vX` for every small attempt.
