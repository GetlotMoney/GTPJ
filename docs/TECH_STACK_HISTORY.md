# GTPJ 技术与工作流演进记录

## 版本类型说明

- `SYS-*`：系统功能和工作流规则。
- `UI-*`：人看的页面与图。
- `DATA-*`：台账、表格和结构化数据格式。
- `MODEL-*`：模型代码框架。
- `CONTENT-*`：论文或其他正文内容。
- `DOC-*`：教程、说明书和其他文档交付物。

## 当前版本一览

| 对象 | 当前版本 | 状态 | 实际内容 |
|---|---|---|---|
| 工作流 | `SYS-WORKFLOW-V7` | 已完成 | 治理/文档分支的当前 CUB 运行文件必须与正式干净母版一致；实验分支仍从准确母版 commit 独立分叉。 |
| 框架台账 | `DATA-FRAMEWORK-LEDGER-V2` | 已完成 | `framework.yaml` 使用历史来源指针，不再使用父子字段。 |
| 框架注册页面 | `UI-FRAMEWORK-REGISTRY-V3` | 已完成 | 本地 HTML 同级展示来源、各母版状态、四类实验数量和 V5 消融“已绑定、待实现”状态。 |
| 模型 | `MODEL-GTPJ-V5-MAIN-ALIGN-V1` | 已完成 | 主线 CUB 模型与配置恢复到 V1；运行身份和 GPU 评估设备边界修复后，冻结为 V2 母版，不改模型数学语义。 |
| 母版台账 | `DATA-FRAMEWORK-TEMPLATE-V1` | 已完成 | 已新增母版与实验起点身份，分开记录母版代码 commit 和后续 registry commit。 |
| V5 当前干净母版 | `MODEL-V5-TEMPLATE-V2` | 本地已冻结 | 分支、Tag、commit 均锁定到 `fb4b29b04087640890a532f105cb527d3a8c461b`；模型数学逻辑沿用 V1，只修正正式运行身份与 GPU 评估设备边界。 |
| V5 历史干净母版 | `MODEL-V5-TEMPLATE-V1` | 本地已冻结 | 分支、Tag、commit 仍锁定到 `2f5fa5e`，没有移动或覆盖。 |
| 代码教程 | `DOC-GTPJ-CODE-TUTORIAL-V1` | 已完成 | 六篇中文教程，解释仓库根目录模型、训练和工具代码，并明确正式 V5 母版边界。 |
| Git 管理关系图 | `UI-GIT-GOVERNANCE-MAP-V1` | 已完成 | 三页本地 HTML 区分管理分支、正式模型框架、母版、实验、PR、Tag，并展示本地与 GitHub 当前同步缺口。 |
| PLVSE 论文正文 | `CONTENT-PLVSE-V1` | 已完成 | 保存双语正文及交错排版 Markdown；不代表模型或工作流版本。 |
| PLVSE PDF 交付物 | `DOC-PLVSE-PDF-V1` | 已完成 | 保存同一正文的多种公式与双语排版 PDF；当前物理文件名保留历史 `CONTENT-PAPER-V1` 前缀。 |
| 实验执行工作流 | `SYS-WORKFLOW-V6` | 已完成 | 默认改为五步短流程；普通账本/参数只机器检查，代码修改固定两轮不同子 Agent 对抗式只读审核。 |
| 干净新框架候选 | `MODEL-CLEAN-V6-CANDIDATE` | RUN-001 已完成，继续修改 | `V5-INNOVATION-011` 的单次 H=61.1564，高于 009/010、低于 V5 74.44；仍不是正式 V6。 |

## 2026-08-13：CONTENT-PLVSE-V1 / DOC-PLVSE-PDF-V1（已完成）

- 本次改的是哪个对象：`CONTENT-PLVSE-V1` 是论文正文；`DOC-PLVSE-PDF-V1` 是由该正文生成的 PDF 交付物，二者不与 `MODEL-*` 或 `SYS-*` 共用版本号。
- 目标问题：把本地已有的 PLVSE 正文和渲染结果正式归入项目，避免散落在项目外或与代码提交混在一起。
- 采用技术：Markdown 保存可编辑正文；PDF 保存双语、交错排版和不同公式渲染的现有输出。
- 替换了什么：不替换模型、训练或工作流；只替代“论文资料未纳入项目目录”的状态。
- 实际可见效果与选择原因：正文和交付件统一位于 `docs/paper/`，可以随项目回查；当前文件保留生成时的 `CONTENT-PAPER-V1` 旧名，版本映射以本条为准，避免为了改名破坏已有引用。
- 已知限制与素材位置：多个 PDF 是同一正文的排版变体，不表示多个内容版本；素材均在 `docs/paper/`。
- 验证与回退：文件已纳入独立文档提交并通过 `git diff --check`；回退该文档提交即可移除，不影响代码、实验账本或训练结果。

