# Module Trial Protocol

Module trials live under:

```text
experiments/module_trials/
```

Required structure:

```text
experiments/module_trials/IDEA-0001_short_name/
|-- IDEA.md
`-- TRIAL-001_short_name/
    |-- README.md
    |-- implementation.md
    |-- code.diff
    |-- config.yaml
    |-- review.md
    |-- result.md
    `-- logs/
```

Every trial must record:

- base version
- base code tag
- code branch
- code tag
- changed files
- implementation summary
- review decision
- result and final decision

Trial decisions:

```text
reject / revise / combine / promote
```
