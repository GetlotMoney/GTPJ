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
| V5 正式实验执行器 | `SYS-RUNNER-V1` | 审核中 | 双卡队列使用绑定 Python、pidfd 进程句柄、本次执行私有只读数据快照、原子 claim 和状态写入失败关闸；正式训练待启动。 |
| 框架台账 | `DATA-FRAMEWORK-LEDGER-V2` | 已完成 | `framework.yaml` 使用历史来源指针，不再使用父子字段。 |
| 框架注册页面 | `UI-FRAMEWORK-REGISTRY-V3` | 已完成 | 本地 HTML 同级展示来源、各母版状态、四类实验数量和 V5 消融“已绑定、待实现”状态。 |
| 模型 | `MODEL-GTPJ-V5` | 未改动 | 本次不改模型、训练和评估语义。 |
| 母版台账 | `DATA-FRAMEWORK-TEMPLATE-V1` | 已完成 | 已新增母版与实验起点身份，分开记录母版代码 commit 和后续 registry commit。 |
| V5 干净母版 | `MODEL-V5-TEMPLATE-V1` | 本地已冻结 | 分支、Tag、commit 均锁定到 `2f5fa5e`；本地等价和三轮审核通过，服务器 U/S/H/ZS 待确认。 |

## 2026-08-07：SYS-RUNNER-V1（已完成）

- 本次改的是哪个对象：`V5-ABLATION-001` 的服务器双卡正式执行器、训练进程绑定和失败凭证路径；没有修改冻结 V5 母版模型。
- 目标问题：普通的“先检查路径、再按路径启动”和“先读 PID、再按 PID 停止”存在极短竞态；数据只复核 inode、大小和时间也不能证明内容仍等于冻结清单。
- 采用技术：正式 Python 先打开文件描述符，后续 helper、训练包装器和最终训练入口都从 `/proc/<控制器PID>/fd/<文件描述符>` 执行；Linux 停止使用 pidfd 绑定具体进程对象，Python 没封装接口时直接调用内核系统调用；控制器把清单中的 12 个数据文件复制到本次 execution 的私有目录，复制时复算 SHA-256，随后将文件和目录改为只读，每个 RUN 只读取并复核这份快照；execution claim 先完整写临时文件再用硬链接原子发布；所有状态写入与失败关闸共用同一把锁；目录、环境和日志准备完成后再做最后一次 STOP 检查，该检查通过后紧接着创建 helper。
- 替换了什么：替换按可变路径执行 Python、按裸 PID/PGID 发送正常停止信号、校验源数据后继续从源目录训练、直接向最终 claim 文件写 JSON，以及状态写失败后才阻断另一队列的做法。
- 实际可见效果：服务器控制器可以证明实际执行的是已打开的 Python 文件对象；PID 被复用时信号也不会发给新进程；源数据在预检后变化不会影响本次训练，因为训练只读取已经校验且只读的私有副本；最终成功状态写失败时，另一张卡也不能抢到下一项；claim 已发布后临时文件清理异常不会丢失领取凭证。
- 选择原因：这项消融会产生论文证据，宁可每次正式执行多占一份输入数据空间和一次复制时间，也不能让运行身份、数据或进程清理存在说不清的边界。
- 已知限制：私有数据快照会额外占用约一份正式输入数据的磁盘空间；pidfd 的内核调用号按当前 `lab4090` 的 Linux x86_64 环境实现；断电瞬间的目录级持久性没有单独做掉电注入；三组同 seed 不等于共享参数逐元素相同初始化。
- 素材位置：`tools/run_v5_ablation_001_server_controller.py`、`tools/run_v5_ablation_001_training.py`、`workflow/gtpj_workflow.py`、`tests/test_v5_ablation_server_runner.py`、`tests/test_v5_ablation_server_linux_integration.py`。
- 验证命令与结果：本地服务器控制器测试 40 项通过；全仓共 334 项，其中 332 项通过、2 项 Linux 专属测试在 Windows 跳过；`lab4090` 上 40 项控制器测试和 2 项真实 Linux 进程测试共 42 项通过；pidfd 能力探测为 `true`，绑定 Python 子进程实际报告固定解释器路径和清单中的 SHA-256。`py_compile` 通过；本地未安装 `pyflakes`，该项未运行。
- 回退方式：回退本实验分支上的执行器提交；冻结母版 `model/v5-template-v1@2f5fa5e`、数据文件、旧运行证据和其他框架不动。

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
