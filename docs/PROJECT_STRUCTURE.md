# 项目结构说明

本文件是 GTPJ 仓库的结构总账本。它说明稳定目录、入口文件和可重复目录模式的用途；
不作为每个实验、idea、trial 实例的逐项清单。

维护硬规则：

- 新增、删除、移动、重命名稳定入口、目录类型或关键文件时，必须同步更新本文件。
- 改变某个文件或目录类型的职责时，必须同步更新本文件。
- 新增普通实验、idea 或 trial 的具体实例时，优先更新对应 INDEX、登记表或 idea_tree 记录；
  只有结构模式、入口职责或维护规则变化时才更新本文件。
- 修改 GitHub 治理规范、实验记录规范、创意树规范、代码接口规范或 workflow/runtime 入口职责时，必须同步更新本文件中对应说明。
- 只更新实验数值、日志路径或普通记录内容时，也要检查本文件是否需要更新；如果结构和职责没有变化，可以不改。
- 结构性改动完成前建议运行 `python workflow/gtpj_workflow.py validate`；需要确认 GitHub 远端状态时再运行
  `python workflow/gtpj_workflow.py validate-remote`。`validate-remote` 核对远端 `main`/`v1`
  分别对齐本地 `main`/`v1`，并确认本地 `main` 包含 `v1` 历史。它们是 workflow 的结构辅助检查，不替代研究判断。

## 总体框架

GTPJ 仓库分成三层：

```text
代码层：model/、tools/、train_*.py、当前运行别名 config/GTPJ_*.yaml
治理与复现控制层：docs/、workflow/、schemas/、AGENTS.md、NEXT_ACTIONS.md
轻量实验索引层：experiments/、config/versions/、idea_tree/ 的索引视图
```

完整材料和大型资产在 GitHub 外：

```text
GTPJ_Research：论文、完整阅读笔记、完整创意树、长推理、创新草稿和来源复核。
GTPJ_Warehouse：raw logs、checkpoint、experiment visualizations、experiment tables、failure cases。
```

核心关系：

```text
idea_tree/                 # 创意来源、评分、排序
  -> experiments/module_trials/
                             # 模块创意被选中后，保存实现和证据
  -> promoted baseline vX    # 成功 trial 才能提升为新版本
  -> experiments/vX/         # 新版本自己的 tune / ablation / confirmation 记录
```

注意两层实验位置：

- version-level tune / ablation / confirmation 写入 `experiments/vX/`；
- module trial 内部的 `param_tune`、narrow `ablation`、clean `confirmation` 写入该 trial 的
  `ATTEMPTS.md` 和 `attempts/ATTEMPT-xxx/`，用于判断这个新模块本身是否值得保留。

版本规则：

```text
一个 vX = 一个 baseline = 一个 Git tag = 一个版本实验目录 = 一个父节点记录
```

当前 active baseline 是 `GTPJ-v2 / tag v2 / H=74.29`。历史基线
`GTPJ-v1 / tag v1 / H=73.93` 永久保留。`main` 是唯一长期分支；
`v1`、`v2` 是 tag，不是分支。

代码层和实验层不要混淆：

```text
代码层跟随 owner 明确选择的 active version，例如 v3。
实验层是全局账本，必须同时保留 experiments/v1/、experiments/v2/、experiments/v3/。
```

`experiments/v2/` 出现在最新 `main` 中，只表示 v2 历史记录仍被保存，
不表示 active version v3 继承了 v2 的代码。

## 顶层文件

| 路径 | 用途 |
|---|---|
| `README.md` | 项目入口说明，解释 GTPJ 的目标、当前版本、主要目录、GitHub 治理重点和结构辅助命令。 |
| `AGENTS.md` | agent 协作规则，规定沟通语言、仓库规则、实验规则、安全边界和结构文档同步要求。 |
| `NEXT_ACTIONS.md` | 当前执行窗口，只保留近期优先动作，不放完整想法库。 |
| `requirements.txt` | pip 环境依赖，包含 PyTorch 周边库和 OpenAI CLIP。 |
| `environment.yml` | conda 环境定义；本机 GTPJ 实验默认使用 `dvsr_gpu` 运行环境。 |
| `train_GTPJ_CUB.py` | CUB GZSL 主训练入口，读取 YAML config，训练 GTPJ 并写训练日志。 |
| `train_GTPJ_AWA2.py` | AWA2 GZSL 训练入口。 |
| `train_GTPJ_SUN.py` | SUN GZSL 训练入口。 |

