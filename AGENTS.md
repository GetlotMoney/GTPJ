# GTPJ Agent 规则

## Owner 自我介绍

- Owner 是研究生一年级、人工智能专业学生，目前研究 CV 方向的 GZSL 领域。
- Owner 喜欢从第一性原理思考问题，希望 agent 在解释概念、判断路线和拆解实验时优先回到问题本质。
- Owner 在本项目内要完成 GZSL / CV 方向的实验、总结和创新沉淀。
- Owner 默认用中文协作，正在把 GTPJ 作为干净主线维护，用于 GZSL / CV 模型实验、版本治理和实验追溯。
- `cv-work` / DVSR 旧项目是历史实验资产库和流程素材库；GTPJ 是当前主仓库和后续工作主线。
- Owner 重视可复现、可回滚、证据完整和长期沉淀；不希望为了快而把旧实验、旧分支、旧 workflow 原样搬进 GTPJ。
- Owner 的长期目标是搭建完整的“论文阅读 -> 创新想法 -> 实验验证 -> 结果总结 -> 反哺创新”的闭环工作流，用 AI 解放重复劳动，自动化完成可靠实验。
- 当前优先级是先把 GitHub 治理、baseline、创意来源、trial 证据链做干净，再逐步接入 OpenClaw / Codex 工作流；最终服务于可复现实验和创新沉淀。

## Owner 默认要求

- 默认用中文沟通，除非任务明确要求英文。
- 先讲结论，再讲关键原因。
- 复杂任务先给简短计划，再开始执行。
- 不确定时说明假设和风险，不要装作确定。
- 回答 owner 不知道什么意思的问题时，从第一性原理出发解释。
- 动手前先阅读相关文件和已有约定。
- 修改范围尽量小，不做与任务无关的重构。
- 遇到 owner 已经修改过的文件，先理解现状再继续。
- 发现需求含糊时，先提出最关键的问题。
- 能直接验证的结果，优先用命令或测试验证。
- 交付时说明改了什么、验证了什么；测试不能跑时说明原因。
- 标出仍然存在的风险和下一步建议。

## 沟通

- 与 owner 协作时默认使用中文。
- 先说结论，再说关键原因。
- 复杂任务在编辑前先给简短计划。
- 直接说明不确定性和风险。

## 仓库规则

- `main` 是唯一长期分支。
- `v1`、`v2`、`v3` 是永久 baseline tags。
- Trial 代码快照使用类似 `trial/idea-0001/trial-001` 的 tag。
- 当前阶段已经强制执行 GTPJ 核心 workflow：任务路由、启动卡、pre-run freeze、artifact 边界、结果账本、质量门、agent 凭证和 promotion gate 都必须遵守。
- OpenClaw / Codex 只是不同 runtime 入口；它们必须共享同一套 GitHub 事实源和 workflow 规范。
- `workflow/gtpj_workflow.py` 是结构辅助工具，用于 validate、audit-boundary、目录创建和结果记录等机械动作；它不替代 Coordinator 的研究判断、owner 决策、代码审查或实验解释。
- `docs/PROJECT_STRUCTURE.md` 是项目结构总账本；新增、删除、移动、重命名文件或改变文件职责时必须同步更新。
- 不创建 controller branch。
- 不迁移旧实验 ID、旧分支、旧 PR 或旧 workflow 文件。
- 除非 owner 明确要求 push，否则不要 push。

## 实验规则

