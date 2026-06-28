# GTPJ 实验创新工作流总规范

本文是 GTPJ 实验创新工作流总规范。它默认只服务跑实验、做创新、复现、消融、调参、debug 和实验结果记账。

## 0. 当前结论

当前项目已经完成的是“治理骨架、核心 workflow 规范和首个真实 module-trial 到正式版本的闭环”：

- GitHub 仓库已经被定位为轻量控制面：保存代码、配置、复现实验索引、版本账本、质量门和 agent 规范。
- 本地外部目录已经被定位为材料和资产面：保存来源材料、完整创意来源、raw logs、checkpoint 和实验诊断材料。
- agents 的角色边界已经落地：选创意、写代码、跑实验、读日志、查接口、审结果、做 promotion 各有边界。
- 代码接口、评估标注、结果记录、artifact 引用和质量门已经形成规范入口。
- `IDEA-0001 / TRIAL-001` 已由 owner 激活为 `GTPJ-v2` 当前主线代码；
  `H=74.29` 是 `best_observed_H`，`confirmed_H` 仍待 clean confirmation。

当前还没有完成的是“自动 runtime 产品化和 v2 后续复核”：

- 还没有把本地看板或自动 runtime 变成日常强制入口。
- `GTPJ-v2` 仍必须补 clean confirmation，之后才可把 `best_observed_H=74.29`
  升级成 `confirmed_H` 或 baseline-grade 证据；seen/unseen gap analysis 和关键 ablation 仍是后续项。

所以现在的正确动作是：核心 workflow 按本文件执行；后续实验默认基于当前 active mainline `v2`，
除非 owner 明确要求从历史版本 tag 开始。

落地状态不要靠口述判断。每次需要确认哪些文件已经实体化、哪些仍是设计时，读取：

```text
docs/workflow/IMPLEMENTATION_STATUS.md
```

Owner 日常入口不要靠临场解释。每次 GTPJ 任务开始前，先读取 owner-facing 入口：

```text
docs/workflow/QUICK_START.md
docs/workflow/TASK_START_MINI.md
```

任务类型不要靠临场推理。Owner 口令进入后台后，再读取总教官/总路由文件：

```text
docs/workflow/WORKFLOW_ROUTER.md
```

Router 判断后，用完整启动卡记录后台执行边界：

```text
docs/workflow/TASK_START_CARD.md
```

Owner 不需要主动要求启动卡，也不需要说 `module trial`、`real_multi_agent`、
`Review 0-3` 或 artifact 边界。人话口令和 mini 启动卡字段以 `QUICK_START.md` /
`TASK_START_MINI.md` 为准，本总规范不重复维护那张入口表。

正式改文件、建目录或跑实验前，先在对话中说明能不能开工、任务类型、当前缺口和下一步最小动作。

第一次开跑工作流时，先用首条闭环指南做 readiness check：

```text
docs/workflow/FIRST_CLOSED_LOOP.md
```

核心判断：

```text
实验是为了调/查/验证已有正式 baseline -> experiments/vX，不进 idea_tree。
实验是为了调/查/确认某个 module trial 内部模块 -> experiments/module_trials/.../attempts/ATTEMPT-xxx，不另进 idea_tree。
实验是为了证明一个新方法值得存在 -> idea_tree + module_trials。
```

## 1. 总体设计

GTPJ 实验创新系统分成两部分：

```text
D:\backup\Documents\Myself\GTPJ
  GitHub 仓库，负责代码、配置、规范、版本、轻量实验索引。

D:\backup\Documents\Myself\GTPJ_Research
D:\backup\Documents\Myself\GTPJ_Warehouse
  本地外部目录。默认实验 workflow 只使用 Research 和 Warehouse。
```

核心原则：

- GitHub 只保存能让实验被复现、被审计、被索引的最小事实。
- GitHub 不保存 raw logs、checkpoint、cache、generated figures 和完整长材料。
- 本地目录保存大文件和研究材料，但 GitHub 里必须留下能追踪它们的 artifact id、URI、hash、size 和复现配置。
- 每个实验结果必须回答四件事：从哪个版本来，用什么配置跑，评估语义是什么，外部证据在哪里。

## 2. GitHub 仓库结构

仓库根目录：

```text
D:\backup\Documents\Myself\GTPJ
```

### 2.1 顶层文件

| 路径 | 作用 |
|---|---|
| `README.md` | 项目入口，说明 GTPJ 是什么、当前基线、主要目录和常用辅助命令。 |
| `AGENTS.md` | 仓库内 agent 协作规则，规定沟通语言、实验边界、安全边界和结构文档同步要求。 |
| `NEXT_ACTIONS.md` | 当前短期执行窗口，只放近期要做的动作，不放完整创意库。 |
| `.gitignore` | 禁止 raw logs、checkpoint、cache、generated figures、本地路径配置和运行状态进入 GitHub。 |
| `requirements.txt` | pip 依赖入口。 |
| `environment.yml` | conda 环境入口。 |
| `train_GTPJ_CUB.py` | CUB GZSL 训练入口，读取 config、训练模型、输出运行日志到外部位置。 |
| `train_GTPJ_AWA2.py` | AWA2 GZSL 训练入口。 |
| `train_GTPJ_SUN.py` | SUN GZSL 训练入口。 |

### 2.2 配置层 `config/`

| 路径 | 作用 |
|---|---|
| `config/README.md` | 说明版本配置、实验局部配置和候选模块开关的关系。 |
| `config/versions/v1.yaml` | `GTPJ-v1` 权威 baseline 配置。正式版本配置放这里。 |
| `config/versions/v2.yaml` | `GTPJ-v2` 权威 baseline 配置，是当前 active baseline 的配置源。 |
| `config/GTPJ_cub_gzsl.yaml` | 当前 CUB 运行别名。只有 owner 明确切换 active version 时才同步到某个 `vX`。 |
| `config/GTPJ_awa2_gzsl.yaml` | 当前 AWA2 运行别名。 |
| `config/GTPJ_sun_gzsl.yaml` | 当前 SUN 运行别名。 |

规则：

- 临时实验不能直接改 `config/versions/vX.yaml`。
- 每次实验必须把 base version 配置复制到实验目录的 `config.yaml`，再记录局部改动。
- `config/versions/vX.yaml` 是版本账本，不是随手调参文件。
- `config/GTPJ_*.yaml` 是当前运行别名，不等于全部历史版本。

### 2.3 代码层

