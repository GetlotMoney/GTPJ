# GitHub 项目治理规范

本文件是当前阶段的主规范。目标不是运行实验工作流，而是先把 GitHub 仓库管理干净，
让未来 OpenClaw 或 Codex 工作流都能接入同一个事实来源。

## 当前唯一权威基线

当前仓库只承认一个正式基线：

```text
GTPJ-v1
code_tag: v1
baseline H: 73.93
长期分支: main
```

`main` 是唯一长期分支。`v1` 是 tag，不是分支。

早期错误指向旧结果的 `v1` tag 不再作为有效基线。当前初始化阶段允许一次性把
`v1` 修正到 `H=73.93` 的 GTPJ-v1 快照；修正后 `v1` 按永久 tag 管理，不再移动。

## 当前阶段只管理什么

- baseline 版本：`GTPJ-v1`、`GTPJ-v2`、`GTPJ-v3`。
- Git tag：每个正式 baseline 对应一个永久 tag，例如 `v1`。
- 分支：只有 `main` 长期存在；临时代码实验使用 `dev/...`、`exp/...` 或 `promote/...`。
- 模块 trial 命名：`dev/v1-idea-0001-trial-001-short-name` 必须写出来源 baseline。
- trial 快照 tag：`trial/v1/idea-0001/trial-001` 必须写出来源 baseline。
- 配置快照：正式版本配置放在 `config/versions/`，实验副本放在具体实验目录。
- 创意树：所有候选模块必须先进入 `idea_tree/`，有来源、评分和适用版本。
- 证据目录：代码验证、trial 记录、调参、消融和确认实验都放在 `experiments/`。
- 大文件边界：数据集、cache、checkpoint、大日志不进入 Git。

## GitHub 轻量边界

GitHub 只回答：

```text
怎么复现？
结果是什么？
为什么保留、放弃、重跑或提升？
是否满足 promotion / activate-version / set-current-version 的治理边界？
```

GitHub 保存：

```text
code
config
schema
manifest.yaml
result.yaml
result.md
quality_check.md
agent_summary.md
EXPERIMENT_REGISTRY
VERSION_TREE
轻量 idea index
agent contracts
```

GitHub 不保存：

```text
raw logs
checkpoint
generated figures
feature cache
完整论文阅读材料
完整创意树
```

这些外部资产分别放在：

```text
GTPJ_Research
GTPJ_Warehouse
```

GitHub 使用 `warehouse://`、`research://` URI 和 sha256/size 引用它们。
本地真实路径只写入 ignored 的 `.gtpj/local_paths.yaml`。

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
5. 稳定入口、目录类型或文件职责变化时，必须同步更新 `docs/PROJECT_STRUCTURE.md`；
   新增普通实验、idea、trial 的具体实例只更新对应账本或索引，除非结构模式也变化。

## 版本树和全局账本

GTPJ 使用版本树，不使用默认串行版本链。