## `config/`

配置目录。版本配置和数据集别名配置都在这里。

| 路径 | 用途 |
|---|---|
| `config/README.md` | 配置策略说明，解释版本配置、实验局部配置和候选模块开关的关系。 |
| `config/versions/v1.yaml` | `GTPJ-v1` 的固定 baseline 配置，是 v1 的权威配置源。 |
| `config/versions/v2.yaml` | `GTPJ-v2` 的固定 baseline 配置，是当前 active baseline 的权威配置源。 |
| `config/GTPJ_cub_gzsl.yaml` | CUB 运行配置别名，当前内容应与 owner 明确选择的 active version 的 `config/versions/vX.yaml` 保持一致；现在对应 `v2`。 |
| `config/GTPJ_awa2_gzsl.yaml` | AWA2 运行配置。 |
| `config/GTPJ_sun_gzsl.yaml` | SUN 运行配置。 |

规则：

- 临时调参不要直接改 `config/versions/v1.yaml`。
- 实验应复制版本配置到对应实验目录后再修改。
- 未启用候选模块不进入版本配置，先进入 `idea_tree/`。
- `config/versions/` 属于账本层；`config/GTPJ_*.yaml` 属于当前运行别名。promotion 分支可以为
  新版本准备运行别名，但回流 `main` 时默认不同步运行别名；只有 owner 明确执行
  `activate-version` 时，才把 `config/GTPJ_*.yaml` 切到对应版本。

## `docs/`

项目文档目录。这里保存长期规则、状态说明和数据说明。

| 路径 | 用途 |
|---|---|
| `docs/PROJECT_STRUCTURE.md` | 本文件，项目结构总账本。 |
| `docs/PROJECT_STATUS.md` | 当前项目状态、baseline、启用模块和参考结果。 |
| `docs/GITHUB_GOVERNANCE.md` | GitHub 控制面主规范，说明 GitHub 如何管理版本树、tag、分支命名、合并删除、配置快照、创意树和实验证据。 |
| `docs/DATA_SETUP.md` | 数据集、本地缓存、大文件不入 Git 的说明。 |

## `docs/workflow/`

实验创新 workflow 目录。默认只服务跑实验、做创新、复现、消融、调参、debug 和实验结果记账。