## 2026-08-13：MODEL-GTPJ-V5-MAIN-ALIGN-V1 / SYS-WORKFLOW-V7（已完成）

- 本次改的是哪个对象：主线当前 CUB 运行代码，以及防止它再次混入实验代码的最小校验。
- 目标问题：正式干净母版已经冻结在 `2f5fa5e`，但 GitHub 主线仍保留历史动态路由和旧兼容层，导致新治理分支继续携带一份很长的累积模型。
- 采用技术：把模型、4 份配置和 V5 计算工具精确对齐到 `MODEL-V5-TEMPLATE-V1@2f5fa5e`；训练入口只增加大文件身份清单复用，并把这份运行代码登记为 `MODEL-V5-TEMPLATE-V2` 候选，不改模型、损失或评估。现有 `validate` 只认 `TEMPLATE.yaml.main_runtime_status: active`，并把它列出的 `runtime_files` 与母版 Git 内容逐项比较，不借用创意树查看版本。
- 替换了什么：替换主线中的累积式 V5 运行副本；不改历史 `v5` Tag、干净母版 Tag/commit、实验账本或训练结果。
- 实际可见效果：`model/MyModel.py` 从约 1357 个物理行恢复为 700 行；大缓存只在首次或身份变化时完整哈希；治理/文档分支若再次改动受管运行文件，校验会直接报出文件和母版 commit。
- 选择原因：主线只保存当前干净底稿，实验变化只留在各自分支，才能避免后续实验相互叠加。
- 已知限制：当前干净母版只保证 CUB；`train_GTPJ_AWA2.py` 和 `train_GTPJ_SUN.py` 仍是历史入口，不在本次兼容范围内。
- 素材位置：`experiments/v5/TEMPLATE.yaml`、`model/MyModel.py`、`train_GTPJ_CUB.py`、`tools/v5_*.py`、`workflow/gtpj_workflow.py`。
- 验证命令与结果：V5 专项 45 项、workflow 259 项和最终结构命令全部通过；两名不同 Reviewer 对最终提交 `378ed95` 按第 1 轮→第 2 轮顺序审核，均为 `pass`、阻断为 0；冻结后再次核对分支、Tag、账本与运行文件。
- 回退方式：回退本次提交即可恢复修复前主线副本；历史 Tag、母版提交、实验结果和 checkpoint 均不受影响。

## 2026-08-11：MODEL-CLEAN-V6-CANDIDATE（RUN-001 已完成，继续修改）

- 本次改的是哪个对象：下一代干净 GZSL 模型框架候选，不是正式 V6 框架。
- 目标问题：V5-INNOVATION-009/010 在保留旧频域、旧局部分支、拓扑和多辅助损失时均显著掉点，无法判断新句子交互机制本身是否合理。
- 采用技术：8 句话固定为 6 个局部部位、1 个全局描述、1 个独特判别特征；图像和文本共用单位初始化线性投影，局部/独特句直接软匹配全部 576 区域，全局句直接匹配 CLS，三项等权后只用主分类损失。
- 替换了什么：删除 PSE、FGVD/频域 Top-K、ICSA、BVSA、SGMP、BMDD、拓扑损失、global/local 辅助损失。
- 实际可见效果：`RUN-001` 最佳 epoch 1，`U/S/H/ZS=48.543394/82.624918/61.156447/76.156127`；高于 009/010 判断线 `59.4058`，但低于 V5 重复均值 `74.44`，所以保留为继续修改的候选，不能作为正式 V6 结果引用。
- 选择原因：先用最小干净路径取得可解释的候选结果，避免在核心路径尚未看清时继续堆复杂实验；本次不是与 009/010 的严格配对消融，不据此单独归因旧模块。
- 已知限制：单 seed 首跑只能判断是否值得继续；若有效，仍需重复训练和确认后才能 promotion 为 `FRAMEWORK-V6`。
- 素材位置：`idea_tree/ideas/IDEA-0013_clean_v6_candidate/IDEA.md`、`experiments/v5/innovation/INNOVATION-011_clean_v6_candidate/`。
- 验证命令与结果：最终完整测试 329 项通过、11 项按环境跳过；两名不同 Reviewer 对提交 `688f564` 依次审核，均为 `pass`、阻断为 0。服务器从该提交的干净隔离工作树完成 50 epoch；数据清单 SHA-256 为 `7b172e9a...175a`，结果见本实验 `result.md`。开跑时未调用旧 helper 生成启动收据，已在训练后执行记录中如实标明；该缺口不影响当前五步短流程下的单次方法判断，但本结果不得用于 confirmation 或 promotion。
- 回退方式：回退实验实现/冻结提交或放弃该实验分支；保留 IDEA 与历史账本，不影响已完成的 V5 实验结果、Tag 或 checkpoint。

