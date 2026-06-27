# 创意树协议

`idea_tree/` 是模块创新的 GitHub 轻量事实索引。

完整论文阅读、长版创意树、长推理、创新草稿、失败路线和图示草稿放在本地
`GTPJ_Research`，不进入 GitHub。GitHub 只保存能让实验可追溯的最小证据。

核心原则：创意全局共用一个总库，但选择清单必须按 baseline 版本分开。

总判断规则见 `docs/workflow/WORKFLOW_ROUTER.md`。最重要的是：

```text
实验是为了调/查/验证已有正式 baseline -> experiments/vX，不进 idea_tree。
实验是为了调/查/确认某个 module trial 内部模块 -> experiments/module_trials/.../attempts/ATTEMPT-xxx，不另进 idea_tree。
实验是为了证明一个新方法值得存在 -> idea_tree + module_trials。
```

因此，tune、ablation、confirmation、debug 不会因为有“想法”就自动进入
`idea_tree/`；只有可复用的新模块、新机制、新方法，或可能成为新 baseline 的设计，
才进入创意树。

## 三层分工

```text
GitHub 仓库
= 轻量索引 + 实验账本 + 可复现引用

GTPJ_Research
= 本地完整创意树 + 论文阅读 + 长推理 + 创新草稿

GTPJ_Warehouse
= 原始日志 + checkpoint + 大文件 artifact
```

GitHub idea 记录只写：

```text
idea_id
标题
来源 paper/code/user observation
source_status
global_score
version_scores.v1/v2/vX
hypothesis
implementation_scope
risk
linked_trials
evidence artifact id / research URI
next_action
```

不要把完整论文笔记、长摘录、完整方法复盘、长版草稿或大量失败分支写入 GitHub。

本地完整创意树建议结构：

```text
GTPJ_Research/
├─ papers/
│  └─ PAPER-YYYY-short-name/
│     ├─ paper_meta.yaml
│     ├─ reading_notes.md
│     ├─ source_review.md
│     ├─ code_review.md
│     ├─ extracted_ideas.md
│     └─ figures/
├─ ideas/
│  └─ IDEA-xxxx_short_name/
│     ├─ idea_full.md
│     ├─ mechanism.md
│     ├─ relation_to_v1.md
│     ├─ variants.md
│     ├─ risks.md
│     ├─ experiment_plan.md
│     └─ decision_history.md
├─ versions/
│  ├─ v1/
│  │  ├─ idea_board.md
│  │  ├─ selected_next.md
│  │  └─ rejected_or_deferred.md
│  └─ v2/
│     ├─ idea_board.md
│     └─ transfer_review.md
└─ source_reviews/
   └─ PAPER-YYYY-short-name_review.md
```

论文先进入本地 `GTPJ_Research/papers/PAPER-.../`，形成阅读和来源复核。
只有抽出的机制足够稳定、来源状态明确、并且能映射到 GTPJ 接口时，才在 GitHub
`idea_tree/` 中创建轻量 idea 索引。

```text
同一个 idea
  global_score              长期价值
  version_scores.v1         对 GTPJ-v1 的适配记录
  version_scores.v2         对 GTPJ-v2 的适配记录
```

不要为 `v1`、`v2`、`v3` 分别建立独立创意树；那会导致重复、丢历史、
看不到同一创意在不同框架里的适用性变化。正确做法是：

```text
idea_tree/INDEX.md          全局总创意清单
idea_tree/versions/v1.md    v1 创意选择清单
idea_tree/versions/v2.md    v2 创意选择清单
idea_tree/idea_tree.json    机器可读唯一事实源
```

规则：

- 每个模块 trial 必须有 `idea_id`。
- 没有 `idea_id`，就不能创建 `dev/vX-idea-*` 分支。
- tune 和 ablation 问题不会直接变成 idea 节点。
- `idea_tree/INDEX.md` 是给人读的总创意清单。它必须展示每个创意文件路径和覆盖版本。
  它不直接决定下一步试什么。
- `idea_tree/versions/vX.md` 是给人读的版本选择清单。决定某个版本下一步创新 trial 时，
  只读对应版本文件，例如 `idea_tree/versions/v1.md`。
- `idea_tree/idea_tree.json` 是机器可读的注册表。它必须包含同样的 `idea_id`、
  `idea_dir`、global score 和 per-version scores。
- 每个创意必须有自己的文件：`idea_tree/ideas/IDEA-xxxx_slug/IDEA.md`。
- 每个模块创意都必须记录 `source_type`、`source_ref` 和 `source_status`。
- 合法的 `source_type` 包括 `paper`、`user`、`observation`、`cross_domain`
  和 `hybrid`。