| 路径 | 用途 |
|---|---|
| `docs/workflow/README.md` | workflow 入口，说明核心规范、阅读顺序、runtime 边界和结构辅助工具。 |
| `docs/workflow/WORKFLOW_ROUTER.md` | GTPJ 总教官/总路由文件，先判断任务类型、是否进入创意树、写入位置、必读协议、agents 和 gate。 |
| `docs/workflow/TASK_START_CARD.md` | 每次 GTPJ 工作开始前的启动卡模板，把 Router 判断落成可检查的任务单。 |
| `docs/workflow/FIRST_CLOSED_LOOP.md` | 首条工作流闭环指南，建议先用 readiness check / tune-suggest / confirmation 验证通路。 |
| `docs/workflow/CURRENT_WORKFLOW_REPORT.md` | 当前工作流汇报版入口，集中解释 GitHub、多 agents、本地目录、工作规范和当前完成度。 |
| `docs/workflow/GTPJ_WORKFLOW_SPEC.md` | GTPJ 实验创新工作流总规范，集中说明 GitHub、本地目录、创意树、实验记账、tag、agents、质量门和实验闭环。 |
| `docs/workflow/IMPLEMENTATION_STATUS.md` | 规范落地状态清单，说明哪些文件已落地、哪些按需创建、哪些仍是设计，避免 owner 反复口述当前完成度。 |
| `docs/workflow/git_policy.md` | Git 分支、tag、push、trial 快照策略，以及带 base version 的命名规则。 |
| `docs/workflow/versioning.md` | baseline 版本命名、tag、实验目录、父节点、版本树和提升规则。 |
| `docs/workflow/idea_tree_protocol.md` | 创意树协议，规定 idea 节点、来源、评分、跨版本复用和排序方式。 |
| `docs/workflow/paper_intake.md` | 论文投递、阅读状态、来源复核、候选 idea 提取和 GitHub 轻量创意同步流程。 |
| `docs/workflow/module_trial_protocol.md` | 模块 trial 协议，规定 trial 目录结构、分支/tag 命名、必填记录和决策类型。 |
| `docs/workflow/code_interface_contract.md` | 代码接口契约，规定新增模块的开关、输入输出、shape、loss、eval 和最低验证要求。 |
| `docs/workflow/experiment_protocol.md` | tune、ablation、confirmation 实验协议，包含历史版本运行分支、调参表、消融接口检查和临时分支销毁规则。 |
| `docs/workflow/artifact_policy.md` | GitHub 轻量边界和 Research/Warehouse 外部资产职责。 |
| `docs/workflow/ARTIFACT_REGISTRATION.md` | 外部 artifact 入账步骤，规定 Warehouse 路径、artifact id、URI、hash、size、manifest/result 引用。 |
| `docs/workflow/result_index_protocol.md` | `manifest.yaml`、`result.yaml`、`result.md` 的实验结果索引协议。 |
| `docs/workflow/agent_contracts.md` | 长期 agent IO 契约、自我介绍、读写边界和失败条件。 |
| `docs/workflow/agent_report_policy.md` | agent 工作凭证保存规范，规定 `agent_summary.md`、长报告 Warehouse 引用和不保存完整聊天流水。 |
| `docs/workflow/promotion.md` | 自动 promotion 规范，规定 `promotion_decision: promote` 后的硬门、本地版本创建、账本回流、不自动切换 main active code 和不自动 push 边界。 |
| `docs/workflow/agent_orchestration.md` | 长期 agent 角色、文件夹管理、四类实验编排、GPU 串行规则和本地 skill 同步规则。 |
| `docs/workflow/agents/` | workflow agent 权威目录；`shared_roles/` 保存共享角色定义，`by_experiment/` 保存每类实验的 agents 编排。 |
| `docs/workflow/progress_dashboard.md` | 本地只读网页看板协议，规定 `.gtpj_runtime/` 运行中状态、agent 进度、GPU/Runner 状态和证据完整性展示边界。 |
| `docs/workflow/quality_gate.md` | 质量门规则，区分普通实验证据检查和 baseline promotion 强制门。 |
| `docs/workflow/runbook.md` | 常见操作手册，包括确认 v1、运行调参、启动模块 trial 和提升版本。 |
| `docs/workflow/issues/` | 日期化实验问题知识库；新对话默认先读 `issues/README.md` 和最近日期文档，不全量读取历史问题。 |

## `workflow/`

结构辅助与 runtime 接入层。用于检查结构、创建标准目录、登记结果、维护本地 runner lock，并给 OpenClaw/Codex 提供同一套 workflow 入口。

| 路径 | 用途 |
|---|---|
| `workflow/README.md` | 结构辅助说明和 runtime 入口说明。 |
| `workflow/gtpj_workflow.py` | CLI helper，提供 `status`、`validate`、`validate-remote`、`audit-boundary`、`new-experiment`、`tune-suggest`、`runner-lock`、`runner-unlock`、`record-result`、`new-idea`、`new-trial`、`set-current-version`；会检查 `v1` tag 是否对应 `H=73.93`，可核对远端 `main`/`v1` 与本地 `main`/`v1` 对齐，要求 `new-experiment` 位于 clean 且包含当前本地 `main` 历史的目标 `exp/...` 分支，并生成带 base version 的分支/tag 建议、tune 候选建议、GPU Runner 本地锁、外部日志 artifact 入账和创意树版本视图。`set-current-version` 只切换创意树视图，不切换 `main` active code。 |
| `workflow/codex/README.md` | Codex workflow 入口，说明 Codex 如何遵循同一套 GitHub 事实源和 workflow 规范。 |
| `workflow/openclaw/README.md` | OpenClaw workflow 入口，说明 OpenClaw 如何遵循同一套 GitHub 事实源和 workflow 规范。 |
| `workflow/openclaw/agent_roles.md` | OpenClaw 多角色职责参考：Coordinator、Reader、Implementer、质量检查者、Result Analyst；角色边界以 `docs/workflow/agent_orchestration.md` 为准。 |

