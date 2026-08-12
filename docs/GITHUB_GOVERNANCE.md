# GitHub 项目治理规范

本文件是 GitHub 控制面主规范。目标是把 GitHub 仓库管理成可复现、可审计、可回滚的事实源，
让 OpenClaw、Codex 或其他 runtime 都接入同一套 workflow 事实来源。

当前核心 workflow 已经生效；任务路由、启动卡、pre-run freeze、artifact 边界、结果账本、质量门、
agent 凭证和 promotion gate 以 `docs/workflow/` 中的规范为准。

## 当前权威基线

当前 active mainline code：

```text
GTPJ-v5
code_tag: v5
best_observed_H: 74.54
confirmed_H: 74.44
confirmation_status: owner_activated_provisional
status: owner_activated_provisional
总管理分支: main
框架代码分支: framework/v5
```

当前 confirmed reference：

```text
v3 CONFIRM-001 local-v3-054
code_tag: v3
confirmed_H: 74.47
H_mean: 74.45
historical_tag: v4 (legacy config-only tag; not a formal framework version)
```

历史 baseline / version tags：

```text
GTPJ-v1
code_tag: v1
baseline H: 73.93

GTPJ-v2 / tag v2
best_observed_H: 74.29
confirmed_H: pending

GTPJ-v3 / tag v3
best_observed_H: 74.27
confirmed_H: pending

GTPJ-v4 / tag v4
legacy config-only reference from v3 confirmation, not a future tune-only promotion template
```

`main` 是总管理长期分支；每个正式框架用 `framework/vX-template-vN` 和母版 Tag 固定一份只读代码母版。旧 `framework/v1`、`framework/v2`、`framework/v3`、`framework/v5` 只作历史来源回查；`v4` 不是正式框架，所以没有正式母版。

早期错误指向旧结果的 `v1` tag 不再作为有效基线。`v1` 修正到 `H=73.93`
后按永久 tag 管理，不再移动。`GTPJ-v5` 是 owner 选择的 active mainline，用于后续动态路由与调参；它仍是 provisional active，不代表已经超过 confirmed reference。
只调参数不能创建新的 formal method version；历史 `v4` 仅作为 legacy config-only tag 记录。

## 当前阶段只管理什么

- baseline / active 版本记录：`GTPJ-v1`、`GTPJ-v2`、`GTPJ-v3`、legacy `GTPJ-v4`、active provisional `GTPJ-v5`。
- Git tag：每个正式 baseline 对应一个永久 tag，例如 `v1`。
- 分支：`main` 管总索引和规范；`framework/vX-template-vN` 固定只读母版；临时实验从 `TEMPLATE.yaml` 登记的准确 commit 开 `exp/vX/<type>/...`，旧 `dev/...` 只作历史兼容。
- 同级正式框架注册表、历史来源连线与四类实验：以 `docs/workflow/FRAMEWORK_EXPERIMENT_STANDARD.md` 和 `experiments/vX/framework.yaml` 为准。
- 旧模块 trial 命名和 `trial/...` 快照 tag 只作历史追溯，不再用于新实验。
- 配置快照：正式版本配置放在 `config/versions/`，实验副本放在具体实验目录。
- 创意树：所有候选模块必须先进入 `idea_tree/`，有来源、评分和适用版本。
- 证据目录：代码验证、trial 记录、调参、消融和确认实验都放在 `experiments/`。
- 大文件边界：数据集、cache、checkpoint、大日志不进入 Git。

## GitHub 轻量事实索引

GitHub 不是只记录来源，而是记录“轻量事实索引”：最小但可复现、可审计、可追溯的事实。
完整论文笔记、长创意树、长推理、草稿和原始运行资产放在本地外部目录。

三层分工：

```text
GitHub 仓库
= 轻量索引 + 实验账本 + 可复现引用

GTPJ_Research
= 本地完整创意树 + 论文阅读 + 长推理 + 创新草稿

GTPJ_Warehouse
= 原始日志 + checkpoint + 大文件 artifact
```

GitHub 负责回答：

```text
怎么复现？
结果是什么？
为什么保留、放弃、重跑或提升？
是否满足 promotion / activate-version / set-current-version 的治理边界？
```

