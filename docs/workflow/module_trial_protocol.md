# Module Trial Protocol

Module trials live under:

```text
experiments/module_trials/
```

The authoritative idea record lives under:

```text
idea_tree/ideas/IDEA-0001_short_name/IDEA.md
```

Required structure:

```text
experiments/module_trials/IDEA-0001_short_name/
|-- IDEA.md              # trial-local pointer to the source idea file
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

- source idea file
- base version
- base code tag
- version-specific idea score
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