## 2026-08-08：SYS-WORKFLOW-V6（已完成，2026-08-11 更新代码审核规则）

- 本次改的是哪个对象：实验从计划到服务器训练再到结果回填的执行流程。
- 目标问题：一次约一小时的训练，曾因专用控制器、双 GPU 锁、三波调度、Git bundle、永久编号、多层收据、制品哈希、三路审核和二次冻结，额外消耗约两小时准备与审核时间。
- 采用技术：五步短流程——唯一实验提交、配置与参数表、一次开跑检查、直接训练到独立 RUN 目录、一次结果回填；普通账本/参数只做机器检查，实验代码、workflow/helper、模板和训练配置生成逻辑改动固定两轮不同子 Agent 对抗式只读审核。
- 替换了什么：替换 `SYS-WORKFLOW-V5` 默认的多 agents/runtime/receipt/strict-3 执行门，也替换 2026-08-08 旧版“代码默认 1 轮审核”的口径；旧工具和旧证据原地保留，只作历史兼容或 owner 明确要求的特殊审计。
- 实际可见效果：参数实验准备上限 10 分钟；涉及代码或评估改动上限 30 分钟。正式论文实验也不再自动增加文件层级或审核轮数。2026-08-13 补上三个小防线：`validate` 会拒绝与 `idea_tree.json` 不一致的人读视图；参数表会用 `<removed>` 明确记录相对基线删除的配置字段；包装或直接书写的嵌套配置都按完整 YAML 值比较，并区分布尔值、空值和同名字符串，含糊的 `value` 混合字典直接拒绝。
- 选择原因：可复现的核心来自准确代码、配置、数据、种子、评估口径和完整结果；其余行政式步骤没有按比例提高科学可信度。
- 已知限制：旧 helper 和旧测试仍保留兼容入口，看到旧命令不代表新实验必须执行；后续只在真实重复问题出现时再做代码级瘦身，不先重构整套 helper。
- 素材位置：`AGENTS.md`、`docs/workflow/START_HERE.md`、`docs/workflow/WORKFLOW_KERNEL.md`、`docs/workflow/FRAMEWORK_EXPERIMENT_STANDARD.md`、`docs/workflow/playbooks/confirmation.md`。
- 验证命令与结果：`git diff --check`、`python workflow/gtpj_workflow.py validate-workflow-consistency`、`python workflow/gtpj_workflow.py validate` 均通过；2026-08-13 新增派生视图漂移、字段删除、嵌套值、类型碰撞、日期及非有限数负例后，完整测试 319 项通过、10 项按环境跳过。本条流程本身不启动训练。
- 回退方式：回退本次文档修改即可恢复旧默认门；不会改模型、训练代码、历史实验、分支、Tag、日志或 checkpoint。

## 2026-08-08：UI-GIT-GOVERNANCE-MAP-V1（已完成）