```text
v1
|-- v2 = parent v1 + 模块A
`-- v3 = parent v1 + 模块B
```

这表示 `v2` 和 `v3` 可以是兄弟版本，不要求 `v3` 继承 `v2`。

每个正式版本都必须记录父节点：

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

代码继承和实验记录保存是两件事：

```text
代码层：model/、tools/、train_*.py、当前运行 config
账本层：docs/、idea_tree/、experiments/、config/versions/
```

`main` 的含义是：

```text
main = owner 明确选择的 active code + 全部历史版本的全局账本
```

promotion 只表示新 baseline 被正式保存，不表示 `main` 当前代码自动切到该版本。
`main` 当前代码是否切到 `vX`，必须由 owner 在实验完成后明确执行 `activate-version vX`。

全局版本树账本放在：

```text
experiments/VERSION_TREE.md
```

所以当 `main` 当前代码切到 `v3` 时，仓库里仍然保留：

```text
experiments/v1/
experiments/v2/
experiments/v3/
config/versions/v1.yaml
config/versions/v2.yaml
config/versions/v3.yaml
```

这些旧目录是历史账本，不表示 `v3` 继承了 `v2` 的代码。

如果 `v3.parent_version = v1`，那么：

```text
v3 代码继承 v1
v3 不继承 v2 代码
experiments/v2/ 仍然保留在 main，作为 v2 历史记录
```

## 从旧父节点提升新正式版本

当当前 `main` 已经包含较新的账本，但新版本代码要从旧父节点产生时，必须按“两条来源”
处理：

```text
代码来源：parent_version 对应的 tag，例如 v1
账本来源：提升时的当前 main
```

必须从当前 `main` 开临时分支，必要时只把代码层恢复到旧父节点。
禁止把旧父节点状态下的完整工作树或旧 `dev/...` 分支整体变成 `main`，因为那会把 `docs/`、`experiments/`、
`idea_tree/`、`config/versions/` 等全局账本回退到旧状态。

正确提升流程：

```text
1. 从当前 main 开 dev 分支，继承最新账本。
2. 如果 parent_version 不是当前 main 代码，只恢复代码层到 parent tag，不恢复账本层。
3. trial 成功后，在明确 code_commit 上打 trial/<parent-version>/idea-xxxx/trial-xxx 快照 tag。
4. 回到当前 main，开 promote 分支。
5. 在 promote 分支中保留当前 main 的账本层。
6. 把成功 trial 的证据目录回流到当前账本。
7. 只把代码层切换或移植为 parent tag + 成功 trial 的代码。
8. 新增 experiments/vX/ 和 config/versions/vX.yaml。
9. 更新 VERSION_TREE、EXPERIMENT_REGISTRY、PROJECT_STATUS、PROJECT_STRUCTURE、README 和 idea_tree current_version。
10. 验证通过后，在 promote 分支的版本代码 commit 上打 vX tag。
11. 回到当前 main，只把版本账本层回流到 main。
12. main 当前代码保持原 active version，除非 owner 明确执行 activate-version vX。
```

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
AGENTS.md
NEXT_ACTIONS.md
README.md
```

每个新版本必须记录：