GitHub 保存轻量事实：

```text
code
config
schema
manifest.yaml
result.yaml
result.md
quality_check.md
idea_intent_check.md
interface_precheck.md
review_round_1.md
review_round_2.md
agent_summary.md
EXPERIMENT_REGISTRY
VERSION_TREE
轻量 idea index
agent contracts
```

GitHub 中的 `idea_tree/` 保存：

```text
idea_id
标题
来源 paper/code/user observation
source_status
global_score
core_summary
version_scores.v1/v2/vX
hypothesis
implementation_scope
risk
linked_trials
evidence artifact id / research URI
```

GitHub 不保存：

```text
raw logs
checkpoint
generated figures
feature cache
完整论文阅读材料
完整创意树
长推理
创新草稿
```

这些外部资产分别放在：

```text
GTPJ_Research
GTPJ_Warehouse
```

GitHub 使用 `warehouse://`、`research://` URI 和 sha256/size 引用它们。
本地真实路径只写入 ignored 的 `.gtpj/local_paths.yaml`。

联动更新原则：

- GitHub 和本地不是机械每次同时写；是否联动由 `docs/workflow/core/WORKFLOW_ROUTER.md` 分类决定。
- 论文阅读、来源复核、新 idea 和长推理先写 `GTPJ_Research`，再把轻量事实和 `research://` 引用写入 GitHub。
- 训练日志、checkpoint 和大文件先写 `GTPJ_Warehouse`，再把 `warehouse://`、sha256、size、指标摘要写入 GitHub。
- 如果某次结果改变 idea 状态、version score、trial 结论、promotion 判断、evidence 或版本适配说明，
  必须同步更新 Research 长版记录和 GitHub 轻量索引。具体下一步动作只写入 queue、trial/attempt、
  task card 或 result/quality 文件，不写入全局 idea 总表。
- 如果某次任务不需要联动，启动卡和收尾说明必须写出 skip reason。

## Runtime 不强制什么

- 不强制绑定某一个 runtime；OpenClaw、Codex 或手工执行都必须遵循同一套 workflow 事实源。
- 不要求纯解释、只读检查或不产生结构性变化的任务调用 `workflow/gtpj_workflow.py`。
- 不强制每次任务都有固定数量的 Claude/Codex 审查轮次；是否启用真实多 agents 由 `agent_orchestration.md` 决定。
- 不把 `review.md` 作为必需文件。
- 不因为旧 workflow 文档存在，就自动执行其中已经过时的状态机。
- 不把 `workflow/gtpj_workflow.py` 当成研究判断黑盒；它只做 validate、audit-boundary、目录创建和结果记录等结构性辅助动作。

## GitHub 必须保证的事情

1. 每个正式版本都能用 tag 回到对应代码。
2. 每个实验结果都能找到它使用的代码、配置、日志和结论。
3. 每个新模块都能追溯到创意来源，而不是凭空出现。
4. 每个 trial 都能说明它基于哪个 baseline，以及是否可以关闭回到 baseline。
5. 稳定入口、目录类型或文件职责变化时，必须同步更新 `docs/PROJECT_STRUCTURE.md`；
   新增普通实验、idea、trial 的具体实例只更新对应账本或索引，除非结构模式也变化。

## 同级正式框架和全局账本

GTPJ 使用同级正式框架注册表。框架之间保留历史来源指针，但不建立包含关系。

```text
FRAMEWORK-V1  derived_from: none
FRAMEWORK-V2  derived_from: FRAMEWORK-V1
FRAMEWORK-V3  derived_from: FRAMEWORK-V2
FRAMEWORK-V5  derived_from: FRAMEWORK-V3
```

这表示 V1、V2、V3、V5 都是同级正式框架；来源指针依次为 V2→V1、V3→V2、V5→V3。

每个正式框架都必须记录历史来源：