- 如果来源不清楚，设置 `source_status: unknown`。在来源被验证前，或者创意被明确接受为
  local heuristic 前，不要启动 trial。
- 创意排序必须按框架版本区分。`versions/vX.md` 使用
  `version_scores.<version>.score`。不要假设 v1 适配记录适用于 v2。
- `global_score` 不能替代版本分数。它只表示长期价值，不能作为当前实验顺序。
- 允许跨版本复用。当一个创意可能适用于多个版本时，添加多个 `version_scores`
  条目，并说明每个版本需要改变什么。
- 如果当前框架是 `v2`，同一个 idea 可以留在总库里，但 trial 必须来自
  `idea_tree/versions/v2.md`，并使用 `version_scores.v2`。`v1` 适配记录只是证据，
  不是许可。
- 没有当前版本适配记录的 idea，不能在当前版本下开 trial。
- 模块 trial 必须先选择一个 base version。选定的 base version 决定质量检查使用哪个分数、
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
- `version_scores.<version>.stage`：这个创意在该版本下的阶段，例如
  `candidate`、`selected`、`trialing`、`validated`、`rejected`、`blocked`
  或 `not_applicable`。
- `version_scores.<version>.rationale`：为什么这个分数适用于该版本。
- `version_scores.<version>.blockers`：来源、接口、数据或风险阻塞点。

每个版本分数必须独立解释：

```text
v1 score 高：说明它适合当前 v1 代码接口和模块组合。
v2 score 高：说明它适合 v2 代码接口和模块组合。
v1 score 高不代表 v2 score 自动高。
```

当新增新版本时，不要批量复制旧分数。每个 idea 至少要重新判断：

- 当前版本是否还有同样的模块接口；
- 输入输出 shape 是否还兼容；
- 这个创意是否和新版本已有模块重复、互补或冲突；
- 旧实验结果对新版本只是参考，还是可以直接迁移；
- 是否需要改实现方式。

版本选择清单排序：

```text
当前版本适配记录
然后 source_status
然后 risk
然后 cost
```

## 当前版本处理

当前创意树视图由 `idea_tree.json.current_version` 声明。它只决定 idea 排序和
`idea_tree/versions/vX.md` 的生成目标，不代表 `main` active code 已切换。
`main` active code 只能由 owner 明确执行 `activate-version vX` 改变。

选择下一个模块 trial 时：

1. 打开 `idea_tree/versions/<base_version>.md`。
2. 优先看该版本选择清单，不要优先看 `global_score` 或总清单。
3. 打开被选中的 idea 文件，检查来源、blockers 和 transfer notes。
4. 一个 trial 只能选择一个明确的 base version。
5. 把 trial 记录到 `experiments/module_trials/IDEA-xxxx_slug/`。

创建新的框架版本时：

1. 保留旧 idea 节点。
2. 添加 `version_scores.vX`。
3. 为该版本设置 `score`、`applicability`、`rationale` 和 `blockers`。
4. 在 `transfer_notes` 中解释接口或模块变化。
5. 对不能迁移的 idea 写 `not_applicable` 和 `score: 0`。
6. 运行 `python workflow/gtpj_workflow.py set-current-version --version vX`，
   刷新 `idea_tree/INDEX.md` 和 `idea_tree/versions/vX.md`。

如果任何 idea 缺少新的 `version_scores.vX` 条目，helper 会拒绝切换
`current_version`。当一个 idea 明确不能迁移到新框架时，使用
`not_applicable` 和 `score: 0`。

## Trial 准入

只有同时满足下面条件，才能从 idea 创建 module trial：

- 有明确 `idea_id`。
- 有当前 base version 的 `version_scores.<base_version>`。
- idea 全局状态和 `version_scores.<base_version>.stage` 都必须是 `selected`，
  不能直接从 `candidate` 开 trial。
- `source_status` 是 `verified` 或 `local_heuristic`。
- `source_ref` 能说明来源：论文、官方代码、用户明确想法、可复核观察或跨学科来源。
- 如果是 `local_heuristic`，必须写明可复核观察、owner 接受理由和日期。
- `version_scores.<base_version>.rationale` 解释了为什么它适合这个版本。
- `version_scores.<base_version>.applicability` 必须是 `direct` 或 `needs_adaptation`。
- `blockers` 必须为空；只要还有未解决 blocker，就不能开 trial。
- `hypothesis`、`implementation_scope`、`risk` 必须非空。

`source_status: unknown` 或 `unverified` 的 idea 只能留在 `inbox` 或 candidate 记录里，
不能开 trial。

`source_status: unknown` 或 `unverified` 的 idea 也不能进入 `selected` 队列；
当前版本适配分应保持 `0`，适用性应为 `unclear` 或 `not_applicable`，避免来源不明的想法占据执行优先级。