| 路径 | 作用 |
|---|---|
| `model/MyModel.py` | GTPJ 主模型实现，包含当前模型结构和候选模块集成点。 |
| `model/modules/` | 预留模块目录。后续把新模块从主模型拆出来时放这里。 |
| `tools/dataset.py` | CUB、AWA2、SUN 数据读取和 DataLoader 定义。 |
| `tools/helper_func.py` | 评估、特征缓存读取、CLIP spatial feature 获取等公共函数。 |
| `tools/extract_features.py` | 预提取 CLIP 特征并写入本地 cache。cache 不进入 GitHub。 |
| `tools/eval_pure_clip.py` | 纯 CLIP zero-shot / GZSL baseline 评估脚本。 |

代码接口硬规则：

- 新模块必须有开关，关闭时回到 base version 行为。
- 不得静默改变 logits 形状、class order、seen/unseen 划分、loss 语义或 eval 语义。
- 首次写 shape 必须带含义，例如 `[B（图片/样本数量）, C（类别数量）]`、`[B（图片/样本数量）, D（特征维度）]`。
- 评估标注不清楚时，结果无效，不能用于比较、调参结论或 promotion。

### 2.4 文档层 `docs/`

| 路径 | 作用 |
|---|---|
| `docs/PROJECT_STRUCTURE.md` | 仓库结构总账本。稳定目录、入口文件或职责变化时必须同步更新。 |
| `docs/PROJECT_STATUS.md` | 当前项目状态、当前 baseline、启用模块和参考结果。 |
| `docs/GITHUB_GOVERNANCE.md` | GitHub 治理主规范，说明 branch、tag、版本树、配置快照、实验索引和合并边界。 |
| `docs/DATA_SETUP.md` | 数据集、本地缓存和大文件不入 GitHub 的说明。 |
| `docs/workflow/GTPJ_WORKFLOW_SPEC.md` | 本文件，供 owner 审阅的完整工作流总规范。 |
| `docs/workflow/workflow_diagrams.md` | 流程图标准，规定版本流程图、module trial 流程图、Mermaid 权威格式和更新时机。 |

### 2.5 工作流规范层 `docs/workflow/`

| 路径 | 作用 |
|---|---|
| `docs/workflow/README.md` | workflow 文档入口和推荐阅读顺序。 |
| `docs/workflow/WORKFLOW_ROUTER.md` | 总教官/总路由文件，先判断任务类型、是否进入创意树、写入位置、必读协议、agents 和 gate。 |
| `docs/workflow/TASK_START_CARD.md` | 任务启动卡模板，记录 Router 分类、base version、写入位置、agents、硬门和阻断条件。 |
| `docs/workflow/FIRST_CLOSED_LOOP.md` | 首条工作流闭环指南，先验证 readiness、tune-suggest 和低风险 confirmation 通路。 |
| `docs/workflow/git_policy.md` | Git 分支、tag、push、trial 快照和命名规则。 |
| `docs/workflow/versioning.md` | baseline 版本、父节点、版本树和提升规则。 |
| `docs/workflow/idea_tree_protocol.md` | 创意树协议，规定 idea 节点、来源、评分、跨版本复用和排序。 |
| `docs/workflow/paper_intake.md` | 论文投递、阅读状态、来源复核、候选 idea 提取和 GitHub 轻量创意同步流程。 |
| `docs/workflow/module_trial_protocol.md` | 模块 trial 协议，规定 trial 目录、分支、tag、必填记录和决策类型。 |
| `docs/workflow/code_interface_contract.md` | 代码接口契约，规定新模块输入输出、shape、loss、eval、开关和最低验证。 |
| `docs/workflow/innovation_code_review_protocol.md` | 创新代码多 agents 多轮审查协议，规定 idea/source intent、接口设计、code diff 和 post-run evidence 四轮 review。 |
| `docs/workflow/code_interface.md` | 代码接口补充说明，用于承接更具体的接口约束。 |
| `docs/workflow/experiment_protocol.md` | tune、ablation、confirmation 实验协议。 |
| `docs/workflow/artifact_policy.md` | GitHub 轻量边界和外部资产职责。 |
| `docs/workflow/ARTIFACT_REGISTRATION.md` | 外部 artifact 登记动作规范，规定 Warehouse 路径、artifact id、URI、hash、size 和 manifest/result 引用。 |
| `docs/workflow/result_index_protocol.md` | `manifest.yaml`、`result.yaml`、`result.md` 的结果索引协议。 |
| `docs/workflow/agent_contracts.md` | agents 的长期 IO 契约、自我介绍、读写边界和失败条件。 |
| `docs/workflow/agent_report_policy.md` | agent 工作凭证保存规范，保留审计摘要，不保存完整聊天流水。 |
| `docs/workflow/agent_orchestration.md` | 多 agents 编排、GPU 串行、实验类型分工和本地 skill 同步规则。 |
| `docs/workflow/quality_gate.md` | 普通实验证据检查和 baseline promotion 强制门。 |
| `docs/workflow/promotion.md` | 从 trial/result 到新版本 tag 的提升规范。 |
| `docs/workflow/progress_dashboard.md` | 未来本地只读看板协议。 |
| `docs/workflow/runbook.md` | 常见操作手册。 |
| `docs/workflow/issues/` | 日期化实验问题知识库，保存具体问题、解决方案和预防规则。 |

### 2.6 agents 目录

| 路径 | 作用 |
|---|---|
| `docs/workflow/agents/README.md` | agents 总入口，说明共享角色和按实验类型编排的关系。 |
| `docs/workflow/agents/shared_roles/coordinator/profile.md` | Coordinator 自我介绍和职责：拆任务、分配 agents、维护状态，不直接改模型。 |
| `docs/workflow/agents/shared_roles/reader_planner/profile.md` | Reader/Planner 自我介绍和职责：读论文、抽取来源、形成候选 idea，不跑实验。 |
| `docs/workflow/agents/shared_roles/implementer/profile.md` | Implementer 自我介绍和职责：按接口契约写代码，不能改评估语义。 |
| `docs/workflow/agents/shared_roles/interface_checker/profile.md` | Interface Checker 自我介绍和职责：检查 shape、class order、label mapping、eval 语义。 |
| `docs/workflow/agents/shared_roles/runner/profile.md` | Runner 自我介绍和职责：独占 GPU 运行实验，把日志和大文件写到 Warehouse。 |
| `docs/workflow/agents/shared_roles/log_analyst/profile.md` | Log Analyst 自我介绍和职责：读取外部日志，抽取 U/S/H/ZS、best epoch、失败原因。 |
| `docs/workflow/agents/shared_roles/result_analyst/profile.md` | Result Analyst 自我介绍和职责：比较结果、写结论、标注可比性。 |
| `docs/workflow/agents/shared_roles/quality_checker/profile.md` | Quality Checker 自我介绍和职责：检查证据链、manifest/result、质量门。 |
| `docs/workflow/agents/shared_roles/reviewer/profile.md` | Reviewer 自我介绍和职责：做最终审查，关注风险、缺失测试和规范偏离。 |
| `docs/workflow/agents/by_experiment/tune/agents/README.md` | tune 实验的 agents 编排。 |
| `docs/workflow/agents/by_experiment/ablation/agents/README.md` | ablation 实验的 agents 编排。 |
| `docs/workflow/agents/by_experiment/innovation/agents/README.md` | innovation/module trial 的 agents 编排。 |
| `docs/workflow/agents/by_experiment/confirmation/agents/README.md` | confirmation 实验的 agents 编排。 |
| `docs/workflow/agents/by_experiment/promotion/agents/README.md` | promotion 的 agents 编排。 |