```text
framework_id: FRAMEWORK-V3
registry_level: formal_peer
derived_from_framework: FRAMEWORK-V2
promoted_from_experiment: V2-INNOVATION-001
code_tag: v3
change_type: add_module / replace_module / remove_module / combo
source_legacy_ref: experiments/module_trials/IDEA-0002_fae_memory_jepa/TRIAL-002_strict_conditional_jepa#ATTEMPT-004
inherits_code_from: FRAMEWORK-V2
does_not_inherit: unconfirmed promotion claim
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

全局同级框架与来源账本放在：

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

如果 `FRAMEWORK-V3.derived_from_framework = FRAMEWORK-V2`，那么：

```text
V3 的代码和方法来源于 V2
V3 与 V1、V2、V5 在正式框架注册表中仍然同级
experiments/v2/ 继续保留在 main，既是 v2 的正式记录，也是 V3 的来源证据
```

## 从已有来源框架确定新正式框架

当当前 `main` 已经包含较新的账本，但新框架代码要从已有正式框架产生时，必须按“两条来源”
处理：

```text
代码来源：derived_from_framework 对应框架的 TEMPLATE.yaml，以及其中登记的母版 Tag 和准确 commit
账本来源：提升时的当前 main
```

必须从来源正式框架的准确母版 commit 开创新实验分支；`main` 只维护治理和总账。
禁止把来源框架状态下的完整工作树或旧 `dev/...` 分支整体变成 `main`，因为那会把 `docs/`、`experiments/`、
`idea_tree/`、`config/versions/` 等全局账本回退到旧状态。

正确提升流程：

```text
1. 读取来源正式框架的 `TEMPLATE.yaml`，创建 `EXPERIMENT.yaml`，从准确母版 commit 开 `exp/vX/innovation/...` 分支。
2. 在该创新实验中完成调参表、结果和确认，不复制来源框架目录；候选阶段没有正式 Tag。
3. 创新成功后，在明确 code_commit 上创建新正式 Tag，并登记来源实验。
4. 回到当前 main，开 promote 分支，只处理新的同级正式框架登记。
5. 在 promote 分支中保留当前 main 的账本层。
6. 把成功 trial 的证据目录回流到当前账本。
7. 只把代码层切换或移植为来源 Tag + 成功 trial 的代码。
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
registry_level: formal_peer
derived_from_framework: FRAMEWORK-V1
promoted_from_experiment: V1-INNOVATION-xxx
ledger_source: current main
ledger_source_commit: <提升开始时的 main commit>
code_source: source framework tag + confirmed innovation commit
```

## 命名规范

正式框架实验分支：

```text
exp/<base-version>/<kind>/<experiment-id>-<short-name>
```

示例：

```text
exp/v1/tune/tune-001-topo008
exp/v1/ablation/ablation-001-disable-jepa
exp/v1/confirmation/confirm-001-clean-seed5
```

创新实验分支：

```text
exp/<base-version>/innovation/innovation-xxx-<short-name>
```

示例：

```text
exp/v1/innovation/innovation-001-token-router
exp/v2/innovation/innovation-002-token-router
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

`trial/...` tag 是 module trial 级代码快照，不是 attempt 级结果标签。不要为
`ATTEMPT-xxx`、best attempt、单次 H 值或调参结果创建 git tag；这些证据由
trial 账本、attempt 目录、commit hash 和 Warehouse artifact id 固定。

## 命名怎么看

```text
exp/v1/tune/tune-001-topo008
```

含义：

- `exp`：普通实验分支。
- `v1`：目标框架是 `FRAMEWORK-V1`；代码起点以该实验 `EXPERIMENT.yaml` 绑定的母版 commit 为准。
- `tune`：调参实验。也可以是 `ablation`、`innovation` 或 `confirmation`。
- `001`：该类型第 1 次实验。
- `topo008`：人能读懂的简短名字。

下面的 `dev/...` 是旧历史编号示例，不是新入口：

```text
dev/v1-idea-0003-trial-001-token-router
```

含义：

- `dev`：迁移前的新模块开发分支；新创新改用 `exp/vX/innovation/...`。
- `v1`：这次旧 trial 的来源代码是 `v1` baseline Tag。
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

- `exp/...` 分支承载目标框架下的 tune、ablation、innovation、confirmation 四类实验。
- 所有新实验都从 `TEMPLATE.yaml` 登记的准确母版 commit 独立开出；分支名为
  `exp/vX/<type>/<experiment-id>-<slug>`，`EXPERIMENT.yaml` 固定母版编号、Tag 和 commit。