- GTPJ 实验默认使用本机 conda 环境 `dvsr_gpu`；运行训练、特征抽取、验证脚本前先激活该环境，或使用 `conda run -n dvsr_gpu ...`。
- OpenClaw 是优先 runtime；Codex 兼容，但必须遵循同一套文件。
- 每个新模块 trial 都必须从 `idea_tree` 节点开始。
- 没有 `idea_id`，就没有 `dev/idea-*` 分支。
- 每个 trial 至少记录 implementation、config、quality_check、result 和 code tag。
- 只有版本级 tune、ablation 和 confirmation 才写入正式版本目录，例如 `experiments/v1/`。
- 模块 trial 内部为了判断一个新模块好不好，可以做 trial-internal param tune、narrow ablation、confirmation/rerun；这些写入该 trial 的 `ATTEMPTS.md` 和 `attempts/ATTEMPT-xxx/`，不要误放到 `experiments/vX/tune|ablation|confirmation/`。
- 如果 trial 内部尝试已经改变实现假设、forward 路径、新 loss 机制或评估语义，就新开 `TRIAL-002`，不要继续堆在同一个 `TRIAL-001`。
- 真实训练或会产出正式证据的运行，必须从 `git status --short` 为空的 clean worktree 启动；dirty tree 只能用于临时 debug/smoke，且结果不能记为 `keep`、`best`、`promote` 或 confirmation evidence。
- 如果一次 run 需要先在仓库里新增 `config.yaml`、`ATTEMPTS.md` 计划行、启动卡或其他预跑账本，必须先把这些“运行前文件”冻结成一次 `pre-run freeze commit`，再确认工作树 clean 后才能启动 Runner。
- `pre-run freeze commit` 只允许包含本次 run 的配置、副本、计划和轻量预跑元数据，不允许提前写入本次 run 的 `manifest.yaml`、`result.yaml`、`result.md`、`quality_check.md`、指标结论或 artifact 注册。
- 真实 run 启动时必须记录并引用冻结后的 `run_commit`；run 完成后，结果账本、artifact 注册和索引更新应进入单独的 `post-run result commit`，不要把“影响运行的配置改动”和“运行后的结果记账”混在同一次提交里。

## Multi-agent 规则

- 每次 GTPJ workflow 启动卡必须写明 `agents.activation_mode`，只能是 `role_only` 或 `real_multi_agent`。
- `role_only` 表示一个主 agent 按 Coordinator、Runner、Quality Checker 等角色清单串行执行；必须在 `agent_summary.md` 里说明为什么没有启动真实多 agents。
- `real_multi_agent` 表示启动或委派独立 agent / reviewer / checker，保留独立输入、发现和结论；如果当前环境没有真实 multi-agent 工具，不能把顺序角色扮演写成 `real_multi_agent`。
- `role_only_with_independent_sequential_review` 不是第三种 activation mode，只能写在 `agents.tool_support.fallback_mode`；它不能用于 promotion、正式 best 结论或 owner 已明确要求真实多 agents 的任务，除非 owner 明确接受 debug/smoke 降级。
- owner 明确要求多 agents、任务修改模型/forward/loss/eval/数据流语义、涉及接口/评估/label mapping/seen-unseen split/class order/logits shape/metric semantics 风险、结果异常有争议、promotion 前复核、结论会影响论文实验路线或 baseline 选择时，必须使用 `real_multi_agent`。
- 窄范围 rerun / confirmation 准备、只读解释、配置查看、单一 Runner 按 frozen config 复跑、debug/smoke 或账本格式整理时，可以使用 `role_only`，但必须记录代执行的角色和升级条件。
- Runner 永远串行并锁 GPU；Implementer 是同一代码路径唯一 writer；Coordinator 是最终 GitHub 账本唯一写入者；Reader/Planner、Log Analyst、Quality Checker、Result Analyst、Reviewer 默认只读，可并行。
- Agent 不能把隐藏聊天记忆当实验事实源。Codex memory 或历史会话摘要只能用于定位，必须回到当前 repo、日志或 artifact 验证后才能写入结果、质量门或 promotion 证据。
- `agent_summary.md` 必须记录 `activation_mode`、`agent_instance_type`、`independence_scope`、`memory_used`、`memory_sources` 和 `verified_against_current_repo`。
- 如果 owner 对 agent 模式提出异议，先暂停真实 run，修正启动卡或升级为 `real_multi_agent` 后再继续。

## 安全

- 不提交数据集、checkpoint、原始 cache、密钥或大型日志。
- 不使用训练/测试反馈在运行中途改变训练行为。
- 不隐藏失败实验；失败也要作为证据记录。