GitHub 轻量化以后，agents 边界必须跟着变化：

- Reader/Planner 可以读外部 Research，但只把最小 idea 索引回写 GitHub。
- Runner 可以写外部 Warehouse，但不能把 raw logs、checkpoint 或 generated figures 写进 GitHub。
- Log Analyst 读取 Warehouse 日志，只把指标摘要、artifact 引用和失败分类写回 GitHub。
- Implementer 只改代码和配置，不负责解释日志。
- Interface Checker 是硬门：标注、split、class order、metric semantics 不清楚时，Runner 和 Result Analyst 都不能继续把结果当有效结论。

### 2.7 workflow 工具层

| 路径 | 作用 |
|---|---|
| `workflow/README.md` | 结构辅助工具说明和 runtime 入口。 |
| `workflow/gtpj_workflow.py` | CLI helper，负责 validate、audit-boundary、new-experiment、record-result、new-idea、new-trial、set-current-version 等结构性动作。 |
| `workflow/codex/README.md` | Codex 接入参考。 |
| `workflow/openclaw/README.md` | OpenClaw 接入参考。 |
| `workflow/openclaw/agent_roles.md` | OpenClaw 多角色参考。 |

当前 helper 是结构辅助层，不是替你做研究判断的黑盒。它负责让目录、索引、artifact 和基本规则不乱。

真实任务开始前，Coordinator 仍必须用 `TASK_START_CARD.md` 自动输出任务类型、写入边界、
agents 和 hard gates。Owner 不负责填写这张卡。只要会产生 raw evidence，就必须同时遵守
`ARTIFACT_REGISTRATION.md`。

### 2.8 schema 和测试

| 路径 | 作用 |
|---|---|
| `schemas/manifest.schema.json` | `manifest.yaml` 的结构约束。 |
| `schemas/result.schema.json` | `result.yaml` 的结构约束。 |
| `schemas/artifact_ref.schema.json` | artifact 引用结构约束，要求记录 id、URI、hash、size 等。 |
| `tests/test_gtpj_workflow.py` | workflow helper 的单元测试。 |

schema 的意义是防止“看起来写了记录，实际不可复现”。尤其是 label mapping、split、class order、metric semantics 这类字段，不能靠口头记忆。

### 2.9 创意树 `idea_tree/`

GitHub 里的 `idea_tree/` 是轻量索引，不是完整论文阅读库。

| 路径 | 作用 |
|---|---|
| `idea_tree/README.md` | 创意树入口说明。 |
| `idea_tree/创意树.md` | 中文入口，解释创意树文件分工。 |
| `idea_tree/idea_tree.json` | 机器可读的最小事实源，保存 idea id、状态、评分、版本适配、linked trials。 |
| `idea_tree/schema.json` | 创意树 JSON 结构约束。 |
| `idea_tree/INDEX.md` | 给人看的总索引，由 `idea_tree.json` 派生。 |
| `idea_tree/versions/v1.md` | v1 视角下的候选创意清单。 |
| `idea_tree/inbox.md` | 临时想法收件箱，尚未成为正式 `IDEA-xxxx`。 |
| `idea_tree/queues/01_selected_next.md` | 已选中的下一步候选。 |
| `idea_tree/queues/02_module_candidates.md` | 当前模块候选队列。 |
| `idea_tree/queues/03_ablation_questions.md` | 消融问题队列。 |
| `idea_tree/queues/04_tuning_questions.md` | 调参问题队列。 |
| `idea_tree/sources/papers_index.md` | GitHub 内的轻量论文来源索引。完整论文笔记在外部 Research。 |
| `idea_tree/sources/source_notes/` | 轻量来源摘要或复核摘要。完整阅读材料不放这里。 |
| `idea_tree/ideas/.gitkeep` | 保留空目录。正式 idea 可生成 `IDEA-xxxx_slug/IDEA.md`。 |

创意树规则：

- 完整论文阅读、完整创意树、长笔记和图片放 `GTPJ_Research`。
- GitHub 只保留能连接实验的轻量 idea 节点。
- `global_score` 表示总体价值，`version_scores.vX` 表示相对某个 base version 的价值。
- 一个 idea 只有来源、假设、接口影响、评估风险和版本适配清楚后，才能进入 trial。
- `set-current-version` 只改变创意树视图，不改变 `main` active code。

### 2.10 实验账本 `experiments/`

GitHub 里的 `experiments/` 是轻量实验索引，不是实验资产仓库。