- 本次改的是哪个对象：人看的 Git 分支、Tag、新旧管理框架和污染边界说明图。
- 目标问题：管理工作流、正式模型框架、临时 PR 分支、实验分支和历史 Tag 被混在一起理解，容易误以为“分支或 Tag 多就会污染 main”。
- 采用技术：单文件自包含 HTML；分三页展示正确逻辑关系、2026-08-08 本地与 GitHub 实查引用、污染判断与安全处理顺序；不依赖服务或外部脚本。
- 替换了什么：不替换当前框架注册页 `UI-FRAMEWORK-REGISTRY-V3`；补充它未覆盖的 Git 物理引用和远端同步关系。
- 实际可见效果：一页可同时看清 `SYS-WORKFLOW-V5` 属于 `main`、未来新正式模型才建立平级 `framework/vN`、实验从只读母版独立分叉，以及 PR #2 合并会和不会带来什么。
- 选择原因：把“研究逻辑结构”和“Git 真实引用”分页后，既避免重新画成无限嵌套树，也能直观看出本地 36 条分支、GitHub 13 条分支和缺失母版 Tag 的同步现状。
- 已知限制：第二页是 2026-08-08 的静态快照，分支、Tag、PR 或远端 main 变化后需要重新实查更新；它不是机器事实源，也不执行清理或合并。
- 素材位置：`docs/diagrams/GTPJ_GIT_GOVERNANCE_MAP_UI-V1.html`。
- 验证命令与结果：HTML 的 `html`、`body` 标签各一组，三页和三个切换按钮完整；4 个本地链接全部存在；使用 Edge 以 1440×2000 渲染三页并完成截图复核；`python workflow/gtpj_workflow.py validate` 与 `git diff --check` 通过。`validate-remote` 按预期拒绝当前未同步状态，并准确报告 GitHub `main=08e5ecb`、本地 `main=88896d3`。
- 回退方式：回退本次 HTML、项目结构登记和本条版本记录；模型、实验、分支、Tag、PR 与远端 main 均不受影响。

## 2026-08-08：DOC-GTPJ-CODE-TUTORIAL-V1（已完成）

- 本次改的是哪个对象：GTPJ 初学者代码教程。
- 目标问题：模型、训练和工具代码缺少一个从 PyTorch 基础到完整数据流的连续阅读入口；教程若不注明源码范围，还会被误当成正式实验母版说明。
- 采用技术：六篇编号 Markdown 教程；总目录统一入口；首次出现的张量缩写同步解释维度含义；首页明确教程解释仓库根目录代码，正式 V5 新实验仍以 `model/v5-template-v1`、commit `2f5fa5e` 和 `experiments/v5/TEMPLATE.yaml` 为准。
- 替换了什么：这是第一版正式教程，不替换模型、训练入口或实验规范；它替换散落阅读代码、没有统一说明的做法。
- 实际可见效果：读者可按 01 至 05 顺序学习 PyTorch 基础、框架全貌、模型、训练和工具代码，并从教程首页进入当前框架注册页面。
- 选择原因：教程与代码放在同一仓库，能随源码一起检查链接、行号和版本边界。
- 已知限制：教程讲解仓库根目录代码，不是冻结母版的逐行副本；源码增删行后，教程中的辅助行号需要重新检查。
- 素材位置：`docs/tutorial/00_README.md` 至 `docs/tutorial/05_tools_explained.md`。
- 验证命令与结果：教程内部链接全部存在；训练教程登记的 1017 行与 `train_GTPJ_CUB.py` 实际行数一致；`python workflow/gtpj_workflow.py validate`、`validate-framework-ledgers`、`validate-workflow-consistency` 和 `audit-boundary` 全部通过；`python -m unittest tests.test_gtpj_workflow` 共 251 项全部通过。
- 回退方式：回退本次文档提交；不会改变模型、配置、实验账本或历史结果。

## 2026-08-08：UI-FRAMEWORK-SNAPSHOT-V1（已归档）

- 本次改的是哪个对象：2026-08-04 生成的两份旧框架说明页面（原 `GTPJ_UI-FRAMEWORK-V1_CURRENT.html` 和 `experiments/GTPJ_framework_overview.html`）。
- 目标问题：旧文件名含“CURRENT”，且一份页面放在 `experiments/`，会和当前正式入口 `UI-FRAMEWORK-REGISTRY-V3` 竞争。
- 采用技术：把两页移动到 `docs/diagrams/archive/`，统一归类为 `UI-FRAMEWORK-SNAPSHOT-V1`，页首标明历史快照并回链 V3 当前入口。
- 替换了什么：停止把两份 8 月 4 日页面当作当前入口；不替换 V3 页面。
- 实际可见效果：项目只剩一个当前框架注册入口，同时仍能回看旧版模型路径和成绩说明。
- 选择原因：保留历史比直接删除安全，明确归档比让多个页面都叫“当前”更容易理解。
- 已知限制：历史快照中的数值和状态只代表 2026-08-04，不会自动随参数矩阵更新。
- 素材位置：`docs/diagrams/archive/GTPJ_UI-FRAMEWORK-SNAPSHOT-V1_COMPACT_2026-08-04.html`、`docs/diagrams/archive/GTPJ_UI-FRAMEWORK-SNAPSHOT-V1_FULL_2026-08-04.html`。
- 验证命令与结果：两份 HTML 的 `html`、`body` 标签完整；两页都有“历史快照”提示，且到 `GTPJ_FRAMEWORK_REGISTRY_UI-V3.html` 的相对链接均可解析；项目结构账本已经登记归档目录。
- 回退方式：回退本次文档提交，可恢复原文件名和位置；机器台账和实验结果不受影响。

