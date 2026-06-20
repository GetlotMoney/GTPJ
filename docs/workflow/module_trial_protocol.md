# 模块 Trial 协议

模块 trial 放在：

```text
experiments/module_trials/
```

权威 idea 记录放在：

```text
idea_tree/ideas/IDEA-0001_short_name/IDEA.md
```

模块代码改动必须遵守：

```text
docs/workflow/code_interface_contract.md
```

必需结构：

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

每个 trial 必须记录：

- source idea file
- base version
- base code tag
- version-specific idea score
- insertion point
- input contract
- output contract
- shape invariants
- config switch and baseline-off path
- 如果触碰 loss/evaluation，记录对应 contract
- 最低验证证据
- code branch
- code tag
- changed files
- implementation summary
- review decision
- result and final decision

Trial decision：

```text
reject / revise / combine / promote
```
