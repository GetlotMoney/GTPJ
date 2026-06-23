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

其中 `v1` 表示这个 trial 的代码来源是 `v1` baseline tag。临时分支仍从当前
`main` 开出，以继承最新账本；如果当前 `main` 代码不是 `v1`，只恢复代码层到
`v1`，不要恢复账本层。
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
- result
- `trial_decision`
- `promotion_decision`

`trial_decision`：

```text
reject / revise / combine / promote
```

`promotion_decision`：

```text
not_applicable / promote / blocked / rejected
```

只有 `trial_decision: promote` 且 `promotion_decision: promote` 时，trial 才会进入
`docs/workflow/promotion.md` 的自动 promotion gate。
`H` 提升但证据不完整时，必须写 `revise`、`blocked` 或 `rejected`，不能写 `promote`。

Promotion 必填证据：

- parent version / parent tag；
- trial code tag；
- trial tag 指向 README 中记录的 code_commit；
- baseline H、trial H、delta H；
- U/S/ZS、best epoch、seed；
- config 副本路径；
- 原始日志路径和 Git 内日志副本路径；
- class order、seen/unseen split、logits shape、metric calculation 未改变的说明；
- switch-off 等价检查；
- `experiments/vX/VERSION.md`、`experiments/VERSION_TREE.md`、`docs/PROJECT_STRUCTURE.md`
  和 `idea_tree/idea_tree.json` 更新记录。