## 2026-08-07：MODEL-V5-TEMPLATE-V1（本地已冻结）

- 本次改的是哪个对象：V5 正式模型、训练入口、严格评估入口、输入身份与断点续训工具、历史 checkpoint 转换工具。
- 目标问题：原 V5 混有旧别名、废弃路线、实验开关和静默回退；继续叠加会让每项实验的真实改动难以判断。
- 采用技术：只接受 `[B（本批图片数量）, 577（1 个 CLS 全局标记 + 576 个真实局部块）, D（特征维度）]`；只保留 PSE、FGVD、BVSA、ICSA、SGMP 和 `global + 0.2 * local`；输入加载前后双指纹；续训绑定代码、配置、输入、类别顺序和随机数状态；旧权重通过独立转换工具显式迁移。
- 替换了什么：删除动态路由、可学习融合门、旧 AG-JEPA/LastViT/FAE 名称镜像、CLS-only/在线提取/增强缓存回退、多套文本路线、自动续训和无效占位参数；正式训练不再依赖旧 `CUBDataLoader` 与未使用的 `clip_att/CUB_attribute.pkl`。
- 实际可见效果：模型由历史约 1075 行减到约 700 行，训练入口由历史约 1007 行减到约 492 行；四份正式配置逐字一致；类别划分用 43 行最小 xlsa17 读取器核对缓存标签。
- 选择原因：每个 V5 实验以后都从不再变化的母版复制，只在自己的实验分支改一次，避免实验之间叠代码。
- 已知限制：本地只证明固定输入下输出、7 项损失、关键梯度、评估含义和中断续训一致；当前 CPU 环境没有执行真实多 GPU 恢复，服务器 U/S/H/ZS 也尚未复跑。
- 素材位置：代码母版分支 `framework/v5-template-v1`、Tag `model/v5-template-v1`、合同 `docs/workflow/contracts/V5_BEHAVIOR_CONTRACT.md`、审核记录 `docs/reviews/2026-08-07-v5-clean-template/`。
- 验证命令与结果：母版代码提交 `2f5fa5e631ef82658d4bac587cdfd17f3534cb35` 上，36 项 V5 专项测试、251 项工作流测试、5 个结构与边界检查全部通过；写入 frozen 登记后又重跑 251 项工作流测试和 5 个结构检查，全部通过；`py_compile`、`pyflakes`、`git diff --check` 通过；三名独立审核员均为 `ALLOW`。
- 回退方式：删除新的本地母版分支和 Tag，并回退本次登记提交；历史 `v5` Tag、原提交和旧实验证据没有移动或改写。

## 2026-08-06：UI-FRAMEWORK-REGISTRY-V3（已完成）

- 本次改的是哪个对象：人看的框架、母版和实验关系总览。
- 目标问题：V2 页面能看平级框架，但看不到每个框架的母版是否可用于新实验，也看不到实验与准确代码起点之间的关系。
- 采用技术：单文件静态 HTML，以技术登记卡形式同级展示 V1、V2、V3、V5；每张卡同时显示 V0 母版状态和四类实验数量，并单列 V5 消融阻塞原因。
- 替换了什么：V2 保留为历史页并链接 V3；当前人类入口切换为 V3。
- 实际可见效果：打开一页即可看出四个框架的历史来源、哪些母版只能回查、V5 为什么暂时不能启动局部分支消融，以及四层账本各自负责什么。
- 选择原因：母版状态是新规范的开工硬门，必须在总览第一页直接可见。
- 已知限制：页面是静态只读视图，事实仍以 YAML、INDEX 和 CSV 为准；服务器精度与消融运行状态需要继续随台账刷新。
- 素材位置：`docs/diagrams/GTPJ_FRAMEWORK_REGISTRY_UI-V3.html`。
- 验证命令与结果：14 个本地相对链接全部存在；使用 Edge 以 1440×1800 静态渲染并完成截图复核，框架卡、状态和四层表均完整可读。
- 回退方式：恢复 V2 为当前入口；不会改变任何机器账本和实验结果。

