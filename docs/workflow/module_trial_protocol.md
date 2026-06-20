# 模块 Trial 协议

模块 trial 放在：

```text
experiments/module_trials/
```

权威 idea 记录放在：

```text
idea_tree/ideas/IDEA-xxxx_short_name/IDEA.md
```

模块代码改动必须遵守：

```text
docs/workflow/code_interface_contract.md
```

分支和 tag 命名必须带 base version：

```text
code_branch: dev/v1-idea-0001-trial-001-short-name
code_tag: trial/v1/idea-0001/trial-001
```

其中 `v1` 表示这个 trial 从 `v1` baseline tag 切出。
如果 trial 成功，它可以被提升为新的 `v2`、`v3` 或后续版本。

必需结构：

```text
experiments/module_trials/IDEA-xxxx_short_name/
|-- IDEA.md              # trial-local pointer to the source idea file
`-- TRIAL-001_short_name/
    |-- README.md
    |-- implementation.md
    |-- code.diff
    |-- config.yaml
    |-- quality_check.md
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
- quality check decision
- result and final decision

Trial decision：

```text
reject / revise / combine / promote
```