`workflow/gtpj_workflow.py` 的职责：

- 检查仓库结构是否完整。
- 检查正式 baseline tags 是否对应各自版本账本中的 H 值。
- 检查创意树、版本配置和接口规范关键章节。
- 创建实验目录和标准模板。
- 创建实验时同步更新全局登记表和版本索引。
- 生成最多 3 个 tune 候选建议；用户选择前不启动训练、不落账本。
- 通过 `.gtpj_runtime/gpu_runner.lock` 提供本地 GPU Runner 文件锁，避免同时启动多个训练。
- 解析外部训练日志中的 U/S/H/ZS 和 best epoch，计算 artifact hash/size，并把 tune 结果写回实验 README、`manifest.yaml`、`result.yaml`、`result.md`、`experiments/vX/tune/INDEX.md` 与 `experiments/EXPERIMENT_REGISTRY.md`。
- 通过 `audit-boundary` 检查新实验没有 raw logs、checkpoint、generated figures 或 cache 进入 GitHub。
- 创建 idea 节点和 trial 目录。
- 创建 trial 时同步更新 module trial 索引和 idea 的 `linked_trials`。
- 根据 `idea_tree.json.current_version` 和每个创意的 `version_scores` 重新生成
  `idea_tree/INDEX.md` 与 `idea_tree/versions/vX.md`。
- `set-current-version` 只改变创意树视图；`main` active code 只能由 owner 明确执行
  `activate-version vX` 改变。

## `model/`

模型代码目录。

| 路径 | 用途 |
|---|---|
| `model/MyModel.py` | GTPJ 主模型实现，包含 CLIP/Adapter/GPT/双向 Transformer、LaSt-ViT pooling、FAE、AG-JEPA 等核心组件。 |
| `model/modules/` | 预留模块目录；如果以后把新模块从 `MyModel.py` 拆出去，应放在这里并同步更新本文件。 |

代码接口要求：

- 新模块必须遵守 `docs/workflow/code_interface_contract.md`。
- 开关关闭时必须回到选定 base version 行为。
- 不得静默改变 logits shape、class order、loss 语义或 eval 语义。

## `tools/`

数据、特征和评估工具目录。

| 路径 | 用途 |
|---|---|
| `tools/dataset.py` | CUB、AWA2、SUN 数据读取和 DataLoader 定义。 |
| `tools/helper_func.py` | 评估、特征缓存加载、CLIP spatial feature 获取等公共函数。 |
| `tools/extract_features.py` | 预提取 CLIP 图像/patch 特征并缓存到 `data/cache/`。 |
| `tools/eval_pure_clip.py` | 纯 CLIP zero-shot / GZSL baseline 评估脚本。 |

注意：

- `data/`、`data/cache/`、原始数据、特征缓存和 checkpoint 不纳入 Git。
- 如果工具脚本改变评估语义，必须同步更新 `docs/workflow/code_interface_contract.md` 和本文件。

## `idea_tree/`

创意树目录。它是 GitHub 中的轻量 idea 事实索引，管理想法来源、评分和优先级，
不保存完整论文笔记、长推理、创新草稿或训练日志。长版材料放在本地 `GTPJ_Research`。

| 路径 | 用途 |
|---|---|
| `idea_tree/README.md` | 创意树入口说明。 |
| `idea_tree/创意树.md` | 中文入口页，帮助快速理解创意树文件分工。 |
| `idea_tree/INDEX.md` | 给人读的总创意清单，只回答有哪些创意；当前为空，等待可靠来源重新登记。 |
| `idea_tree/idea_tree.json` | 机器可读总创意注册表，包含 `current_version`、`ideas` 和每个 idea 的 `version_scores.vX`；当前 `ideas` 为空，是创意树唯一机器事实源。 |
| `idea_tree/schema.json` | `idea_tree.json` 的结构约束，规定版本分数字段必须按 `v1`、`v2` 这类版本键保存。 |
| `idea_tree/versions/` | 按版本生成的人类阅读选择清单；创新 trial 只读取对应 base version 的清单。 |
| `idea_tree/versions/v1.md` | `v1` 创意选择清单，由 helper 根据 `idea_tree.json` 生成。 |
| `idea_tree/versions/v2.md` | `v2` 创意选择清单，由 helper 根据 `idea_tree.json` 生成。 |
| `idea_tree/inbox.md` | 粗糙想法收件箱，尚未成为稳定 `IDEA-xxxx`。 |
| `idea_tree/sources/papers_index.md` | 论文来源索引。 |
| `idea_tree/sources/source_notes/` | 预留来源笔记目录；可放论文摘录、来源复核摘要等轻量文本。 |