## 2026-08-06：SYS-WORKFLOW-V5（已完成）

- 本次改的是哪个对象：正式框架代码母版和四类实验的开工规则。
- 目标问题：长期框架分支、正式母版和实验开发线没有彻底分开，后续实验可能互相叠代码并污染框架模板。
- 采用技术：每个正式框架登记可版本化的只读母版；每项实验从准确 Tag 和 commit 独立开分支；实验代码不并回母版；创新确认后建立新的同级框架。正式参数行只允许在标准四类实验目录冻结和启动，旧动态路由正式 runner 退役但保留不进入证据的调试探针。
- 替换了什么：已经替换“新实验只要从可继续变化的 `framework/vX` 开分支”这一条不够严格的规则。
- 实际可见效果：同一框架下的实验拥有相同、可证明的代码起点，人可以直接判断每个实验只改了什么。
- 选择原因：避免 V5 及后续框架不断增加旧开关、兼容分支和实验专用代码。
- 已知限制：治理代码和 V5 干净母版已建立；旧 V0 仍不能启动新实验，V5 消融还需从 V1 母版重新绑定。
- 素材位置：`docs/workflow/FRAMEWORK_EXPERIMENT_STANDARD.md`、`workflow/gtpj_workflow.py`、`docs/diagrams/GTPJ_FRAMEWORK_REGISTRY_UI-V3.html`。
- 验证命令与结果：最终 `python -m pytest tests/test_gtpj_workflow.py -q` 为 251 项通过；`validate`、母版、实验账本、工作流一致性、边界、语法和差异检查全部通过；三轮独立审核均为 allow。审核记录位于 `docs/reviews/2026-08-06-framework-template-governance/`。
- 回退方式：回退 V5 规范和 helper 提交；现有正式 Tag、旧证据和运行结果不动。

## 2026-08-06：DATA-FRAMEWORK-TEMPLATE-V1（已完成）

- 本次改的是哪个对象：框架母版身份、实验基点身份和相关 schema。
- 目标问题：现有 `framework.yaml` 记录正式框架身份，但没有单独说明实验使用哪一版干净母版。
- 采用技术：每框架新增 `TEMPLATE.yaml`、每实验新增 `EXPERIMENT.yaml`，记录母版编号、Tag、代码 commit、`template_registry_commit`、状态和旧记录映射；registry 必须属于本地 `main` 历史。
- 替换了什么：已替换只凭框架分支名判断实验起点的做法。
- 实际可见效果：每个实验都能一眼看到准确代码起点，机器会阻止错基点启动。
- 选择原因：分支名可能继续变化，准确 commit 才能保证实验可复现。
- 已知限制：历史实验只能记录当时真实基点；不能倒填成未来创建的干净母版。
- 素材位置：`docs/superpowers/specs/2026-08-06-immutable-framework-template-design.md`。
- 验证命令与结果：四个 V0 的 Tag/commit/branch 校验通过；九个当前正式实验的历史基点或等待母版状态通过；错误 Tag、移动母版分支、任意祖先伪装、非标准目录启动和旧正式 runner 绕过均有回归测试；三轮独立审核通过。
- 回退方式：新增台账可按提交撤回，不移动旧目录、不修改历史证据。

## 2026-08-06：MODEL-V5-TEMPLATE-V1（原计划，已由 2026-08-07 冻结版本完成）

