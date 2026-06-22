# GTPJ Agent 规则

## Owner 自我介绍

- Owner 是研究生一年级、人工智能专业学生，目前研究 CV 方向的 GZSL 领域。
- Owner 喜欢从第一性原理思考问题，希望 agent 在解释概念、判断路线和拆解实验时优先回到问题本质。
- Owner 在本项目内要完成研究生论文相关的实验、总结和论文撰写。
- Owner 默认用中文协作，正在把 GTPJ 作为干净主线维护，用于 GZSL / CV 模型实验、版本治理和实验追溯。
- `cv-work` / DVSR 旧项目是历史实验资产库和流程素材库；GTPJ 是当前主仓库和后续工作主线。
- Owner 重视可复现、可回滚、证据完整和长期沉淀；不希望为了快而把旧实验、旧分支、旧 workflow 原样搬进 GTPJ。
- Owner 的长期目标是搭建完整的“论文阅读 -> 创新想法 -> 实验验证 -> 结果总结 -> 反哺创新”的闭环工作流，用 AI 解放重复劳动，自动化完成可靠实验，并为最终论文写作积累证据和文本素材。
- 当前优先级是先把 GitHub 治理、baseline、创意来源、trial 证据链做干净，再逐步接入 OpenClaw / Codex 工作流；最终服务于研究生论文的实验和写作。

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
- 当前阶段只强制 GitHub 项目治理规范；workflow 只作为未来 OpenClaw/Codex 接入参考。
- `workflow/gtpj_workflow.py` 目前只作为可选的结构检查和目录创建辅助，不代表必须执行完整实验工作流。
- `docs/PROJECT_STRUCTURE.md` 是项目结构总账本；新增、删除、移动、重命名文件或改变文件职责时必须同步更新。
- 不创建 controller branch。
- 不迁移旧实验 ID、旧分支、旧 PR 或旧 workflow 文件。
- 除非 owner 明确要求 push，否则不要 push。

## 实验规则

- OpenClaw 是优先 runtime；Codex 兼容，但必须遵循同一套文件。
- 每个新模块 trial 都必须从 `idea_tree` 节点开始。
- 没有 `idea_id`，就没有 `dev/idea-*` 分支。
- 每个 trial 至少记录 implementation、config、quality_check、result 和 code tag。
- Tune、ablation 和 confirmation 运行属于具体版本目录，例如 `experiments/v1/`。

## 安全

- 不提交数据集、checkpoint、原始 cache、密钥或大型日志。
- 不使用训练/测试反馈在运行中途改变训练行为。
- 不隐藏失败实验；失败也要作为证据记录。