| 路径 | 作用 |
|---|---|
| `experiments/README.md` | 实验记录目录说明。 |
| `experiments/EXPERIMENT_REGISTRY.md` | 全局实验登记表，记录所有正式实验、trial、状态和结论。 |
| `experiments/VERSION_TREE.md` | 版本树账本，记录每个正式 baseline 的父节点、tag、来源和指标。 |
| `experiments/LEGACY_POLICY.md` | 边界收口前历史证据迁移规则。 |
| `experiments/templates/experiment_README_template.md` | 普通实验 README 模板。 |
| `experiments/templates/agent_summary_template.md` | agent 工作凭证模板。 |
| `experiments/templates/TRIAL_README_template.md` | trial README 模板。 |
| `experiments/templates/TRIAL_ATTEMPTS_template.md` | module trial 内部多次 attempt 总表模板。 |
| `experiments/templates/implementation_template.md` | 模块实现记录模板。 |
| `experiments/templates/quality_check_template.md` | 质量检查模板。 |
| `experiments/templates/IDEA_template.md` | idea 文件模板。 |
| `experiments/templates/VERSION_template.md` | 版本说明模板。 |
| `experiments/module_trials/INDEX.md` | 模块 trial 索引。 |
| `experiments/v1/VERSION.md` | v1 版本说明。 |
| `experiments/v1/config.yaml` | v1 配置归档副本。 |
| `experiments/v1/result.md` | v1 结果摘要。 |
| `experiments/v1/baseline/README.md` | v1 baseline 证据说明。 |
| `experiments/v1/baseline/config.yaml` | v1 baseline 实验配置副本。 |
| `experiments/v1/baseline/manifest.yaml` | v1 baseline 复现地图，记录配置、代码、环境、数据和外部 artifact 引用。 |
| `experiments/v1/baseline/result.yaml` | v1 baseline 机器可读结果。 |
| `experiments/v1/baseline/quality_check.md` | v1 baseline 质量检查记录。 |
| `experiments/v1/tune/INDEX.md` | v1 tune 实验索引。 |
| `experiments/v1/ablation/INDEX.md` | v1 ablation 实验索引。 |
| `experiments/v1/confirmation/INDEX.md` | v1 confirmation 实验索引。 |
| `experiments/v2/VERSION.md` | v2 版本说明。 |
| `experiments/v2/config.yaml` | v2 配置归档副本。 |
| `experiments/v2/result.md` | v2 结果摘要。 |
| `experiments/v2/baseline/README.md` | v2 baseline 证据说明。 |
| `experiments/v2/baseline/config.yaml` | v2 baseline 实验配置副本。 |
| `experiments/v2/baseline/manifest.yaml` | v2 baseline 复现地图，记录配置、代码、环境、数据和外部 artifact 引用。 |
| `experiments/v2/baseline/result.yaml` | v2 baseline 机器可读结果。 |
| `experiments/v2/baseline/quality_check.md` | v2 baseline 质量检查记录。 |
| `experiments/v2/tune/INDEX.md` | v2 tune 实验索引。 |
| `experiments/v2/ablation/INDEX.md` | v2 ablation 实验索引。 |
| `experiments/v2/confirmation/INDEX.md` | v2 confirmation 实验索引。 |

每个新实验目录至少要包含：

```text
README.md
config.yaml
manifest.yaml
result.yaml
result.md
quality_check.md
agent_summary.md
```

trial 还要包含：

```text
implementation.md
code.diff
Trial Flow in README.md or flow.md
```

实验目录不允许包含：

```text
raw logs
checkpoint
cache
generated figures
大体积表格导出
临时可视化文件
```

这些内容放到 `GTPJ_Warehouse`，GitHub 只记录 artifact 引用。

## 3. 本地外部目录结构

外部目录和 GitHub 仓库平级，不进入 GitHub。

### 3.1 本地路径配置 `.gtpj/`

| 路径 | 作用 |
|---|---|
| `.gtpj/local_paths.example.yaml` | 可提交的示例路径配置，告诉别人本地目录应该怎么映射。 |
| `.gtpj/local_paths.yaml` | 你机器上的真实路径配置，包含本地绝对路径，不提交。 |

推荐内容：

```yaml
warehouse_root: D:/backup/Documents/Myself/GTPJ_Warehouse
research_root: D:/backup/Documents/Myself/GTPJ_Research
```

### 3.2 `GTPJ_Research`

```text
D:\backup\Documents\Myself\GTPJ_Research
|-- README.md
|-- IDEA_REGISTRY.yaml
|-- papers/
|-- notes/
|-- ideas/
`-- source_reviews/
```

| 路径 | 作用 |
|---|---|
| `README.md` | 说明 Research 目录的角色和使用边界。 |
| `IDEA_REGISTRY.yaml` | 本地完整创意注册表，可比 GitHub idea index 更细。 |
| `papers/` | PDF、论文补充材料、bib、下载源等。 |
| `notes/` | 完整论文阅读笔记。 |
| `ideas/` | 长版创意树、推导、失败思路、图片草图。 |
| `source_reviews/` | 对论文来源、方法可行性、相似工作和 claim 的复核记录。 |

Research 的职责：

- 保存“为什么有这个创意”的完整上下文。
- 支持 Reader/Planner 找来源、做比较、避免重复造轮子。
- 不承担实验结果事实源；实验结果事实源在 GitHub 轻量账本和 Warehouse artifact。

Research 和 GitHub 的联动规则：

- 论文、来源复核、新机制和长版推理先写 Research。
- 稳定事实、idea id、版本评分、linked trials、next_action 和证据 URI 写 GitHub。
- 如果 Research 中的判断会影响实验选择、version score、trial 结论或 promotion，必须在同一任务内
  同步 GitHub 轻量索引。
- 如果只是普通 tune / confirmation 结果，不产生新的机制判断，Research 可以不更新，但启动卡和收尾
  必须写明 skip reason。

### 3.3 `GTPJ_Warehouse`

```text
D:\backup\Documents\Myself\GTPJ_Warehouse
|-- README.md
|-- ARTIFACT_REGISTRY.yaml
|-- runs/
|-- logs/
|-- checkpoints/
|-- figures/
|-- tables/
`-- failure_cases/
```

| 路径 | 作用 |
|---|---|
| `README.md` | 说明 Warehouse 是大型实验资产事实源。 |
| `ARTIFACT_REGISTRY.yaml` | 外部 artifact 总登记表，记录 artifact id、URI、hash、size、来源实验。 |
| `runs/` | 每次运行的本地运行目录，可包含 stdout、环境快照和中间文件。 |
| `logs/` | raw logs。GitHub 只保存日志 artifact 引用。 |
| `checkpoints/` | checkpoint、best model、临时权重。 |
| `figures/` | 实验可视化输出、训练曲线、失败案例图。 |
| `tables/` | 实验统计导出、CSV、Excel、指标汇总。GitHub 只放摘要结论。 |
| `failure_cases/` | 失败样本、错误可视化、诊断材料。 |

Warehouse 的职责：

- 保存“实验实际产生了什么”的大文件证据。
- 给 Log Analyst 和 Quality Checker 提供可核对材料。
- 给 GitHub 的 `manifest.yaml` / `result.yaml` 提供 artifact id、URI、hash、size。

## 4. Git 分支、tag 和版本规范

### 4.1 长期分支

| 名称 | 作用 |
|---|---|
| `main` | 唯一长期分支。保存当前治理规范、代码、配置、轻量实验账本。 |

不建议长期保留 `v1`、`v2` 这类分支。`vX` 是 tag 和实验目录，不是长期分支。