- 本次改的是哪个对象：V5 正式框架的第一份干净代码母版。
- 目标问题：V5 从早期框架演变而来，继续在原代码上增加实验开关会让模型和训练入口越来越难读。
- 采用技术：计划从 V5 实际有效路径重新提取 PSE、FGVD、conditional BVSA、ICSA、SGMP、局部/全局固定融合和正式训练评估流程；旧 checkpoint 兼容移到母版外的转换工具。
- 替换了什么：计划替换带有旧别名、废弃入口、无调用分支和后续实验代码的 V5 开工模板。
- 实际可见效果：本条是原计划记录；实际完成情况见上方 2026-08-07 条目。
- 选择原因：重新提取有效路径比继续增加开关更能控制代码长度和实验混杂。
- 已知限制：必须先证明固定输入下输出、损失、梯度和 GZSL 评估语义等价，再做服务器确认；未通过前不能冻结。
- 素材位置：设计在 `docs/superpowers/specs/2026-08-06-immutable-framework-template-design.md`，代码位置将在实施计划中逐项列出。
- 验证命令与结果：计划阶段当时尚未运行；后续本地验证已经完成，服务器确认仍未运行。
- 回退方式：原 `v5` Tag 和准确 commit 保持不动；新母版失败时直接放弃草稿分支，不影响历史 V5。

## 2026-08-06：SYS-WORKFLOW-V4（已完成）

- 本次改的是哪个对象：正式框架关系和晋级规则。
- 目标问题：V3 把历史来源关系写成父子框架和逻辑嵌套，导致正式框架视觉上无限套娃。
- 采用技术：所有正式框架使用 `registry_level: formal_peer`；用 `derived_from_framework` 单独记录历史来源；候选创新无正式 Tag。
- 替换了什么：替换“创新生成子框架”为“创新确认后注册新的同级正式框架”。
- 实际可见效果：V1、V2、V3、V5 同排；V2 指向 V1、V3 指向 V2、V5 指向 V3，箭头只表示来源。
- 选择原因：既保留历史演变证据，又避免把来源误解成包含关系。
- 已知限制：旧 Trial/Attempt 和旧审核材料里的历史字段不改写，只在现行规范和正式台账中停止使用。
- 素材位置：`docs/workflow/FRAMEWORK_EXPERIMENT_STANDARD.md`、`docs/workflow/protocols/versioning.md`。
- 验证命令与结果：全量 250 项测试通过；25 项 framework 专项测试通过；`validate`、`validate-framework-ledgers`、`validate-workflow-consistency`、`audit-boundary`、HTML 7 个内部链接和 `git diff --check` 全部通过；三路独立复核最终均为 `PASS`。
- 回退方式：回退 V4 规范提交；模型、训练结果、Tag 和 Warehouse 证据不变。

## 2026-08-06：DATA-FRAMEWORK-LEDGER-V2（已完成）

- 本次改的是哪个对象：正式框架 schema、framework.yaml、创新索引和校验器。
- 目标问题：`parent_version`、`source_experiment`、`lineage_status` 和 `Child framework` 会把来源关系固化成上下级。
- 采用技术：改为 `derived_from_framework`、`promoted_from_experiment`、`origin_status` 和 `Promoted framework`，并增加来源成环检查。
- 替换了什么：替换 `gtpj.framework.v1` 为 `gtpj.framework.v2`；参数矩阵和历史实验结果不变。
- 实际可见效果：正式框架仍能互相追溯，但机器数据明确声明它们是 `formal_peer`。
- 选择原因：字段本身就能阻止以后自动页面重新画成嵌套树。
- 已知限制：历史 v4 Tag 仍保留，但继续明确标为非正式框架。
- 素材位置：`schemas/framework.schema.json`、`experiments/v1|v2|v3|v5/framework.yaml`、四类 INDEX。
- 验证命令与结果：实际来源链 `V2→V1、V3→V2、V5→V3` 通过；缺 Tag、同名分支冒充 Tag、候选提前占号、错误 `promote_to`、第二根节点、未知来源和成环来源均被回归测试拦截；参数矩阵、成绩、运行记录和旧 Attempt/Trial 证据零改动。
- 回退方式：回退台账 schema 和 helper；旧证据路径不动。

## 2026-08-06：UI-FRAMEWORK-REGISTRY-V2（已完成）

- 本次改的是哪个对象：人看的正式框架关系图。
- 目标问题：旧 V1 页面使用逐层缩进，容易把正式框架理解成目录套娃。
- 采用技术：单文件 HTML 同级卡片，使用 `V1 ← V2 ← V3 ← V5` 的历史来源箭头。
- 替换了什么：V1 页面保留历史并加醒目停用提示；V2 成为当前入口。
- 实际可见效果：四个正式框架同排；V5 的四类实验单独展示，动态路由候选明确标为“无正式 Tag”。
- 选择原因：让人第一眼区分正式框架、历史来源和候选实验。
- 已知限制：静态页面依赖正式 YAML、INDEX 和参数表更新。
- 素材位置：`docs/diagrams/GTPJ_FRAMEWORK_REGISTRY_UI-V2.html`。
- 验证命令与结果：HTML 的 7 个内部链接全部存在；现行文档与本地 Skill 旧术语扫描通过；文档独立复核最终为 `PASS`。
- 回退方式：回退 V2 页面并恢复旧入口；不影响机器台账。

