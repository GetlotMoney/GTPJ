# GTPJ 规范落地状态清单

本文件回答一个问题：规范里写到的东西，哪些已经有实体文件，哪些还只是设计或按需创建。

维护规则：

- 新增规范时，必须在这里标注落地状态。
- 新建本地外部文件时，必须在这里记录路径。
- 暂不创建的未来文件，必须写明触发条件，不能只写“以后再说”。
- 本文件只记录状态，不替代具体规范；具体规则仍以 `GTPJ_WORKFLOW_SPEC.md` 和对应协议文件为准。

## 0. 状态定义

| 状态 | 含义 |
|---|---|
| `已落地` | 已有真实文件或目录，可以直接使用。 |
| `部分落地` | 顶层结构存在，但细分内容或自动化还不完整。 |
| `按需创建` | 不应提前创建，触发条件满足时再建。 |
| `设计中` | 只有规范或草案，还没有稳定文件/工具入口。 |
| `不创建` | 明确不应该创建，避免污染边界。 |

## 1. GitHub 规范与控制面

| 模块 | 状态 | 已有文件 | 说明 |
|---|---|---|---|
| Workflow Router | 已落地 | `docs/workflow/WORKFLOW_ROUTER.md` | 总教官/总路由文件，任何 GTPJ 任务先用它判断任务类型、是否进入创意树、写入位置、必读协议、agents 和 gate。 |
| Task Start Card | 已落地 | `docs/workflow/TASK_START_CARD.md` | 每次改文件、跑实验或登记结果前填写，记录 Router 分类、写入边界、agents、硬门和阻断条件。 |
| First Closed Loop | 已落地 | `docs/workflow/FIRST_CLOSED_LOOP.md` | 第一次开跑工作流时使用，先用 readiness check / tune-suggest / confirmation 验证闭环，不直接从复杂 module trial 开始。 |
| 总工作流规范 | 已落地 | `docs/workflow/GTPJ_WORKFLOW_SPEC.md` | owner 审阅入口，解释 GitHub、本地、创意树、实验、tag、agents 和闭环。 |
| workflow 入口 | 已落地 | `docs/workflow/README.md` | 记录阅读顺序。 |
| 仓库结构总账本 | 已落地 | `docs/PROJECT_STRUCTURE.md` | 记录稳定目录和文件职责。 |
| GitHub 治理 | 已落地 | `docs/GITHUB_GOVERNANCE.md` | 记录 main/tag/版本树/轻量边界。 |
| agent 规范 | 已落地 | `docs/workflow/agent_contracts.md`, `docs/workflow/agent_orchestration.md`, `docs/workflow/agents/` | 文件级角色边界已落地；真正运行时仍由 Codex/OpenClaw 按任务调用。 |
| agent 工作凭证 | 已落地 | `docs/workflow/agent_report_policy.md`, `experiments/templates/agent_summary_template.md` | 真实实验保存 agent 审计凭证，不保存完整聊天流水；helper 会为新实验创建 `agent_summary.md`。 |
| 代码接口硬门 | 已落地 | `docs/workflow/code_interface_contract.md`, `docs/workflow/code_interface.md` | 评估标注、label mapping、split、class order、metric semantics 不清楚时必须阻断。 |
| 实验结果索引 | 已落地 | `docs/workflow/result_index_protocol.md`, `schemas/manifest.schema.json`, `schemas/result.schema.json`, `schemas/artifact_ref.schema.json` | 规范和 schema 已有；每个新实验仍需实际填写。 |
| Artifact 登记动作 | 已落地 | `docs/workflow/ARTIFACT_REGISTRATION.md` | 规定 raw artifact 从本地文件到 Warehouse registry、manifest、result 的登记步骤。 |
| 质量门 | 已落地 | `docs/workflow/quality_gate.md` | 普通实验和 promotion gate 的检查规则。 |
| promotion | 已落地 | `docs/workflow/promotion.md` | promotion 规则已写；只有实验记录明确 `promotion_decision: promote` 才触发。 |
| 看板 runtime | 设计中 | `docs/workflow/progress_dashboard.md` | `.gtpj_runtime/` 只在真实运行时创建，纯规划不创建。 |

## 2. GitHub 轻量创意树

| 模块 | 状态 | 已有文件 | 说明 |
|---|---|---|---|
| 机器总索引 | 已落地 | `idea_tree/idea_tree.json` | GitHub 里的轻量事实源。 |
| 人类总索引 | 已落地 | `idea_tree/INDEX.md` | 由轻量索引派生的人读清单。 |
| v1 版本视图 | 已落地 | `idea_tree/versions/v1.md` | v1 视角下的轻量创意清单。 |
| idea 目录 | 已落地 | `idea_tree/ideas/.gitkeep` | 具体 idea 只有来源明确后再创建。 |
| v2 版本视图 | 按需创建 | `idea_tree/versions/v2.md` | 只有正式产生 `v2` 后再创建。 |

