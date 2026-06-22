# 版本管理

## Baseline 版本

每个 baseline 命名为：

```text
GTPJ-v1
GTPJ-v2
GTPJ-v3
```

对应 Git tag：

```text
v1
v2
v3
```

注意：`v1`、`v2`、`v3` 是 tag，不是长期分支。仓库只有一个长期分支 `main`。

当前唯一权威基线：

```text
GTPJ-v1
code_tag: v1
H: 73.93
```

每个版本拥有自己的记录目录：

```text
experiments/v1/
experiments/v2/
experiments/v3/
```

## 版本树

版本不是默认串行继承关系。

```text
v1
|-- v2 = parent v1 + 模块A
`-- v3 = parent v1 + 模块B
```

每个正式版本必须在 `experiments/vX/VERSION.md` 中记录：

```text
version: v3
parent_version: v1
parent_tag: v1
code_tag: v3
change_type: add_module / replace_module / remove_module / combo
based_on_trial: trial/v1/idea-0003/trial-001
inherits_code_from: v1
does_not_inherit: v2
```

`parent_version` 表示代码父节点，不表示实验记录父节点。

实验记录是全局账本。`experiments/v2/` 保留在最新 `main` 中，
不表示 `v3` 继承了 `v2` 的代码。

```text
main = 当前主版本代码 + 全部版本账本
```

全局版本树账本：

```text
experiments/VERSION_TREE.md
```

因此，如果当前主版本从 `v2` 切换到 `v3`，而 `v3.parent_version = v1`：

- `model/`、`tools/`、`train_*.py` 等代码层应反映 `v3`；
- `experiments/v2/` 仍然保留，作为 `v2` 历史记录；
- `config/versions/v2.yaml` 仍然保留，作为 `v2` 配置快照；
- `experiments/v3/VERSION.md` 必须明确写 `parent_version: v1` 和 `does_not_inherit: v2`。

## 账本继承实现

从旧父节点提升新版本时，使用双来源：

```text
代码来源 = parent tag + 成功 trial tag
账本来源 = 当前 main
```

不要把从旧 tag 切出的 `dev/...` 分支整体合并成 `main`。那个分支的账本停留在旧时间点，
可能缺少后来的 `experiments/v2/`、`experiments/v3/`、创意树和规范更新。

实现步骤：

```text
当前 main = v3 代码 + 最新账本
目标 v4 = v1 代码 + 模块B

1. 从当前 main 开 dev/v1-idea-xxxx-trial-001-b，继承最新账本。
2. 如果当前 main 代码不是 v1，只恢复代码层到 v1，不恢复账本层。
3. dev 分支只负责证明 v1 + 模块B。
4. 成功后在明确 commit 上打 trial/v1/idea-xxxx/trial-001。
5. 从当前 main 开 promote/v1-idea-xxxx-to-v4。
6. promote 分支保留当前 main 的账本层。
7. promote 分支把代码层切换成 v1 + 模块B。
8. promote 分支把成功 trial 的证据回流到当前账本。
9. promote 分支新增 experiments/v4/ 和 config/versions/v4.yaml。
10. promote 分支更新 experiments/VERSION_TREE.md、全局索引、PROJECT_STATUS、PROJECT_STRUCTURE、README 和 idea_tree current_version。
11. 通过验证后，promote 合并为 main，最终 main commit 打 tag v4。
```

每个 `experiments/vX/VERSION.md` 必须记录：

```text
parent_version:
parent_tag:
ledger_source:
ledger_source_commit:
code_source:
based_on_trial:
```

## 提升规则

只有成功且通过质量检查的 trial 才能成为新的 baseline。

```text
GTPJ-v1 -> IDEA-xxxx -> TRIAL-001 -> promote -> GTPJ-v2
```

不要因为每个小尝试都创建一个新的 `vX`。

`vX` 不要求严格线性继承。`v3` 可以基于 `v1` 的新 trial 产生，
也可以基于 `v2` 的新 trial 产生。

```text
v1
|-- dev/v1-idea-0001-trial-001-a -> promote -> v2
`-- dev/v1-idea-0002-trial-001-b -> promote -> v3
```

规则：

- `main` 永远代表最新稳定项目，不要为了重新基于 `v1` 做实验而把 `main` 回退到 `v1`。
- 想从哪个 baseline 做新模块，就在临时分支名和记录中写清楚 `base_code_tag`。
- 临时分支从当前 `main` 开出，以继承最新账本；必要时只把代码层恢复到目标 baseline tag。
- 分支名里的 `v1`、`v2` 是来源版本；提升后的 `vX` 是新的正式版本。
- 版本提升时，必须在新版本记录中写清楚 `parent_version`。
- 添加模块、替换模块、删除模块或组合模块，只要成为正式框架，就新增一个 `vX`。
- 新 `vX` 不需要继承当前 `main` 的代码；它只继承自己声明的 `parent_version`。
- 新 `vX` 不能删除旧版本账本；旧版本代码靠 tag 保存，旧版本记录靠 `experiments/vX/` 保存。
- 版本继承关系以 `experiments/VERSION_TREE.md` 和 `experiments/vX/VERSION.md` 为准，不以 Git commit parent 推断。

## Promotion 成功标准

`H` 提升是必要证据，但不是唯一标准。

一个 trial 只有同时满足下面条件，才能提升为正式 `vX`：

- 指标有效：记录父版本 baseline H、trial H、delta H、U、S、ZS、best epoch。
- 对照一致：至少同 seed 对照；高风险改动需要重复运行或多 seed 复核。
- 口径一致：class order、seen/unseen split、logits shape、metric calculation 不变。
- 配置可追溯：使用的 config 副本保存在 trial 或新版本目录。
- 日志可追溯：原始日志路径和 Git 内日志副本路径明确。
- 接口干净：输入输出 shape、loss、eval、checkpoint 变化已声明。
- 关闭等价：模块 switch 关闭后回到 `parent_version` 行为。
- 决策完整：`quality_check.md` 的 promotion decision 为 `ACCEPTED`。
- 账本完整：`experiments/vX/VERSION.md`、`experiments/VERSION_TREE.md`、
  `experiments/EXPERIMENT_REGISTRY.md`、`docs/PROJECT_STATUS.md`、`docs/PROJECT_STRUCTURE.md`、
  `README.md` 和 `idea_tree/idea_tree.json` 已同步更新。
- tag 正确：新 `vX` tag 指向最终 `main` commit，trial tag 指向记录的 `code_commit`。

如果只满足 `H` 提升，但无法证明口径一致或关闭等价，结论只能是 `revise`，
不能是 `promote`。
