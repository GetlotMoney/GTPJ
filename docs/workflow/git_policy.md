# Git 策略

## 永久对象

- `main`：最新稳定项目文件和轻量记录。
- `v1`、`v2`、`v3`：永久 baseline tag。
- `trial/v1/idea-xxxx/trial-xxx`：永久 trial 代码快照，必须带 base version。

## 临时分支

```text
dev/v1-idea-0001-trial-001-short-name
dev/v2-idea-0001-trial-001-short-name
exp/v1-tune-001-short-name
exp/v1-ablation-001-short-name
exp/v1-confirm-001-short-name
```

## 命名规范

普通实验分支：

```text
exp/<base-version>-<kind>-<number>-<short-name>
```

示例：

```text
exp/v1-tune-001-topo008
exp/v1-ablation-001-disable-jepa
exp/v1-confirm-001-clean-seed5
```

模块 trial 开发分支：

```text
dev/<base-version>-idea-xxxx-trial-xxx-<short-name>
```

示例：

```text
dev/v1-idea-0003-trial-001-token-router
dev/v2-idea-0003-trial-002-token-router
```

模块 trial 永久快照 tag：

```text
trial/<base-version>/idea-xxxx/trial-xxx
```

示例：

```text
trial/v1/idea-0003/trial-001
trial/v2/idea-0003/trial-002
```

规则：

- 不创建 controller branch。
- 不要直接在 `main` 上做新模块开发。
- trial 分支从 baseline tag 切出。
- trial 分支名必须带 base version，格式为
  `dev/<base-version>-idea-xxxx-trial-xxx-short-name`。
- tune、ablation 和 confirmation 分支从匹配的 baseline tag 切出。
- 失败 trial 的代码通过 trial tag 保留，不合并进 `main`。
- 成功 trial 的代码可以提升为新的 `vX` tag。新 `vX` 必须记录父节点，
  不默认继承当前 `main` 代码。
- 从旧父节点提升新 `vX` 时，必须从当前 `main` 开 `promote/...` 分支，
  保留账本层，只替换或移植代码层。

## 命名怎么看

```text
dev/v1-idea-0003-trial-001-token-router
```

含义：

- `dev`：这是新模块开发分支，不是稳定版本。
- `v1`：这次 trial 基于 `v1` baseline tag 切出。
- `idea-0003`：对应 `idea_tree/ideas/IDEA-0003_*`。
- `trial-001`：这个 idea 的第 1 次实现尝试。
- `token-router`：人能读懂的简短名字。

```text
trial/v1/idea-0003/trial-001
```

含义：

- `trial`：永久 trial 代码快照。
- `v1`：快照基于 `v1` baseline。
- `idea-0003`：对应的创意。
- `trial-001`：对应的实现尝试。

分支名里的 `v1` 表示来源版本，不表示它成功后一定变成 `v2`。
如果 `dev/v1-idea-0003-trial-001-token-router` 成功，它可能被提升为 `v2`、
`v3` 或后续任何新的 baseline tag，具体取决于当时下一个正式版本号。

## 合并和删除

- `exp/...` 分支：实验记录合并回 `main` 后可以删除。
- 成功的 `dev/...` 分支：先打 trial tag，再提升为新 `vX`。
  提升必须通过 `promote/...` 分支完成；`promote/...` 从当前 `main` 开出，
  因此继承最新账本。然后只把代码层切换到新 `vX`。
  全局账本层必须保留所有历史版本记录。
  打好新 `vX` tag 后可以删除 `dev/...` 分支。
- 失败的 `dev/...` 分支：先打 `trial/<base-version>/idea-xxxx/trial-xxx` tag，
  再把失败证据记录回 `main`，然后可以删除分支。
- 不删除 `main`。
- 不删除 `vX` baseline tag。
- 不删除 `trial/...` 永久快照 tag。

## Promote 分支

当 trial 成功并准备成为正式版本时，使用：

```text
promote/<parent-version>-idea-xxxx-to-vX
```

示例：

```text
promote/v1-idea-0003-to-v4
```

含义：

- `promote`：正式提升分支，不是实验分支。
- `v1`：代码父节点。
- `idea-0003`：来自哪个创意 trial。
- `v4`：准备生成的新 baseline。

`promote/...` 必须从当前 `main` 切出，这样它继承最新账本；
代码层再从 parent tag 和 trial tag 移植。

Push 规则：

- 不自动 push。只有 owner 明确要求后才 push。