```text
parent_version: v1
parent_tag: v1
ledger_source: current main
ledger_source_commit: <提升开始时的 main commit>
code_source: parent tag + trial tag
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

## 命名怎么看

```text
exp/v1-tune-001-topo008
```

含义：

- `exp`：普通实验分支。
- `v1`：基于 `v1` baseline tag。
- `tune`：调参实验。也可以是 `ablation` 或 `confirm`。
- `001`：该类型第 1 次实验。
- `topo008`：人能读懂的简短名字。

```text
dev/v1-idea-0003-trial-001-token-router
```

含义：

- `dev`：新模块开发分支，不是稳定版本。
- `v1`：这次 trial 的父代码来源是 `v1` baseline tag；`dev/...` 分支仍从当前 `main`
  开出，必要时只恢复代码层。
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

分支名里的 `v1` 是来源版本，不是最终版本号。这个 trial 如果成功，可以被提升成
下一个正式 baseline，例如 `v2` 或 `v3`。

## 合并和删除

普通实验分支：

- `exp/...` 分支只承载 tune、ablation、confirmation 的实验记录。
- 当前 `main` 代码就是目标 `vX` 时，`exp/...` 从当前 `main` 开出；分支名里的 `v1` 是
  `base_code_tag`。
- 历史版本 tune、ablation、confirmation 可以从 `vX` tag 开只运行代码的 `exp/...`
  临时分支；该分支不合并进 `main`。
- 历史版本跑完后，回当前 `main` 只把 README、config、日志路径、结果和结论写入
  `experiments/vX/` 账本。
- 实验记录入账后，可以删除这个 `exp/...` 临时分支。

成功的模块 trial：

- 成功标准不是只看一次 `H` 上涨，而是指标有效、代码干净、实验口径一致。
- 成功 trial 可以提升为新的 `vX`，但必须先写清 `parent_version`。
- 如果新 `vX` 的父节点不是当前 `main` 代码，提升时必须从当前 `main` 开 promote 分支，
  只切换代码层，不能删除或回退全局账本层。
- `experiments/v1/`、`experiments/v2/` 等历史记录目录必须继续保留在 `main`。
- 成功 trial 的轻量证据目录、artifact 指针、quality_check、result 和 code.diff 必须回流到当前 `main` 账本；raw logs、checkpoint 和 generated figures 留在 Warehouse。
- 在包含正式版本代码和版本材料的明确 commit 上打新的 baseline tag，例如 `v2` 或 `v3`；
  这个 commit 不必是当前 `main` commit。
- `main` 代码是否切到新 baseline，必须由 owner 明确执行 `activate-version` 决定。
- 新 baseline tag 打好后，可以删除对应 `dev/...` 分支。

Promotion 硬门：

- `H` 相比父版本有明确提升，且记录 baseline H、trial H 和 delta H。
- 不能只凭一次偶然结果；至少要记录同 seed 对照，必要时补充多 seed 或重复运行。
- `U`、`S`、`ZS` 没有出现不可接受退化；如果有退化，必须解释为什么仍然接受。
- 训练命令、seed、配置副本、日志路径、best epoch 和结果表完整。
- evaluation 口径没有改变，包括 class order、seen/unseen split、logits shape 和 metric calculation。
- 模块开关关闭时可以回到 `parent_version` 行为。
- `quality_check.md` 的 `promotion_decision` 必须是 `promote`，并通过
  `docs/workflow/promotion.md` 的自动 promotion gate。
- `experiments/vX/VERSION.md`、`experiments/VERSION_TREE.md`、`EXPERIMENT_REGISTRY.md`
  都已经更新。

只有同时满足上面条件，实验或 trial 才能提升为正式 `vX`。

失败的模块 trial：

- 失败代码不合并进 `main`。
- 先打永久快照 tag，例如 `trial/v1/idea-0003/trial-001`。
- 把失败证据、日志路径、结论合并回 `main`。
- 快照 tag 和证据都保存后，可以删除对应 `dev/...` 分支。

永久保留：

- 不删除 `main`。
- 不删除 `vX` baseline tag。
- 不删除 `trial/...` 永久快照 tag。

## GitHub 保护规则

GitHub 远端应设置保护规则：

- 保护 `main`，禁止 force push。
- 禁止删除 `main`。
- 保护 `v*` tag，禁止移动、覆盖或删除。
- 保护 `trial/**` tag，禁止移动、覆盖或删除。
- 只有 owner 明确要求时才允许 push。
- 正式 baseline tag 和 trial tag 推送后视为不可变对象。

如果 GitHub ruleset 暂时没有配置，也必须在人工操作中遵守这些规则。

例外：当前初始化阶段已经确认唯一基线是 `H=73.93`，如果远端 `v1` tag 仍指向旧结果，
允许在 owner 明确要求推送时执行一次强制修正。修正完成后 `v1` 不再移动。

## 规范文件在哪里

当前 GitHub 项目治理的入口是本文件。具体规范按职责拆到下面这些文件：

| 规范 | 文件 | 什么时候更新 |
|---|---|---|
| GitHub 总规范 | `docs/GITHUB_GOVERNANCE.md` | 改版本、分支、tag、证据边界、创意树总原则时更新。 |
| 项目结构总账本 | `docs/PROJECT_STRUCTURE.md` | 改稳定入口、目录类型、关键文件或职责时更新；动态实例只更新对应索引。 |
| 当前项目状态 | `docs/PROJECT_STATUS.md` | 当前正式 baseline、正式结果、下一步发生变化时更新。 |
| 版本树账本 | `experiments/VERSION_TREE.md` | 新增正式 `vX`、改变父节点关系或主版本时更新。 |
| 创意树细则 | `docs/workflow/idea_tree_protocol.md` | 改创意来源、评分、跨版本复用、排序和 trial 准入规则时更新。 |
| 创意树使用说明 | `idea_tree/README.md` | 改创意树目录用法、登记流程、人类阅读规则时更新。 |
| 机器可读格式 | `idea_tree/schema.json` | 改 `idea_tree.json` 字段结构时更新。 |
| 代码接口契约 | `docs/workflow/code_interface_contract.md` | 改新增模块的开关、输入输出、shape、loss、eval 约束时更新。 |
| Git 规则 | `docs/workflow/git_policy.md` | 改 `main`、`dev/...`、`exp/...`、tag、push 规则时更新。 |
| 普通实验协议 | `docs/workflow/experiment_protocol.md` | 改 tune、ablation、confirmation 流程、历史版本临时分支、调参表或消融接口检查时更新。 |
| 自动 promotion | `docs/workflow/promotion.md` | 改 `promotion_decision: promote`、硬门、本地 tag、版本材料、账本回流、main active code 或不自动 push 边界时更新。 |
| agent 编排 | `docs/workflow/agent_orchestration.md` | 改长期 agent 角色、文件夹结构、多 agent 编排、GPU 串行或 skill 同步规则时更新。 |
| 进度看板协议 | `docs/workflow/progress_dashboard.md` | 改本地网页看板、`.gtpj_runtime/` 状态文件、agent 进度、GPU/Runner 展示或只读边界时更新。 |

## 本地 skill 和 GitHub 的同步

GitHub 文档是 GTPJ workflow 规范的权威来源。本地 Codex skill 只是执行副本：

```text
C:\Users\Administrator\.codex\skills\gtpj-workflow
```

修改 workflow 规范时必须同步两边：

1. 先更新 GitHub 文档。
2. 再同步更新本地 `gtpj-workflow` skill 的 `SKILL.md` 或 `references/`。
3. 运行 skill 校验。
4. 运行仓库验证。
5. 用户明确要求后再提交推送。

如果 GitHub 文档和本地 skill 冲突，以 GitHub 文档为准。

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
version_scores.v1 = 对 GTPJ-v1 的适配记录
version_scores.v2 = 对 GTPJ-v2 的适配记录
version_scores.v3 = 对 GTPJ-v3 的适配记录
```

规则：

- 版本选择清单只看对应 `version_scores.vX`，例如 `versions/v1.md` 看 `version_scores.v1`。
- `global_score` 只表示长期价值，不决定当前优先级。
- `idea_tree/INDEX.md` 是总创意清单；`idea_tree/versions/vX.md` 是某个版本的选择清单。
- 创新 trial 只读取对应 base version 的 `idea_tree/versions/vX.md`，避免每次读取完整总表。
- 新增 `v2` 后，每个保留创意都必须重新写 `version_scores.v2`。
- 不能把 `version_scores.v1` 直接复制成 `version_scores.v2`。
- 缺少当前版本适配记录的 idea，不能在当前版本下开 trial。
- `source_status: unknown` 或 `unverified` 的 idea 不能开 trial，只能留在 inbox 或 candidate 状态。

## quality_check 是什么

普通实验的 `quality_check.md` 是轻量质量检查记录，不等于旧工作流里的强制审查门。

它只回答：

- 这次记录有没有明确的代码快照或 base version？
- 配置是不是保存到了实验目录？
- 结果能不能追溯到日志？
- 有没有改变 eval、class order、logits shape 或数据划分？
- 如果是模块 trial，关闭开关后能不能回到 baseline？

但 baseline promotion 是强制门。任何 trial、ablation 或 tuned configuration 想成为正式
`vX`，必须通过 `docs/workflow/promotion.md` 的自动 promotion gate，不能只看一次 `H` 提升。

以后如果正式接入 OpenClaw/Codex 工作流，可以把 `quality_check` 升级成自动化质量门。
在此之前，普通实验的 `quality_check` 是 GitHub 证据完整性的检查表；
promotion 的 `quality_check` 是正式版本准入门。当实验记录明确写
`promotion_decision: promote` 且硬门全部通过时，Coordinator 可以自动创建本地新版本材料和本地 tag，
并把版本账本回流到 `main`；但不自动切换 `main` 当前代码，也不自动 push GitHub。

## agent_summary 是什么

`agent_summary.md` 是 agent 工作凭证，不是完整聊天记录。它记录：

- 本次实验启用了哪些 agents；
- 哪些 agents 被禁用；
- 每个 agent 检查了哪些输入；
- 发现了哪些 blocking / non-blocking issue；
- 最终决策引用了哪些 artifact、commit 和质量检查。

长报告、完整日志分析和 runner 细节放 Warehouse；GitHub 只保存摘要和 artifact id。具体规则见
`docs/workflow/agent_report_policy.md`。

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
- 旧工作流的固定 `ACCEPTED / REJECTED` 决策格式。
- 自动选择下一个实验。
- 自动调用 OpenClaw、Codex 或其他 agent。
- 完整实验状态机。