## 2026-08-06：SYS-WORKFLOW-V3（已被 V4 纠正）

- 本次改的是哪个对象：实验管理工作流。
- 目标问题：旧 `TRIAL / ATTEMPT` 混合承载框架、实验项和运行，难以一眼看懂，容易重复调参。
- 采用技术：正式框架树、四类同级实验索引、每实验一张参数矩阵、旧编号只读映射。
- 替换了什么：替换 Trial-first 的人类查看方式；旧文件只作为历史证据保留。
- 实际可见效果：当时已经能从一个 HTML 和每个框架的 `EXPERIMENTS.md` 看全貌；当时采用从 `framework/vX` 开分支的规则，现已由 `SYS-WORKFLOW-V5` 的准确母版起点替换。
- 选择原因：避免物理目录无限嵌套，同时保留清楚的父子关系。
- 已知限制：旧实验缺少逐任务参数时只能标 `legacy_summary_only`，不能补猜测值。
- 素材位置：`docs/workflow/FRAMEWORK_EXPERIMENT_STANDARD.md`、`experiments/`、`docs/diagrams/`。
- 验证命令与结果：`python -m unittest discover -s tests -p "test_*.py"` 共 239 项全部通过；`validate`、`validate-framework-ledgers`、`validate-workflow-consistency`、`audit-boundary` 和最终差异空白检查全部通过；三路独立复核最终均为 `PASS`。
- 回退方式：回退本次治理提交；历史 tags、旧实验和 Warehouse 证据不受影响。

## 2026-08-06：DATA-FRAMEWORK-LEDGER-V1（已被 V2 纠正）

- 本次改的是哪个对象：框架和实验台账数据。
- 目标问题：框架身份、来源创新、四类实验、参数行和旧编号缺少统一映射。
- 采用技术：`framework.yaml`、统一 INDEX 表头、生成式 `EXPERIMENTS.md`、`PARAMETER_MATRIX.csv/.md`。
- 替换了什么：不再把 `ATTEMPT-xxx` 当成人看的主编号。
- 实际可见效果：V1、V2、V3、V5 均有正式机器身份、四类索引和自动总览；v4 明确保留为非框架历史标签；现有 9 个正式实验项均有参数表。
- 选择原因：一份机器事实源，一份自动生成人类视图，避免两张表手工漂移。
- 已知限制：历史缺失字段保持缺失。
- 素材位置：`schemas/framework.schema.json`、`experiments/templates/`。
- 验证命令与结果：参数矩阵阅读版已刷新；V5 局部分支消融与旧冻结计划的 15 行哈希、参数、种子、复跑关系和配置快照映射差异均为 0，仍全部 `planned`、未启动训练；框架总校验通过。
- 回退方式：回退台账文件；旧证据路径保持原样。

## 2026-08-06：UI-FRAMEWORK-TREE-V1（已停止使用）

- 本次改的是哪个对象：人看的框架树页面。
- 目标问题：只看文件夹难以立即理解父子框架、四类实验、局部分支权重和待跑消融。
- 采用技术：单文件本地 HTML，直接链接各框架参数矩阵。
- 替换了什么：不替换模型图；新增一个治理全貌入口。
- 实际可见效果：页面显示 V1 → V2 → V3 → V5、v4 历史特例、`local_weight=0.2`、动态路由状态和 ATTEMPT-019 未运行状态。
- 选择原因：不用安装服务，双击即可看，并能直接进入具体参数表。
- 已知限制：页面是轻量静态视图；机器事实仍以 YAML、INDEX 和 CSV 为准。
- 素材位置：`docs/diagrams/GTPJ_FRAMEWORK_TREE_UI-V1.html`。
- 验证命令与结果：文件存在，关键框架、实验号、权重和状态标记均可检索；最终框架账本校验通过，三路独立复核均通过。
- 回退方式：删除本 UI 文件不会影响机器台账和历史证据。
