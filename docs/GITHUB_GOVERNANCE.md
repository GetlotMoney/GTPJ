# GitHub 项目治理规范

本文件是当前阶段的主规范。目标不是运行实验工作流，而是先把 GitHub 仓库管理干净，
让未来 OpenClaw 或 Codex 工作流都能接入同一个事实来源。

## 当前阶段只管理什么

- baseline 版本：`GTPJ-v1`、`GTPJ-v2`、`GTPJ-v3`。
- Git tag：每个正式 baseline 对应一个永久 tag，例如 `v1`。
- 分支：`main` 长期存在；临时代码实验使用 `dev/...` 或 `exp/...`。
- 模块 trial 命名：`dev/v1-idea-0001-trial-001-short-name` 必须写出来源 baseline。
- trial 快照 tag：`trial/v1/idea-0001/trial-001` 必须写出来源 baseline。
- 配置快照：正式版本配置放在 `config/versions/`，实验副本放在具体实验目录。
- 创意树：所有候选模块必须先进入 `idea_tree/`，有来源、评分和适用版本。
- 证据目录：代码验证、trial 记录、调参、消融和确认实验都放在 `experiments/`。
- 大文件边界：数据集、cache、checkpoint、大日志不进入 Git。

## 当前阶段不强制什么

- 不强制运行完整 OpenClaw 工作流。
- 不强制调用 Codex workflow helper。
- 不强制 Claude/Codex 审查轮次。
- 不把 `review.md` 作为必需文件。
- 不因为旧 workflow 文档存在，就自动执行其中的状态机。

## GitHub 必须保证的事情

1. 每个正式版本都能用 tag 回到对应代码。
2. 每个实验结果都能找到它使用的代码、配置、日志和结论。
3. 每个新模块都能追溯到创意来源，而不是凭空出现。
4. 每个 trial 都能说明它基于哪个 baseline，以及是否可以关闭回到 baseline。
5. 项目目录新增、删除、移动或改职责时，必须同步更新 `docs/PROJECT_STRUCTURE.md`。

## 分支名怎么看

```text
exp/v1-tune-001-topo008
```

表示：基于 `v1` 的第 1 个调参实验。

```text
dev/v1-idea-0003-trial-001-token-router
```

表示：基于 `v1` 的 `IDEA-0003` 第 1 次模块实现尝试。

分支名里的 `v1` 是来源版本，不是最终版本号。这个 trial 如果成功，可以被提升成
下一个正式 baseline，例如 `v2` 或 `v3`。

## 规范文件在哪里

当前 GitHub 项目治理的入口是本文件。具体规范按职责拆到下面这些文件：

| 规范 | 文件 | 什么时候更新 |
|---|---|---|
| GitHub 总规范 | `docs/GITHUB_GOVERNANCE.md` | 改版本、分支、tag、证据边界、创意树总原则时更新。 |
| 项目结构总账本 | `docs/PROJECT_STRUCTURE.md` | 新增、删除、移动、重命名文件或改变文件职责时更新。 |
| 当前项目状态 | `docs/PROJECT_STATUS.md` | 当前正式 baseline、正式结果、下一步发生变化时更新。 |
| 创意树细则 | `docs/workflow/idea_tree_protocol.md` | 改创意来源、评分、跨版本复用、排序和 trial 准入规则时更新。 |
| 创意树使用说明 | `idea_tree/README.md` | 改创意树目录用法、登记流程、人类阅读规则时更新。 |
| 机器可读格式 | `idea_tree/schema.json` | 改 `idea_tree.json` 字段结构时更新。 |
| 代码接口契约 | `docs/workflow/code_interface_contract.md` | 改新增模块的开关、输入输出、shape、loss、eval 约束时更新。 |
| Git 规则 | `docs/workflow/git_policy.md` | 改 `main`、`dev/...`、`exp/...`、tag、push 规则时更新。 |

你刚才说的“不同版本的创意权重不一样”属于创意树细则，所以主更新位置是：

```text
docs/workflow/idea_tree_protocol.md
idea_tree/README.md
idea_tree/schema.json
```

如果这个规则影响整体 GitHub 管理原则，也同步更新本文件。

## 创意树和版本的关系

创意树只保留一棵，不按 `v1`、`v2`、`v3` 各建一棵。

原因是：同一个创意可能对多个版本都有意义，但权重和适用性不同。

```text
idea = 全局创意
global_score = 长期价值
version_scores.v1.score = 对 GTPJ-v1 的当前价值
version_scores.v2.score = 对 GTPJ-v2 的当前价值
version_scores.v3.score = 对 GTPJ-v3 的当前价值
```

规则：

- 当前排序只看 `idea_tree.json.current_version` 对应的版本分数。
- `global_score` 只表示长期价值，不决定当前优先级。
- 新增 `v2` 后，每个保留创意都必须重新写 `version_scores.v2`。
- 不能把 `version_scores.v1` 直接复制成 `version_scores.v2`。
- 缺少当前版本分数的 idea，不能在当前版本下开 trial。
- `source_status: unknown` 或 `unverified` 的 idea 不能开 trial，只能留在 inbox 或 candidate 状态。

## quality_check 是什么

`quality_check.md` 是轻量质量检查记录，不等于旧工作流里的强制审查门。

它只回答：

- 这次记录有没有明确的代码快照或 base version？
- 配置是不是保存到了实验目录？
- 结果能不能追溯到日志？
- 有没有改变 eval、class order、logits shape 或数据划分？
- 如果是模块 trial，关闭开关后能不能回到 baseline？

以后如果正式接入 OpenClaw/Codex 工作流，可以把 `quality_check` 升级成自动化质量门。
在此之前，它只是 GitHub 证据完整性的检查表。

## 从旧 cv 实验工作流可以学习什么

可以保留为未来工作流设计素材的思想：

- 每次实验前后都要有 Git 检查点。
- 代码改动、配置改动、结果记录要分开。
- 新模块必须默认关闭，实验配置再打开。
- 结果要反馈到创意树，而不是只写在日志里。
- 失败实验也要保留，避免重复踩坑。
- 多 runtime 必须共享同一套仓库事实来源。

暂时不接入的部分：

- 固定多轮审查。
- 强制 `ACCEPTED / REJECTED` 决策格式。
- 自动选择下一个实验。
- 自动调用 OpenClaw、Codex 或其他 agent。
- 完整实验状态机。
