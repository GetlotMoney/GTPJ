# GitHub 项目治理规范

本文件是当前阶段的主规范。目标不是运行实验工作流，而是先把 GitHub 仓库管理干净，
让未来 OpenClaw 或 Codex 工作流都能接入同一个事实来源。

## 当前阶段只管理什么

- baseline 版本：`GTPJ-v1`、`GTPJ-v2`、`GTPJ-v3`。
- Git tag：每个正式 baseline 对应一个永久 tag，例如 `v1`。
- 分支：`main` 长期存在；临时代码实验使用 `dev/...` 或 `exp/...`。
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
