# 创意树协议

`idea_tree/` 是模块创新的严格来源。

规则：

- 每个模块 trial 必须有 `idea_id`。
- 没有 `idea_id`，就不能创建 `dev/idea-*` 分支。
- tune 和 ablation 问题不会直接变成 idea 节点。
- `idea_tree/INDEX.md` 是给人读的总索引。它必须展示每个创意文件路径和当前版本分数。
  决定下一步试什么时，先读这个文件。
- `idea_tree/idea_tree.json` 是机器可读的注册表。它必须包含同样的 `idea_id`、
  `idea_dir`、global score 和 per-version scores。
- 每个创意必须有自己的文件：`idea_tree/ideas/IDEA-xxxx_slug/IDEA.md`。
- 每个模块创意都必须记录 `source_type`、`source_ref` 和 `source_status`。
- 合法的 `source_type` 包括 `paper`、`user`、`observation`、`cross_domain`
  和 `hybrid`。
- 如果来源不清楚，设置 `source_status: unknown`。在来源被验证前，或者创意被明确接受为
  local heuristic 前，不要启动 trial。
- 创意排序必须按框架版本区分。当前 baseline version 使用
  `version_scores.<version>.score`。不要假设 v1 分数适用于 v2。
- 允许跨版本复用。当一个创意可能适用于多个版本时，添加多个 `version_scores`
  条目，并说明每个版本需要改变什么。
- 如果当前框架是 `v2`，同一个 idea 可以留在树里，但 trial 必须使用
  `version_scores.v2`。`v1` 分数只是证据，不是许可。
- 模块 trial 必须先选择一个 base version。选定的 base version 决定 review 使用哪个分数、
  风险和约束。
- 被拒绝的 idea 也留在树里，带着证据和较低优先级。
- 旧实验结果不迁移。
- 旧 idea 可以重写为新的 `candidate` 节点。

必填字段定义在 `idea_tree/schema.json`。

## 分数字段

使用 0-100 分：

- `global_score`：这个创意在整个项目中的长期价值。
- `version_scores.<version>.score`：它对某个具体框架版本的优先级。
- `version_scores.<version>.applicability`：`direct`、`needs_adaptation`、
  `unclear` 或 `not_applicable`。
- `version_scores.<version>.rationale`：为什么这个分数适用于该版本。
- `version_scores.<version>.blockers`：来源、接口、数据或风险阻塞点。

当前工作窗口排序：

```text
当前版本分数
然后 source_status
然后 risk
然后 cost
```

## 当前版本处理

当前激活框架由 `idea_tree.json.current_version` 声明。

选择下一个模块 trial 时：

1. 打开 `idea_tree/INDEX.md`。
2. 优先看当前版本分数，不要优先看 `global_score`。
3. 打开被选中的 idea 文件，检查来源、blockers 和 transfer notes。
4. 一个 trial 只能选择一个明确的 base version。
5. 把 trial 记录到 `experiments/module_trials/IDEA-xxxx_slug/`。

创建新的框架版本时：

1. 保留旧 idea 节点。
2. 添加 `version_scores.vX`。
3. 为该版本设置 `applicability`。
4. 在 `transfer_notes` 中解释接口或模块变化。
5. 运行 `python workflow/gtpj_workflow.py set-current-version --version vX`。

如果任何 idea 缺少新的 `version_scores.vX` 条目，helper 会拒绝切换
`current_version`。当一个 idea 明确不能迁移到新框架时，使用
`not_applicable` 和 `score: 0`。
