# GTPJ 技术与工作流演进记录

## 版本类型说明

- `SYS-*`：系统功能和工作流规则。
- `UI-*`：人看的页面与图。
- `DATA-*`：台账、表格和结构化数据格式。
- `MODEL-*`：模型代码框架。

## 当前版本一览

| 对象 | 当前版本 | 状态 | 实际内容 |
|---|---|---|---|
| 工作流 | `SYS-WORKFLOW-V5` | 已完成 | 同级框架各有只读母版，四类实验从准确母版 commit 独立分叉；旧 Trial 正式 runner 已退役。 |
| 框架台账 | `DATA-FRAMEWORK-LEDGER-V2` | 已完成 | `framework.yaml` 使用历史来源指针，不再使用父子字段。 |
| 框架注册页面 | `UI-FRAMEWORK-REGISTRY-V3` | 已完成 | 本地 HTML 同级展示来源、V0 母版状态、四类实验数量和 V5 消融阻塞。 |
| 模型 | `MODEL-GTPJ-V5` | 未改动 | 本次不改模型、训练和评估语义。 |
| 母版台账 | `DATA-FRAMEWORK-TEMPLATE-V1` | 已完成 | 已新增母版与实验起点身份，分开记录母版代码 commit 和后续 registry commit。 |
| V5 干净母版 | `MODEL-V5-TEMPLATE-V1` | 本地候选 | 已只保留 577-token、PSE、FGVD、BVSA、ICSA、SGMP 和固定 0.2 融合路线；33 项直接测试和 251 项工作流测试通过，等待阻断修复复审，尚未冻结。 |

## 2026-08-07：MODEL-V5-TEMPLATE-V1（本地候选）

- 本次改的是哪个对象：V5 正式模型、训练入口、严格评估入口和历史 checkpoint 转换工具。
- 目标问题：上一版候选仍会接受缺少 CLS 的输入，训练会按本机缓存状态切换路线，局部分支权重也能被改成非 0.2；这会让同一份配置在不同机器上得到不同含义。
- 采用技术：模型只接受 `[B（本批图片数量）, 577（1 个 CLS + 576 个真实局部块）, D（特征维度）]`；PSE、FGVD、conditional BVSA、ICSA、SGMP 全部走唯一正式路线；最终分数硬锁为 `global + 0.2 * local`；训练和评估缺少真实缓存时直接停止；历史权重转换必须用干净母版 `state_dict` 逐字段核对名字、形状和类型。
- 替换了什么：删除 PSE 旧适配器、无几何 FGVD、三种 SGMP 上下文、adapted/conditional 文本切换、多视角/CLS-only/在线训练、混合文本、AMP、评估偏置、自动续训、重启和微调等岔路。
- 实际可见效果：模型由历史约 1075 行减到约 700 行，训练入口由历史约 1007 行减到约 482 行；四份正式配置内容一致并删除 18 个不生效或只负责切路线的字段。
- 选择原因：每个实验应从不变母版复制后只改一次，母版本身不应积累后续实验开关；缺输入时明确失败比静默退化更能保证局部分支消融可信。
- 已知限制：当前只证明固定 CPU 小输入上的输出、损失和关键梯度等价，并用受控 logits 证明 U/S/H/ZS 计算含义；尚未获得服务器正式精度，也尚未冻结 Tag 和母版台账。
- 素材位置：`model/MyModel.py`、`train_GTPJ_CUB.py`、`tools/v5_evaluation.py`、`tools/convert_v5_checkpoint.py`、`docs/workflow/contracts/V5_BEHAVIOR_CONTRACT.md`。
- 验证命令与结果：稳定 Python 3.10 运行 V5 合同、转换器、数学路径和续训复现测试，33 项全部通过；工作流 251 项通过；5 个结构/边界检查、`py_compile`、`pyflakes` 与 `git diff --check` 通过；历史 `v5` Tag 的真实模型经字段转换后，评估/训练 logits、7 项损失和 PSE/BVSA/ICSA/SGMP 关键梯度在 `rtol=1e-5、atol=1e-6` 下对齐；CPU 小模型连续训练与中断续训 3 个 step 的 loss 和参数逐位一致。
- 回退方式：回退本候选提交即可；历史 `v5` Tag、原 commit、旧实验目录和结果证据均未改动。

## 2026-08-06：UI-FRAMEWORK-REGISTRY-V3（已完成）

- 本次改的是哪个对象：人看的框架、母版和实验关系总览。
- 目标问题：V2 页面能看平级框架，但看不到每个框架的母版是否可用于新实验，也看不到实验与准确代码起点之间的关系。
- 采用技术：单文件静态 HTML，以技术登记卡形式同级展示 V1、V2、V3、V5；每张卡同时显示 V0 母版状态和四类实验数量，并单列 V5 消融阻塞原因。
- 替换了什么：V2 保留为历史页并链接 V3；当前人类入口切换为 V3。
- 实际可见效果：打开一页即可看出四个框架的历史来源、哪些母版只能回查、V5 为什么暂时不能启动局部分支消融，以及四层账本各自负责什么。
- 选择原因：母版状态是新规范的开工硬门，必须在总览第一页直接可见。
- 已知限制：页面是静态只读视图，事实仍以 YAML、INDEX 和 CSV 为准；V5 干净母版完成后需同步刷新状态。
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
- 已知限制：治理代码已实现，但 V5 干净模型母版仍未建立；旧 V0 不能启动新实验。
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

## 2026-08-06：MODEL-V5-TEMPLATE-V1（计划中）

- 本次改的是哪个对象：V5 正式框架的第一份干净代码母版。
- 目标问题：V5 从早期框架演变而来，继续在原代码上增加实验开关会让模型和训练入口越来越难读。
- 采用技术：计划从 V5 实际有效路径重新提取 PSE、FGVD、conditional BVSA、ICSA、SGMP、局部/全局固定融合和正式训练评估流程；旧 checkpoint 兼容移到母版外的转换工具。
- 替换了什么：计划替换带有旧别名、废弃入口、无调用分支和后续实验代码的 V5 开工模板。
- 实际可见效果：尚未完成；完成后每个 V5 实验从同一份干净代码独立修改。
- 选择原因：重新提取有效路径比继续增加开关更能控制代码长度和实验混杂。
- 已知限制：必须先证明固定输入下输出、损失、梯度和 GZSL 评估语义等价，再做服务器确认；未通过前不能冻结。
- 素材位置：设计在 `docs/superpowers/specs/2026-08-06-immutable-framework-template-design.md`，代码位置将在实施计划中逐项列出。
- 验证命令与结果：计划阶段，尚未运行新旧 V5 等价测试和服务器确认。
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