### `idea_tree/queues/`

当前工作队列，从总索引派生，不是事实来源。

| 路径 | 用途 |
|---|---|
| `idea_tree/queues/01_selected_next.md` | 已选中的下一步模块 trial。 |
| `idea_tree/queues/02_module_candidates.md` | 当前候选模块列表。 |
| `idea_tree/queues/03_ablation_questions.md` | 消融问题队列。 |
| `idea_tree/queues/04_tuning_questions.md` | 调参问题队列。 |

### `idea_tree/ideas/`

每个稳定创意一个目录，每个目录里必须有 `IDEA.md`。

| 路径 | 用途 |
|---|---|
| `idea_tree/ideas/.gitkeep` | 保留空的创意目录；来源明确后再新增 `IDEA-xxxx_slug/IDEA.md`。 |

## `experiments/`

实验记录目录。这里保存轻量证据，不保存原始数据、大型日志、checkpoint、generated figures 或 cache。

| 路径 | 用途 |
|---|---|
| `experiments/README.md` | 实验记录目录说明。 |
| `experiments/EXPERIMENT_REGISTRY.md` | 全局实验登记表，记录版本、模块 trial 和版本实验。 |
| `experiments/VERSION_TREE.md` | 全局版本树账本，记录正式 baseline 的父节点、代码 tag、账本来源和 trial 来源。 |
| `experiments/LEGACY_POLICY.md` | 边界重构前历史证据的迁移规则；`GTPJ-v1` baseline 原始日志已迁到外部 Warehouse，GitHub 只保留 artifact id、URI、hash 和 size。 |

### `experiments/templates/`

实验和 trial 的模板目录。

| 路径 | 用途 |
|---|---|
| `experiments/templates/experiment_README_template.md` | 普通实验 README 模板，记录代码快照、环境、数据/cache、日志、attempt、失败阶段和 tune/ablation 专属字段。 |
| `experiments/templates/agent_summary_template.md` | agent 工作凭证模板，记录参与 agents、检查范围、发现、结论和证据引用。 |
| `experiments/templates/IDEA_template.md` | idea 文件模板。 |
| `experiments/templates/implementation_template.md` | 模块实现记录模板，包含输入输出契约和最低验证项。 |
| `experiments/templates/quality_check_template.md` | 质量检查模板，用于记录证据完整性，并在正式升版时执行 promotion gate。 |
| `experiments/templates/TRIAL_README_template.md` | trial README 模板，包含结果记录和 promotion gate 字段。 |
| `experiments/templates/TRIAL_ATTEMPTS_template.md` | module trial 内部多次 attempt 总表模板。 |
| `experiments/templates/VERSION_template.md` | 版本说明模板。 |

### `experiments/module_trials/`

模块 trial 证据目录。这里不是权威创意库；权威创意在 `idea_tree/ideas/`。

| 路径 | 用途 |
|---|---|
| `experiments/module_trials/INDEX.md` | 模块 trial 索引。 |
| `experiments/module_trials/.gitkeep` | 保留空的模块 trial 目录；来源明确且开始实现后再新增 `IDEA-xxxx_slug/`。 |

真正开始 trial 后，目录会增加：

```text
experiments/module_trials/IDEA-xxxx_slug/TRIAL-xxx_slug/
|-- README.md
|-- ATTEMPTS.md
|-- implementation.md
|-- code.diff
|-- agent_summary.md
`-- attempts/
    `-- ATTEMPT-001/
        |-- config.yaml
        |-- manifest.yaml
        |-- result.yaml
        |-- quality_check.md
        `-- result.md