### 4.2 正式版本 tag

| tag | 作用 |
|---|---|
| `v1` | `GTPJ-v1` 正式 baseline 快照。 |
| `v2` | `GTPJ-v2` 正式 baseline 快照，当前 active mainline。 |
| `v3`、后续 `vX` | 未来 promotion 后创建的新 baseline 快照。 |

正式版本关系：

```text
一个 vX = 一个 baseline = 一个 Git tag = 一个 experiments/vX/ 目录 = 一个 VERSION_TREE 节点
```

### 4.3 trial 快照 tag

trial 可以有永久快照 tag：

```text
trial/v1/idea-0001/trial-001
trial/v2/idea-0003/trial-002
```

用途：

- 锁定某次重要 trial 的代码快照。
- 让后续 promotion 能说明自己从哪个 trial 来。
- 不替代正式 `vX` tag。
- 不表示某个 `ATTEMPT-xxx`、某次调参结果或某个 best H 值。attempt 级证据写入
  `ATTEMPTS.md`、`attempts/ATTEMPT-xxx/`、commit hash 和 Warehouse artifact id。

### 4.4 临时分支

| 分支前缀 | 作用 |
|---|---|
| `exp/vX/tune/...` | 调参实验分支。 |
| `exp/vX/ablation/...` | 消融实验分支。 |
| `exp/vX/confirmation/...` | 复现实验或确认实验分支。 |
| `dev/vX/IDEA-xxxx/...` | 模块开发分支。 |
| `promote/vY/...` | promotion 准备分支。 |

规则：

- 分支名必须带 base version，例如 `v1`。
- 实验开始前必须确认当前分支 clean，且包含本地 `main` 历史。
- 合并或废弃后，临时分支可以删除；正式证据靠 tag、账本和外部 artifact 保留。
- 不自动 push。远端动作必须由 owner 明确要求。

## 5. 创意树工作流

### 5.1 从论文到 idea

```text
论文/PDF/阅读笔记
  -> GTPJ_Research/papers + notes + source_reviews
  -> Reader/Planner 复核来源、动机、可能模块接口
  -> GitHub idea_tree/inbox.md 或 idea_tree.json 轻量登记
  -> 形成 IDEA-xxxx
```

进入正式 idea 前必须明确：

- 来源论文或来源观察是什么。
- 想解决 GTPJ 的哪个问题。
- 影响哪个模块或哪条训练/评估链路。
- 是否改变输入输出、label mapping、class order、loss 或 metric semantics。
- 针对哪个 base version 有价值。

### 5.2 idea 评分

每个 idea 至少有两类评分：

| 字段 | 含义 |
|---|---|
| `global_score` | 不依赖具体版本的总体价值。 |
| `version_scores.vX` | 相对某个 base version 的价值。 |

为什么要分开：

- 一个创意可能理论上很好，但对当前 v1 接口风险太高。
- 一个创意可能只适合 v1 的缺陷，不一定适合未来 v3。
- promotion 后，老创意需要重新评估，不应自动继承旧优先级。

### 5.3 从 idea 到 trial

```text
IDEA-xxxx
  -> interface risk check
  -> new-trial
  -> experiments/module_trials/IDEA-xxxx_slug/TRIAL-xxx_slug/
  -> dev/vX/IDEA-xxxx/...
  -> trial tag
```

trial 通过前，不能进入正式版本。

trial 的决策类型：

| 决策 | 含义 |
|---|---|
| `promote` | 证据足够强，可进入 promotion 候选。 |
| `keep` | 有价值但暂不提升，需要更多实验。 |
| `revise` | 思路可能有价值，但接口、实现或证据要重做。 |
| `reject` | 证据不支持，归档。 |

## 6. 实验记账规范

### 6.1 实验必须记录什么

每个实验必须有：

- base version，例如 `v1`。
- 代码快照，例如 commit 或 tag。
- 完整配置副本 `config.yaml`。
- 数据集、split、seen/unseen class、class order、label mapping 说明。
- 评估脚本和 metric semantics。
- 外部日志 artifact 引用。
- 结果摘要和可比性判断。
- 质量检查结论。

除此之外，所有会产出正式证据的真实 run 都必须满足：

- run 前先把配置、副本和计划索引冻结成一次 `pre-run freeze commit`；
- `pre-run freeze commit` 之后 `git status --short` 必须为空；
- Runner 只能从这个 clean worktree 启动；
- 本次 run 必须能唯一映射到冻结后的 `run_commit`；
- run 后的 `manifest.yaml`、`result.yaml`、`result.md`、`quality_check.md`、artifact 注册和索引更新，必须进入单独的 `post-run result commit`；
- 如果真实 run 启动时工作树不干净，这次结果最多算 debug 证据，不能直接作为 `keep`、`best`、confirmation 或 promotion 依据。

### 6.2 `manifest.yaml`

`manifest.yaml` 是复现地图。它回答：

- 这次实验从哪个代码和配置来。
- 用了什么环境、数据、cache 和随机种子。
- 原始日志、checkpoint、图表等外部 artifact 在哪里。
- 每个 artifact 的 hash 和 size 是什么。
- 评估边界是否清楚。

### 6.3 `result.yaml`

`result.yaml` 是机器可读结果。它回答：

- U/S/H/ZS 等核心指标是多少。
- best epoch 是多少。
- 是否可和 baseline 对比。
- 是否满足质量门。
- 是否建议继续、重跑、拒绝或 promotion。

### 6.4 `result.md`

`result.md` 是给人看的结果说明。它回答：

- 这次实验结论是什么。
- 与 baseline 差多少。
- 结果是否可信。
- 失败或异常在哪里。
- 下一步建议是什么。

### 6.5 `quality_check.md`

`quality_check.md` 是质量检查记录。它回答：

- 配置是否完整。
- 代码快照是否明确。
- artifact 是否可追踪。
- 评估标注是否清楚。
- 是否存在不可比风险。
- 是否允许进入下一步。

### 6.6 `agent_summary.md`

`agent_summary.md` 是 agent 工作凭证。它回答：

- 本次实验启用了哪些 agents；
- 哪些 agents 被禁用，为什么；
- 每个 agent 检查了什么输入；
- 发现了哪些 blocking / non-blocking issue；
- 最终决策由哪些证据支持。

它不保存完整聊天流水，也不保存 raw logs。长报告进入 Warehouse，并通过 artifact id 引用。

## 7. 实验类型闭环

### 7.1 tune

目标：在不改变模型结构和评估语义的前提下找更好配置。

