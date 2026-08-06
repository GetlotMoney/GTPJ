# GTPJ 技术与工作流演进记录

## 版本类型说明

- `SYS-*`：系统功能和工作流规则。
- `UI-*`：人看的页面与图。
- `DATA-*`：台账、表格和结构化数据格式。
- `MODEL-*`：模型代码框架。

## 当前版本一览

| 对象 | 当前版本 | 状态 | 实际内容 |
|---|---|---|---|
| 工作流 | `SYS-WORKFLOW-V4` | 已完成 | 正式框架全部平级，候选无 Tag，确认后注册新同级框架。 |
| 框架台账 | `DATA-FRAMEWORK-LEDGER-V2` | 已完成 | `framework.yaml` 使用历史来源指针，不再使用父子字段。 |
| 框架注册页面 | `UI-FRAMEWORK-REGISTRY-V2` | 已完成 | 本地 HTML 同级展示 V1、V2、V3、V5，并用反向箭头表示来源。 |
| 模型 | `MODEL-GTPJ-V5` | 未改动 | 本次不改模型、训练和评估语义。 |

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
- 实际可见效果：从一个 HTML 和每个框架的 `EXPERIMENTS.md` 就能看到全貌；新实验必须从 `framework/vX` 开分支。
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
