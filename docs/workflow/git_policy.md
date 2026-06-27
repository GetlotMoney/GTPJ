# Git 策略

## 永久对象

- `main`：唯一长期分支，保存 owner 明确选择的 active code 和全部实验账本。
- `v1`、`v2`、`v3`：永久 baseline tag，不是分支。
- `trial/v1/idea-xxxx/trial-xxx`：永久 trial 代码快照，必须带 base version。

当前 active baseline 是：

```text
GTPJ-v2
tag: v2
H: 74.29
```

历史 baseline `GTPJ-v1 / tag v1 / H=73.93` 仍永久保留。如果本地或远端 baseline tag
指向的记录与版本账本不一致，说明 tag 错位，必须先修正，不能继续开正式实验。

## 临时分支

临时分支默认从当前 `main` 开出，用来继承最新账本。

```text
dev/v1-idea-0001-trial-001-short-name
dev/v2-idea-0001-trial-001-short-name
exp/v1-tune-001-short-name
exp/v1-ablation-001-short-name
exp/v1-confirm-001-short-name
promote/v1-idea-0001-to-v2
```

分支名里的 `v1`、`v2` 表示代码来源 tag，不表示存在 `v1`、`v2` 分支。

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

一个 `trial/...` tag 只对应一个 module trial 的代码快照，不对应某次
`ATTEMPT-xxx`、某个 H 值或某个 best result。trial 内部的参数尝试、窄消融、
confirmation/rerun 和 debug-fix 只写入 `ATTEMPTS.md`、`attempts/ATTEMPT-xxx/`、
commit hash 和 Warehouse artifact id；不要创建 attempt 级 git tag。

Promote 分支：

```text
promote/<parent-version>-idea-xxxx-to-vX
```

示例：

```text
promote/v1-idea-0003-to-v4
```

## 分支从哪里切

规则：

- 不创建 `v1`、`v2` 这种长期版本分支。
- 不创建 controller branch。
- 不直接在 `main` 上做新模块开发或普通训练实验。
- 默认 `exp/...`、`dev/...`、`promote/...` 都从当前 `main` 切出。
- 历史版本 tune、ablation、confirmation 是例外：当当前 `main` 代码不是目标 `vX` 时，
  可以从 `vX` tag 开 `exp/...` 只运行代码的临时分支；该分支不合并进 `main`，跑完回当前
  `main` 写 `experiments/vX/` 账本并删除临时分支。
- `base-version` 通过 `base_code_tag` 记录代码来源，例如 `v1`。
- 当前 `main` 代码就是目标 base version 时，直接跑。
- 当前 `main` 代码不是目标 base version 时，只恢复代码层到目标 tag，不能恢复账本层。

代码层包括：

```text
model/
tools/
train_*.py
当前运行别名 config/GTPJ_*.yaml
```

账本层包括：

```text
docs/
workflow/
idea_tree/
experiments/
config/versions/
README.md
AGENTS.md
NEXT_ACTIONS.md
```

## 命名怎么看

```text
exp/v1-tune-001-topo008
```

含义：

- `exp`：普通实验分支。
- `v1`：代码来源是 `v1` baseline tag。
- `tune`：调参实验，也可以是 `ablation` 或 `confirm`。
- `001`：该版本该类型第 1 次实验。
- `topo008`：人能读懂的短名。

```text
dev/v1-idea-0003-trial-001-token-router
```

含义：

- `dev`：新模块开发分支，不是稳定版本。
- `v1`：这次 trial 的父代码来源是 `v1` tag。
- `idea-0003`：对应 `idea_tree/ideas/IDEA-0003_*`。
- `trial-001`：这个 idea 的第 1 次实现尝试。
- `token-router`：人能读懂的短名。

```text
trial/v1/idea-0003/trial-001
```

含义：

- `trial`：永久 trial 代码快照。
- `v1`：快照基于 `v1` baseline。
- `idea-0003`：对应的创意。
- `trial-001`：对应的实现尝试。

分支名里的 `v1` 是来源版本，不是最终版本号。成功 trial 可以提升为 `v2`、`v3` 或后续任何新的 baseline tag。

## Tag 规则

- tag 必须打在明确 commit 上，不打在 dirty working tree 上。
- 打 trial tag 前，先把 trial README 的 `code_commit` 填成 `git rev-parse HEAD`。
- 命令使用 `git tag <tag-name> <code_commit>`，不要省略 `<code_commit>`。
- 不为 `ATTEMPT-xxx`、`best_attempt`、单次指标值或调参结果创建 git tag。
  这些证据由 trial 账本、attempt 目录、commit hash 和 Warehouse artifact id 固定。
- 新 `vX` tag 必须打在包含正式版本代码和版本材料的明确 commit 上，而不是打在中间 trial
  commit 或 dirty working tree 上；该 commit 不必是当前 `main` commit。
- 推送后的 `vX` 和 `trial/...` tag 视为不可移动对象。

## 合并和删除

- `exp/...`：实验记录合并回 `main` 后可以删除。
- 失败 `dev/...`：先打 `trial/...` tag，再把失败证据记录回 `main`，然后可以删除。
- 成功 `dev/...`：先打 `trial/...` tag，再通过 `promote/...` 提升为新 `vX`。
- `promote/...`：从当前 `main` 开出，保留最新账本，整理正式版本代码和新增版本账本。
  tag `vX` 打好后，只把账本层回流到 `main`；代码层是否回流由 owner 通过 `activate-version`
  明确决定。账本回流完成后可以删除 promotion 分支。
- 不删除 `main`。
- 不删除已推送的 `vX` baseline tag。
- 不删除已推送的 `trial/...` 永久快照 tag。

## GitHub 远端保护

建议在 GitHub ruleset 中配置：

- `main`：禁止 force push，禁止删除。
- `v*`：保护正式 baseline tag，禁止移动、覆盖或删除。
- `trial/**`：保护 trial 快照 tag，禁止移动、覆盖或删除。

当前仓库初始化阶段如果发现 `v1` tag 错指旧基线，允许做一次性更正；更正后 `v1`
必须指向 `H=73.93` 的 GTPJ-v1 快照，之后按不可移动对象管理。`v2` 是当前 active
baseline tag，也按不可移动对象管理。

Push 规则：

- 不自动 push。只有 owner 明确要求后才 push。