本节说的是 version-level tune：基于某个正式 baseline `vX` 调参数，写入 `experiments/vX/tune/`。
如果调的是某个 module trial 内部的 heads、ratio、dropout、seed 等 attempt 参数，写入该 trial 的
`ATTEMPTS.md` 和 `attempts/ATTEMPT-xxx/`，按 `module_trial_protocol.md` 处理。

流程：

```text
tune-suggest
  -> owner 选择候选
  -> exp/vX/tune/...
  -> new-experiment
  -> 写 config / 计划行并提交 pre-run freeze commit
  -> 确认 clean worktree，记录 run_commit
  -> Runner 独占 GPU 运行
  -> raw logs 写入 Warehouse
  -> Log Analyst 抽指标
  -> post-run result commit
  -> record-result 写回 GitHub 轻量索引
  -> Quality Checker 检查
  -> Result Analyst 写结论
```

tune 不允许：

- 改模型结构。
- 改数据划分。
- 改评估语义。
- 用不清楚的日志直接比较。

### 7.2 ablation

目标：验证某个模块或设计是否真的贡献了指标。

本节说的是 version-level ablation：基于某个正式 baseline `vX` 做消融，写入
`experiments/vX/ablation/`。如果只是解释某个 module trial 当前实现假设下的局部因素，
它是 trial-internal narrow ablation，写入该 trial 的 `ATTEMPTS.md` 和
`attempts/ATTEMPT-xxx/`。

流程：

```text
明确消融问题
  -> 固定 base config
  -> 只改变一个受控因素
  -> Runner 运行
  -> Log Analyst 抽指标
  -> Interface Checker 确认没有评估语义漂移
  -> Result Analyst 判断贡献
```

ablation 必须说明：

- 消融掉什么。
- 保留什么不变。
- 指标变化是否超过随机波动。
- 是否有额外副作用。

### 7.3 innovation / module trial

目标：验证新 idea 或新模块是否值得进入正式版本。

流程：

```text
Reader/Planner 形成 IDEA-xxxx
  -> Interface Checker 预审
  -> Implementer 实现
  -> 最低代码验证
  -> 写 attempt config / ATTEMPTS 计划行并提交 pre-run freeze commit
  -> 确认 clean worktree，记录 run_commit
  -> Runner 运行 trial
  -> Log Analyst 抽指标
  -> post-run result commit
  -> Quality Checker 查证据
  -> Reviewer 查风险
  -> 决策 promote/keep/revise/reject
```

innovation 的硬规则：

- 必须有开关。
- 关闭开关必须回到 base behavior。
- 接口语义不清楚时不能跑正式结果。
- 只要 idea / 创新 / module trial 会落成代码改动，必须遵守 `innovation_code_review_protocol.md`。
- 必须使用 `real_multi_agent`，并完成 Review 0-3；临时 agents 可以开启，但必须加载长期角色文件并留下审查凭证。
- trial 通过不等于自动成为新版本。
- 同一个 `TRIAL-001` 可以有多个 `ATTEMPT-xxx`，用于记录同一实现假设下的参数尝试、小范围 follow-up ablation、rerun 或 debug-fix。
- trial 内部必须允许 `param_tune`、narrow `ablation` 和 clean `confirmation`，否则无法判断这个模块到底好不好。
- `ATTEMPTS.md` 是 trial 内部的人读总表；单次 attempt 的复现证据放在 `attempts/ATTEMPT-xxx/`。
- trial 根目录的 `README.md`、`result.yaml`、`quality_check.md` 只汇总当前用于决策的 `best_attempt_id`。
- 如果变化已经超出小范围参数或局部诊断，形成新的实现假设，就新开 `TRIAL-002`，不要继续堆在 `TRIAL-001`。
- 旧 trial 如果只有一次 root-level attempt，可以作为历史证据保留；但从这条规则开始新增的 attempt 必须进入 `ATTEMPTS.md`。
- 真实 attempt run 不允许在 dirty worktree 上启动，也不允许在未提交 attempt config 和计划行时直接开跑。

### 7.4 confirmation

目标：确认一个已有结果能复现，或确认某个 promotion 候选不是偶然。

本节说的是 version-level confirmation，写入 `experiments/vX/confirmation/`。如果确认对象是某个
module trial 的 `best_attempt_id`，则写入该 trial 的 `ATTEMPTS.md` 和 `attempts/ATTEMPT-xxx/`，
作为 trial-internal clean confirmation。

流程：

```text
选择待确认结果
  -> 固定配置和代码快照
  -> 提交 pre-run freeze commit
  -> 确认 clean worktree，记录 run_commit
  -> 改 seed 或重新跑
  -> 检查日志和指标
  -> post-run result commit
  -> 判断是否稳定
```

confirmation 必须说明：

- 确认对象是谁。
- 与原结果的差异是多少。
- 是否仍满足质量门。
- 这次确认运行引用的 `run_commit` 是什么。

### 7.5 promotion

目标：把一个通过证据链的 trial 或实验提升为新 baseline。

流程：

```text
promotion_decision: promote
promote_to: vY
evidence_level: baseline_grade
confirmation_status: confirmed
  -> Quality Checker 硬门
  -> Reviewer 复核接口、评估、证据和可复现性
  -> 建立 config/versions/vY.yaml
  -> 建立 experiments/vY/
  -> 更新 VERSION_TREE
  -> 创建本地 vY tag
  -> main 保留账本
  -> active version 只有 owner 明确要求时才切换
```

promotion 不会自动做的事：

- 不自动改远端。
- 不自动把 `main` active code 切到新版本。
- 不自动删除旧版本账本。
- 不自动把外部大文件复制进 GitHub。

## 8. 评估标注和代码接口硬门

任何实验只要出现以下问题，就不能作为有效结果：

- seen/unseen split 没写清楚。
- class order 没写清楚。
- label mapping 没写清楚。
- logits 对应类别不清楚。
- U/S/H/ZS 的计算语义不清楚。
- zero-shot 和 generalized zero-shot 混用。
- train/test 数据来源或 cache 版本不清楚。
- 新模块关闭后不能回到 base behavior。

Runner 的拒绝条件：

- `config.yaml` 不完整。
- 评估标注缺失。
- 输出目录会把 raw logs 或 checkpoint 写进 GitHub。
- GPU lock 已存在。
- 当前分支不 clean，或者不是预期实验分支。

Result Analyst 的拒绝条件：

- 日志无法解析。
- 指标语义不明。
- artifact hash/size 缺失。
- 与 baseline 不可比，但报告里没有明确标注。