## 3. 本地 Research

根目录：

```text
D:\backup\Documents\Myself\GTPJ_Research
```

| 模块 | 状态 | 已有文件 | 说明 |
|---|---|---|---|
| Research 顶层说明 | 已落地 | `README.md` | 说明本地研究材料库职责。 |
| 本地 idea 注册表 | 已落地 | `IDEA_REGISTRY.yaml` | 当前为空，等正式 idea 进入后填写。 |
| 完整创意树总入口 | 已落地 | `ideas/MASTER_IDEA_TREE.md` | 保存长版推理、失败路线、跨版本判断。 |
| Research ideas 说明 | 已落地 | `ideas/README.md` | 说明本地完整创意树和 GitHub 轻量索引的关系。 |
| v1 本地创意视图 | 已落地 | `ideas/versions/v1.md` | `GTPJ-v1` 视角的长版创意筛选文件。 |
| 未来版本模板 | 已落地 | `ideas/versions/_template.md` | `v2`、`v3` 产生后从这里复制。 |
| v2 本地创意视图 | 按需创建 | `ideas/versions/v2.md` | 只有 `v2` tag 和 `experiments/v2/` 正式产生后再创建。 |
| 论文索引 | 已落地 | `papers/PAPERS_INDEX.md` | 记录论文、阅读状态和关联 idea。 |
| papers 说明 | 已落地 | `papers/README.md` | 说明 PDF 和补充材料的放置边界。 |
| 阅读笔记说明 | 已落地 | `notes/README.md` | 说明 `paper_notes/` 和 `method_notes/`。 |
| 来源复核索引 | 已落地 | `source_reviews/SOURCE_REVIEW_INDEX.md` | 记录来源复核和是否进入 idea tree。 |
| source_reviews 说明 | 已落地 | `source_reviews/README.md` | 说明复核内容和 trial 前置要求。 |

## 4. 本地 Warehouse

根目录：

```text
D:\backup\Documents\Myself\GTPJ_Warehouse
```

| 模块 | 状态 | 已有文件 | 说明 |
|---|---|---|---|
| Warehouse 顶层说明 | 已落地 | `README.md` | 说明 raw logs、checkpoint、experiment visualizations、experiment tables、failure cases 不进 GitHub。 |
| artifact 注册表 | 已落地 | `ARTIFACT_REGISTRY.yaml` | 已登记迁出的 v1 baseline log。 |
| raw logs 目录 | 已落地 | `logs/` | 真实实验日志写这里。 |
| checkpoint 目录 | 已落地 | `checkpoints/` | 权重和 checkpoint 写这里。 |
| figures 目录 | 已落地 | `figures/` | 实验可视化输出写这里。 |
| tables 目录 | 已落地 | `tables/` | 实验统计导出写这里。 |
| failure cases 目录 | 已落地 | `failure_cases/` | 失败样本和诊断材料写这里。 |
| run 细分目录 | 按需创建 | `runs/<run_id>/` | 只有真实实验运行时创建。 |

## 5. 本地路径映射

| 模块 | 状态 | 已有文件 | 说明 |
|---|---|---|---|
| 示例路径配置 | 已落地 | `.gtpj/local_paths.example.yaml` | 可提交的示例。 |
| 本机路径配置 | 已落地 | `.gtpj/local_paths.yaml` | 本机真实路径，不应提交。 |

## 6. 不应该创建的文件

| 文件类型 | 状态 | 原因 |
|---|---|---|
| GitHub 内 raw logs | 不创建 | raw logs 属于 Warehouse。 |
| GitHub 内 checkpoint | 不创建 | checkpoint 属于 Warehouse。 |
| GitHub 内 generated figures | 不创建 | 实验生成图属于 Warehouse。 |
| 未产生正式版本的 `vX.md` | 不提前创建 | 避免把未来版本误认为真实状态。 |
| 空的实验 run 目录 | 不提前创建 | run 目录必须对应真实运行。 |

## 7. 下次任务前的读取顺序

GTPJ 任务开始前，优先读取：

1. `docs/workflow/WORKFLOW_ROUTER.md`
2. `docs/workflow/TASK_START_CARD.md`
3. `docs/workflow/FIRST_CLOSED_LOOP.md`
4. `docs/workflow/GTPJ_WORKFLOW_SPEC.md`
5. `docs/workflow/IMPLEMENTATION_STATUS.md`
6. `docs/workflow/README.md`
7. 与任务类型相关的具体协议文件
8. `docs/workflow/ARTIFACT_REGISTRATION.md`
9. `.gtpj/local_paths.yaml`
10. 需要时再读本地 Research/Warehouse 对应 README

这样不需要 owner 每次口述哪些文件已经落地。