```

### `experiments/v1/`

`GTPJ-v1` 的版本实验目录。

| 路径 | 用途 |
|---|---|
| `experiments/v1/VERSION.md` | v1 版本说明，记录 baseline、启用模块和训练策略。 |
| `experiments/v1/config.yaml` | v1 配置归档副本，应与 `config/versions/v1.yaml` 保持一致。 |
| `experiments/v1/result.md` | v1 结果记录，保存第一版正式 baseline 指标和外部日志 artifact 证据。 |
| `experiments/v1/baseline/README.md` | `GTPJ-v1` 第一版正式 baseline 证据说明。 |
| `experiments/v1/baseline/config.yaml` | `GTPJ-v1` baseline 配置副本，`conditional_text_ratio=0.008`。 |
| `experiments/v1/baseline/manifest.yaml` | `GTPJ-v1` baseline 复现地图，记录外部日志 artifact URI、hash、size 和评估契约。 |
| `experiments/v1/baseline/result.yaml` | `GTPJ-v1` baseline 机器可读结果，供 helper、agent 和 promotion gate 读取。 |
| `experiments/v1/baseline/quality_check.md` | `GTPJ-v1` baseline 轻量质量检查记录。 |
| `experiments/v1/tune/INDEX.md` | v1 调参实验索引。 |
| `experiments/v1/ablation/INDEX.md` | v1 消融实验索引。 |
| `experiments/v1/confirmation/INDEX.md` | v1 确认实验索引。 |

### `experiments/v2/`

`GTPJ-v2` 的版本实验目录。

| 路径 | 用途 |
|---|---|
| `experiments/v2/VERSION.md` | v2 版本说明，记录父版本、来源 trial、启用模块、正式结果和已知风险。 |
| `experiments/v2/config.yaml` | v2 配置归档副本，应与 `config/versions/v2.yaml` 保持一致。 |
| `experiments/v2/result.md` | v2 结果记录，保存当前正式主线指标和外部日志 artifact 证据。 |
| `experiments/v2/baseline/README.md` | `GTPJ-v2` baseline 证据说明。 |
| `experiments/v2/baseline/config.yaml` | `GTPJ-v2` baseline 配置副本，来自 `TRIAL-001 / ATTEMPT-019`。 |
| `experiments/v2/baseline/manifest.yaml` | `GTPJ-v2` baseline 复现地图，记录外部 artifact URI、hash、size 和评估契约。 |
| `experiments/v2/baseline/result.yaml` | `GTPJ-v2` baseline 机器可读结果。 |
| `experiments/v2/baseline/quality_check.md` | `GTPJ-v2` baseline 质量检查和 owner 主线化决策记录。 |
| `experiments/v2/tune/INDEX.md` | v2 调参实验索引。 |
| `experiments/v2/ablation/INDEX.md` | v2 消融实验索引。 |
| `experiments/v2/confirmation/INDEX.md` | v2 确认实验索引。 |

这些 `experiments/vX/*` 索引用于 version-level 实验。某个 module trial 内部为了比较 heads、ratio、
dropout、seed，或做窄消融、clean confirmation，应写入该 trial 的 `ATTEMPTS.md` 和
`attempts/ATTEMPT-xxx/`。

## 更新本文件的判断标准

必须更新本文件的情况：

- 新增、删除、移动、重命名稳定入口、目录类型、顶层目录或关键规范文件。
- 新增正式 baseline 目录或新的版本层级说明，例如 `experiments/v2/`、`config/versions/v2.yaml`。
- 新增脚本、工具、模型文件、配置文件，且它们承担新的入口或职责。
- 改变某个文件的职责、入口地位或维护规则。

通常不需要更新本文件的情况：

- 在已有 `tune/`、`ablation/`、`confirmation/` 下新增一次实验运行目录。
- 在已有 `idea_tree/ideas/` 下新增一个具体 `IDEA-xxxx_slug/`。
- 在已有 `experiments/module_trials/` 下新增一个具体 trial 目录。
- 只在已有实验 README 中补充一次运行结果。
- 在外部 Warehouse 增加 raw log、checkpoint 或 generated figure，但 GitHub 结构和职责不变。
- 只修改配置数值，但配置文件职责不变。

即使通常不需要，也必须在提交前检查本文件是否仍然准确。