Quality Checker 的拒绝条件：

- `manifest.yaml`、`result.yaml`、`result.md`、`quality_check.md` 任一缺失。
- 外部 artifact 无法定位。
- schema 字段缺失或明显不一致。
- promotion 候选缺少 confirmation 或 reviewer 复核。

## 9. agents 工作边界

### 9.1 共享原则

- 一个代码路径同一时间只能有一个 writer。
- Runner 串行占用 GPU。
- 能读外部目录的 agent，不等于能把外部材料写回 GitHub。
- 所有 agents 都要先读对应规范文件，再行动。
- 任何 agent 发现评估语义不清楚，都必须停止把结果当作有效结论。
- Coordinator 不能临场自由决定是否使用多 agents；每次任务启动卡必须显式记录 `agents.activation_mode`、`activation_reason`、`decision_basis`、`required_roles`、`required_real_agents`、`tool_support`、`single_agent_allowed` 和 `memory_policy`。

### 9.1.1 Agent 启用模式

GTPJ 任务只有两种 agent 启用模式：

| 模式 | 含义 | 适用范围 |
|---|---|---|
| `role_only` | 一个主 agent 按多个角色清单串行执行，并在 `agent_summary.md` 记录各角色检查结果。 | 只读解释、状态检查、配置查看、窄范围 rerun / confirmation 准备、账本格式整理。 |
| `real_multi_agent` | 启动或委派独立 agent / reviewer / checker 执行对应角色，保留独立输入、发现和结论。 | 代码语义变更、接口风险、promotion、争议结果、owner 明确要求多 agents。 |

如果当前 Codex 环境没有真实 sub-agent / multi-agent 工具，不能把 `role_only` 写成
`real_multi_agent`。`role_only_with_independent_sequential_review` 不是第三种 `activation_mode`，
只能写在 `agents.tool_support.fallback_mode` 中：

```yaml
agents:
  activation_mode: role_only
  tool_support:
    real_multi_agent_available: false
    fallback_mode: role_only_with_independent_sequential_review
```

该 fallback 不能用于 promotion、正式 best 结论或 owner 已明确要求真实多 agents 的任务，
除非 owner 明确接受它只作为 debug/smoke 证据。

`required_real_agents` 是真实 sub-agent 硬需求角色列表；`real_multi_agent` 时填写必须独立执行的
角色，`role_only` 时填写 `[]`。

必须使用 `real_multi_agent` 的情况：

- owner 明确说“用多 agents”“多 agents 验证”“独立 review”；
- 修改模型结构、forward、loss、eval、数据流、label mapping、seen/unseen split、class order 或 logits shape；
- 新 module trial 的实现阶段、接口检查阶段或 promotion 前复核；
- 结果异常或争议较大，例如明显低于预期、指标大幅波动、和 baseline 不可比，或 owner 对解释提出质疑；
- 准备写 `promotion_decision: promote`、创建新 `vX`、打 version tag；
- 任务需要同时阅读论文、源码、日志和质量证据，且这些输入可以被不同角色独立检查。
- 同一结论会影响论文实验路线、baseline 选择或下一轮大成本实验。

允许使用 `role_only` 的情况：

- 只读解释、定位文件、查看配置、普通状态汇报；
- 不改代码、不改实验语义的窄范围 rerun / confirmation 准备；
- 单一 Runner 按 frozen config 串行训练；
- 结果只记为 debug/smoke，不作为 keep / best / promote / confirmation evidence；
- 账本格式整理，且不改变实验结论。

如果 owner 对 `activation_mode` 提出异议，Coordinator 必须暂停真实 run，先修正启动卡或升级为 `real_multi_agent`。

### 9.1.2 Agent 记忆规则

Agent 不能把隐藏聊天记忆当作实验事实源。事实源优先级是：

1. 当前仓库文件、commit、tag、实验账本、config、manifest、result、quality check。
2. Warehouse / Research 中被 artifact id、URI、hash、size 引用的外部证据。
3. 当前对话中 owner 明确给出的任务约束。
4. Codex 全局 memory 或历史会话摘要，只能用于快速定位和背景提醒，必须回到当前仓库或 artifact 验证后才能入账。

真实多 agent 下，每个 agent 只自动拥有自己收到的任务说明、被显式传入的文件和当前工具可见上下文。
它们不应假定自己拥有主 agent 的全部隐藏记忆。Coordinator 如果依赖历史记忆，必须在任务说明里显式写出，
并要求 agent 回到当前仓库验证。

`agent_summary.md` 必须记录：

- `memory_used`
- `memory_sources`
- `verified_against_current_repo`
- `agent_instance_type`
- `independence_scope`

没有经过当前仓库或 artifact 验证的 memory-derived fact，不能写入 `result.yaml`、`quality_check.md`、
promotion 证据或正式结论。

### 9.1.3 当前 ATTEMPT-007 的 agent 结论

CLIP-A-self ATTEMPT-007 是 ATTEMPT-003 配置的干净 confirmation run，但 owner 已经质疑流程、
结果解释和多 agent 使用边界。因此本轮应按 `real_multi_agent` 处理。启用：

```text
Coordinator
Runner
Log Analyst
Quality Checker
Result Analyst
Reviewer
```

不启用 Implementer 和 Interface Checker，除非 ATTEMPT-007 前修改训练代码、loss、eval、数据流、
label mapping、seen/unseen split、class order、logits shape 或 metric semantics。

### 9.2 角色分工

| 角色 | 主要输入 | 主要输出 | 禁止事项 |
|---|---|---|---|
| Coordinator | owner 目标、当前规范、仓库状态 | 任务拆解、agent 分配、状态同步 | 直接改模型或伪造结果 |
| Reader/Planner | Research 论文和笔记 | idea 候选、来源摘要、风险点 | 跑实验、改代码 |
| Implementer | idea、接口契约、base config | 代码改动、实现说明、最低验证 | 改评估语义但不记录 |
| Interface Checker | 代码、config、评估脚本 | 接口检查结论 | 忽略标注风险 |
| Runner | config、代码快照、GPU lock | 外部运行日志、artifact | 把大文件写进 GitHub |
| Log Analyst | Warehouse 日志 | 指标摘要、失败分类 | 在语义不清时给结论 |
| Result Analyst | result、baseline、实验目标 | 对比结论、下一步建议 | 把不可比结果当提升依据 |
| Quality Checker | manifest/result/artifact/schema | 质量门结论 | 放过缺失证据链 |
| Reviewer | 全部轻量证据和关键代码 | 风险审查、是否可合并建议 | 只写总结不列风险 |

