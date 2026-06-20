# Git 策略

## 永久对象

- `main`：最新稳定项目文件和轻量记录。
- `v1`、`v2`、`v3`：永久 baseline tag。
- `trial/idea-xxxx/trial-xxx`：永久 trial 代码快照。

## 临时分支

```text
dev/idea-0001-trial-001-short-name
dev/v2-short-name
exp/v1-tune-001-short-name
exp/v1-ablation-001-short-name
exp/v1-confirm-001-short-name
```

规则：

- 不创建 controller branch。
- 不要直接在 `main` 上做新模块开发。
- trial 分支从 baseline tag 切出。
- tune、ablation 和 confirmation 分支从匹配的 baseline tag 切出。
- 失败 trial 的代码通过 trial tag 保留，不合并进 `main`。
- 成功 trial 的代码可以提升到 `main`，并打成新的 `vX` tag。

Push 规则：

- 不自动 push。只有 owner 明确要求后才 push。
