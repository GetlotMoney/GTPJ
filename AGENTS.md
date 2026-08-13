# GTPJ Agent 规则

## 1. 当前效力与入口

- 本文件只保留当前生效的项目级命令；2026-08-13 以前的旧规则只用于解释历史实验，不得用于启动新任务。
- 旧版三份核心规则全文统一归档在 `docs/workflow/archive/specs/WORKFLOW_PRE_V6_ARCHIVE.md`。
- 当前任务先读本文件；需要实验规则时，再读 `docs/workflow/START_HERE.md`、`docs/workflow/WORKFLOW_KERNEL.md` 和一个必要的 playbook 或 protocol。
- 下层文件与本文件冲突时以本文件为准；历史目录 `docs/workflow/archive/` 永远没有当前命令权。

## 2. 沟通与执行

- 默认中文，先讲结论；解释陌生概念时先说为什么存在、解决什么，再说怎么做。
- 不确定时写明假设和风险；不知道就直说，不能把未验证结果说成完成。
- 动手前只读当前任务需要的文件，理解已有修改，只做最小范围，不做无关重构。
- 普通问答、Git 状态、分支比较、概念解释和不改变门槛或语义的纯文字修正，直接完成，不生成实验计划、启动卡或状态机。
- 简单任务直接做；中等任务最多 3 步。用户说“开始、继续、批准、就这样”后立即执行已确认事项。
- 手动流程 Skill 只能由 owner 直接点名或从菜单选择；完成具体文件、图片、浏览器等操作的工具 Skill 可在任务确实需要时使用。

## 3. 当前实验短流程

只有创建实验、改变训练/评估含义、冻结运行、启动训练、记录正式结果或晋级版本时，才进入实验流程：

1. 写清实验问题、基线、唯一代码提交、配置和 `PARAMETER_MATRIX`。
2. 一次开跑检查：工作区干净、数据/划分身份一致、GPU 可见、输出目录不存在。
3. 使用现有训练入口直接运行；多 GPU 只做简单任务分配，不为单次实验新增控制器。
4. 每个 `RUN-xxx` 使用独立目录，至少保留 `training.log`、最终指标和需要保留的最佳模型，禁止覆盖历史目录。
5. 训练后把全部结果回填同一张参数表，并写一份结论。

必须保留：准确 commit、配置快照、数据/划分身份、seed、评估口径、完整 U/S/H/ZS 和不覆盖历史结果。除非当前真实风险需要或 owner 明确要求，不增加额外控制层、凭证层或调度机制。

正式训练必须从 clean worktree 和冻结的唯一 `commit:<sha>` 启动。运行前配置与计划先进入 pre-run commit；运行后的结果账本另行记录，不能混写预跑结论。debug/smoke 产生的结果不能作为 keep、best、promotion 或 confirmation evidence。

训练、特征抽取和验证默认使用本机 conda 环境 `dvsr_gpu`，使用 `conda run -n dvsr_gpu ...` 或先激活该环境；运行记录必须能确认实际 Python 环境。

## 4. 修改与审核

- 修改代码、workflow、helper、模板或训练配置生成逻辑前，先从干净基线切到 `codex/` 专用分支。
- 普通说明文档、账本值，以及已审核代码支持的普通超参数/seed 修改，只要不改变 schema、解析/生成逻辑、数据/划分、评估语义或工作流门槛，只做直接相关的机器检查。
- 其他代码或规则修改在机器测试通过后，必须由两个不同子 Agent **依次**完成两轮对抗式只读审核；Implementer 是唯一 writer。
- 第 1 轮检查实现、接口、shape、梯度、数据和评估错误；修复、重测并经第 1 轮复核通过后，才能开始第 2 轮。
- 第 2 轮检查同一份最终代码，寻找反例、隐藏耦合、回归和测试盲区。若它引发代码修改，两轮对该最终版本重新按顺序确认。
- 两轮必须绑定同一 `reviewed_code_id` 和 `reviewed_extra_files`，记录 `files_reviewed`、`machine_test_ref`、发现、`unresolved_blockers`、`decision`、`uncovered_scope`；第 2 轮另记 `previous_round_ref`。
- 两轮都为 `pass`、阻断为 0 且机器测试通过，代码才算完成并可进入正式训练。普通任务不增加独立审核、审核包、命名审核线程或第三轮审核。

## 5. 框架、账本与资产

- `main` 是治理分支；正式新实验读取所属 `experiments/vX/TEMPLATE.yaml`，从锁定的 `framework/vX-template-vN` / `model/vX-template-vN` 准确提交独立分叉。
- 正式框架平级；每个框架只有 tune、ablation、innovation、confirmation 四类实验。创新通过确认和接纳后才注册新框架与 Tag。
- 每个真实训练对应参数矩阵中的一行 `RUN-xxx`；旧记录无法可靠恢复时写 `legacy_summary_only`，不得猜值。
- 正式复现固定 `repeat_type: exact_repeat`、`original_seed`、原始配置、代码、数据、训练日程和评估口径，并写明 `max_attempts: 5`、`max_attempts_hard_cap: true`、`early_stop_on_best_hit: true`、`restore_target_H`、`near_miss_tolerance_H`、`near_miss_not_restored`。`seed_sweep`、`score_search`、`multi_seed_stability` 必须写 `not_confirmation_evidence: true`；best hit、stable confirm 和 promotion 的详细判定以 `docs/workflow/protocols/promotion.md` 与 `docs/workflow/protocols/experiment_protocol.md` 为准。
- GitHub 只保存轻量账本、配置与证据索引；数据集、checkpoint、原始 cache、密钥和大型日志不入 Git。失败实验也必须如实记录。
- 新增、删除、移动、重命名文件或改变职责时，同步更新 `docs/PROJECT_STRUCTURE.md`。
- 涉及新旧仓库对照时先读 `REPOSITORY_INDEX.json`；未经 owner 明确授权，不跨仓库写入、同步或迁移。

## 6. 安全与交付

- 不自动删除或覆盖重要数据，不自动 push、发布、部署、破坏性迁移，也不自动处理密钥；这些动作必须有 owner 当前明确授权。
- Runner 串行使用 GPU，不使用训练/测试反馈在运行中途改变训练行为。
- 完成时简要说明改了什么、验证了什么、没验证什么和真实剩余风险。

## 7. 权威文件

- 项目状态：`docs/PROJECT_STATUS.md`
- 结构总账本：`docs/PROJECT_STRUCTURE.md`
- 工作流入口：`docs/workflow/START_HERE.md`
- 工作流硬规则：`docs/workflow/WORKFLOW_KERNEL.md`
- 框架与实验结构：`docs/workflow/FRAMEWORK_EXPERIMENT_STANDARD.md`
- 版本账本：`experiments/VERSION_TREE.md`
- 参数矩阵总看板：`experiments/PARAMETER_MATRIX_CATALOG.md`