### 9.3 按实验类型使用 agents

| 实验类型 | 必需 agents |
|---|---|
| 只读状态 / 配置检查 | Coordinator，必要时 Reader/Planner |
| 调参建议 | Coordinator、Reader/Planner、Result Analyst |
| tune 真实运行 | Coordinator、Runner、Log Analyst、Result Analyst、Quality Checker |
| ablation | Coordinator、Runner、Log Analyst、Interface Checker、Result Analyst、Quality Checker |
| innovation/module trial | Coordinator、Reader/Planner、Implementer、Interface Checker、Runner、Log Analyst、Result Analyst、Quality Checker、Reviewer |
| confirmation | Coordinator、Runner、Log Analyst、Result Analyst、Quality Checker |
| promotion | Coordinator、Quality Checker、Reviewer、Result Analyst，必要时 Interface Checker |
| debug / smoke | Coordinator、Runner、Log Analyst，必要时 Interface Checker |

## 10. 标准命令入口

以下命令只作为结构辅助，不能替代 owner 判断。完整命令索引见 `workflow/README.md`；
owner 人话入口见 `docs/workflow/QUICK_START.md`。

日常开工前可先用只读 mini 卡确认路由：

```powershell
python workflow\gtpj_workflow.py start --phrase "开新模块"
```

常用结构检查：

```powershell
python workflow\gtpj_workflow.py status
python workflow\gtpj_workflow.py validate
python workflow\gtpj_workflow.py audit-boundary
python workflow\gtpj_workflow.py validate-remote
```

module trial attempt 收口优先用 helper 闭环：

```powershell
python workflow\gtpj_workflow.py record-module-attempt --trial-dir <trial-dir> --attempt-id ATTEMPT-001 --log <external-log> --decision keep
python workflow\gtpj_workflow.py sync-trial-summary --trial-dir <trial-dir> --attempt-id ATTEMPT-001 --decision keep
python workflow\gtpj_workflow.py closeout-check --trial-dir <trial-dir> --attempt-id ATTEMPT-001
```

## 11. 完整闭环

### 11.1 从 idea 到新版本

```text
1. 记录来源或想法
   Research 可保存长推理；GitHub 只保存轻量 idea/source 索引。

   如果来源或想法会影响后续实验选择，Research 和 GitHub 轻量索引必须在同一任务收尾前同步。

2. 进入创意树
   GitHub 保存最小 idea 索引，记录来源、假设、版本评分、接口风险。

3. 选择 trial
   Coordinator 和 Reader/Planner 选定一个 idea，Interface Checker 预审。

4. 实现模块
   Implementer 按接口契约写代码，保留开关和 base behavior。

5. 跑实验
   Runner 独占 GPU，日志和大文件进 Warehouse。

6. 读日志
   Log Analyst 从 Warehouse 抽指标，写轻量结果。

7. 查质量
   Quality Checker 检查 manifest/result/artifact/schema。

8. 形成结论
   Result Analyst 判断 keep/revise/reject/promote。

9. 确认和消融
   对 trial best attempt 做 trial-internal clean confirmation；必要时做 trial-internal narrow ablation。
   若确认对象已经是正式 baseline 版本，再写入 `experiments/vX/confirmation/` 或 `experiments/vX/ablation/`。

10. 提升版本
    promotion 通过后创建 vY 配置、账本、tag。

```

### 11.2 每一步事实源

| 问题 | 事实源 |
|---|---|
| 代码是什么 | GitHub code + tag/commit |
| 配置是什么 | GitHub `config.yaml` / `config/versions/vX.yaml` |
| 为什么做 | Research 完整材料 + GitHub idea index |
| 怎么跑 | GitHub `manifest.yaml` |
| 原始输出在哪 | Warehouse artifact |
| 指标是多少 | GitHub `result.yaml` / `result.md` |
| 是否可信 | GitHub `quality_check.md` |
| 是否成为版本 | GitHub `VERSION_TREE.md` + tag |

## 12. 交付和审查标准

一次合格实验交付必须包含：

- GitHub 中有实验目录和登记表记录。
- GitHub 中有完整 `config.yaml`。
- GitHub 中有 `manifest.yaml`，且 artifact 可追踪。
- GitHub 中有 `result.yaml` 和 `result.md`。
- GitHub 中有 `quality_check.md`。
- 如果是正式版本或 module trial，GitHub 中有对应流程图。
- 外部 Warehouse 中有 raw log 或其他必要证据。
- 评估标注、split、class order、metric semantics 明确。
- 结论中写明可比或不可比。

一次合格 promotion 必须额外包含：

- trial 或实验的完整证据链。
- 至少一个质量门复核结论。
- 必要的 confirmation 或 ablation。
- `config/versions/vY.yaml`。
- `experiments/vY/`。
- `experiments/VERSION_TREE.md` 更新。
- 本地 `vY` tag。
- owner 明确是否切换 active version。

## 13. 审阅清单

你读完后可以逐项确认：

- GitHub 是否只承担轻量控制面，而不是材料仓库。
- 默认实验 workflow 是否只依赖 Research/Warehouse。
- 创意树是否接受“外部完整材料 + GitHub 最小索引”的折中。
- 实验记账是否足够支撑复现。
- raw logs 不进 GitHub 是否可接受。
- artifact id/URI/hash/size 是否足够追踪证据。
- agents 边界是否符合你希望的自动化程度。
- 评估标注和代码接口硬门是否足够严格。
- `main` 唯一长期分支、`vX` 用 tag 是否符合你的版本管理直觉。
- promotion 不自动切换 active code 是否符合你的安全边界。

## 14. 下一阶段建议

建议下一阶段不要直接跑大实验，而是做一个“首轮干跑”：

```text
1. 选一个低风险 tune 候选。
2. 用 helper 创建实验目录。
3. 手工或 agent 检查 config/manifest/result 模板。
4. 用一份小日志或已有日志模拟 record-result。
5. 让 Interface Checker、Quality Checker、Result Analyst 按规范审查。
6. 根据暴露的问题修订本规范。
7. 规范稳定后，再进入正式实验闭环。
```

最终目标产品不是“多几个文件夹”，而是：

- owner 能一眼知道当前版本、下一步和证据状态。
- 每个结果能追踪到配置、代码、日志和评估语义。
- 每个 idea 能追踪到来源和 trial 证据。
- 每个新版本能追踪到父版本、promotion 决策和 tag。
- agents 能各司其职，不越权、不污染 GitHub、不把不可比结果当结论。