- 实验分支不得并回母版，也不得作为另一个实验的代码起点。
- 结果写回该框架的四类账本和总览；治理索引同步回 `main`。
- 实验记录入账后，可以删除这个 `exp/...` 临时分支。

成功的模块 trial：

- 成功标准不是只看一次 `H` 上涨，而是指标有效、代码干净、实验口径一致。
- 成功 trial 可以确定为新的同级正式 `FRAMEWORK-VX`，但必须先写清 `derived_from_framework` 和 `promoted_from_experiment`。
- 如果新 `vX` 的来源框架不是当前 `main` 代码，提升时必须从当前 `main` 开 promote 分支，
  只切换代码层，不能删除或回退全局账本层。
- `experiments/v1/`、`experiments/v2/` 等历史记录目录必须继续保留在 `main`。
- 成功 trial 的轻量证据目录、artifact 指针、quality_check、result 和 code.diff 必须回流到当前 `main` 账本；raw logs、checkpoint 和 generated figures 留在 Warehouse。
- 在包含正式版本代码和版本材料的明确 commit 上打新的 baseline tag，例如 `v2` 或 `v3`；
  这个 commit 不必是当前 `main` commit。
- `main` 代码是否切到新 baseline，必须由 owner 明确执行 `activate-version` 决定。
- 新 baseline tag 打好后，可以删除对应 `dev/...` 分支。

Promotion 硬门：

- `H` 相比来源框架有明确提升，且记录 baseline H、trial H 和 delta H。
- 不能只凭一次偶然结果；必须区分 `best_observed_H` 和 `confirmed_H`，并达到
  `evidence_level: baseline_grade`。
- 运行必须来自 clean pre-run freeze commit；`dirty_state: dirty` 或 `git_dirty: true`
  只能记录为 debug/best_observed，不能 promotion。
- `U`、`S`、`ZS` 没有出现不可接受退化；如果有退化，必须解释为什么仍然接受。
- 训练命令、seed、配置副本、日志路径、best epoch 和结果表完整。
- evaluation 口径没有改变，包括 class order、seen/unseen split、logits shape 和 metric calculation。
- 模块开关关闭时可以回到 `derived_from_framework` 对应的来源行为。
- `quality_check.md` 的 `promotion_decision` 必须是 `promote`，并通过
  `docs/workflow/protocols/promotion.md` 的自动 promotion gate。
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
| 同级框架注册表 | `experiments/VERSION_TREE.md` | 新增正式 `vX`、改变历史来源指针或主版本时更新。 |
| 创意树细则 | `docs/workflow/protocols/idea_tree_protocol.md` | 改创意来源、评分、跨版本复用、排序和 trial 准入规则时更新。 |
| 论文 intake / idea discovery | `docs/workflow/protocols/paper_intake.md` | 改论文投递、阅读状态、来源复核、候选 idea 提取或 GitHub 轻量创意同步流程时更新。 |
| 创意树使用说明 | `idea_tree/README.md` | 改创意树目录用法、登记流程、人类阅读规则时更新。 |
| 机器可读格式 | `idea_tree/schema.json` | 改 `idea_tree.json` 字段结构时更新。 |
| 代码接口契约 | `docs/workflow/protocols/code_interface_contract.md` | 改新增模块的开关、输入输出、shape、loss、eval 约束时更新。 |
| 创新代码审查 | `docs/workflow/protocols/innovation_code_review_protocol.md` | 改 idea/创新/module trial 落成代码、多 agents 多轮审查、临时 agents 或 review 轮次规则时更新。 |
| Git 规则 | `docs/workflow/protocols/git_policy.md` | 改 `main`、`dev/...`、`exp/...`、tag、push 规则时更新。 |
| 普通实验协议 | `docs/workflow/protocols/experiment_protocol.md` | 改 tune、ablation、confirmation 流程、历史版本临时分支、调参表或消融接口检查时更新。 |
| 自动 promotion | `docs/workflow/protocols/promotion.md` | 改 `promotion_decision: promote`、硬门、本地 tag、版本材料、账本回流、main active code 或不自动 push 边界时更新。 |
| agent 编排 | `docs/workflow/protocols/agent_orchestration.md` | 改长期 agent 角色、文件夹结构、多 agent 编排、GPU 串行或 skill 同步规则时更新。 |
| 长期 agent 记忆 | `docs/workflow/agents/long_term_memory.md` | 改长期 agent 身份、角色记忆、实例加载、记忆写回或复用经验规则时更新。 |
| 进度看板协议 | `docs/workflow/protocols/progress_dashboard.md` | 改本地网页看板、`.gtpj_runtime/` 状态文件、agent 进度、GPU/Runner 展示或只读边界时更新。 |

## 本地 skill 和 GitHub 的同步

GitHub 仓库规则是 GTPJ workflow 的唯一事实来源。本地 Codex Skill 只是一个轻量入口：

```text
C:\Users\Administrator\.codex\skills\gtpj-workflow
```

修改 workflow 规范时：

1. 先更新 GitHub 文档。
2. 只有入口文件路径变化时，才更新本地 `gtpj-workflow/SKILL.md`。
3. 运行 Skill 入口校验和仓库验证。
4. 用户明确要求后再提交推送。

本机 Skill 不再镜像整套 `references/`。历史副本可以保留回查，但不参与当前规则校验；发生冲突时始终以 GitHub 仓库为准。

你刚才说的“不同版本的创意权重不一样”属于创意树细则，所以主更新位置是：

```text
docs/workflow/protocols/idea_tree_protocol.md
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
- `idea_tree/INDEX.md` 是总创意清单，只说明创意主要内容；`idea_tree/versions/vX.md` 是某个版本的选择清单。
- 下一步动作不写入全局总创意清单，只写入 queue、trial/attempt、task card 或实验结果文件。
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
`vX`，必须通过 `docs/workflow/protocols/promotion.md` 的自动 promotion gate，不能只看一次 `H` 提升。
单次最高结果只能写成 `best_observed_H`；没有 clean confirmation 或多 run 稳定性证据时，
只能由 owner 选择 provisional/owner-activated 主线，不能写 confirmed baseline。

以后如果把 `quality_check` 自动化接入 OpenClaw/Codex runtime，可以把它升级成自动化质量门。
在此之前，普通实验的 `quality_check` 是 GitHub 证据完整性的检查表；
promotion 的 `quality_check` 是正式版本准入门。当实验记录明确写
`promotion_decision: promote`、`evidence_level: baseline_grade` 且硬门全部通过时，
Coordinator 可以自动创建本地新版本材料和本地 tag，
并把版本账本回流到 `main`；但不自动切换 `main` 当前代码，也不自动 push GitHub。

## agent_summary 是什么

`agent_summary.md` 是 agent 工作凭证，不是完整聊天记录。它记录：

- 本次实验启用了哪些 agents；
- 哪些 agents 被禁用；
- 每个 agent 检查了哪些输入；
- 创新代码改动的 Review 0-3 是否完成，以及是否启用了临时 agents；
- 发现了哪些 blocking / non-blocking issue；
- 最终决策引用了哪些 artifact、commit 和质量检查。

长报告、完整日志分析和 runner 细节放 Warehouse；GitHub 只保存摘要和 artifact id。具体规则见
`docs/workflow/protocols/agent_report_policy.md`。

## 从旧 cv 实验工作流可以学习什么

可以继续保留并复用的工作流思想：

- 每次实验前后都要有 Git 检查点。
- 代码改动、配置改动、结果记录要分开。
- 新模块必须默认关闭，实验配置再打开。
- 结果要反馈到创意树，而不是只写在日志里。
- 失败实验也要保留，避免重复踩坑。
- 多 runtime 必须共享同一套仓库事实来源。

暂时不接入自动调度的部分：

- 固定多轮审查。
- 旧工作流的固定 `ACCEPTED / REJECTED` 决策格式。
- 自动选择下一个实验。
- 自动调度 OpenClaw、Codex 或其他 agent 来选择/启动实验。
- 完整实验状态机。
