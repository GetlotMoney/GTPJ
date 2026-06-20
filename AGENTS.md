# GTPJ Agent 规则

## 沟通

- 与 owner 协作时默认使用中文。
- 先说结论，再说关键原因。
- 复杂任务在编辑前先给简短计划。
- 直接说明不确定性和风险。

## 仓库规则

- `main` 是唯一长期分支。
- `v1`、`v2`、`v3` 是永久 baseline tags。
- Trial 代码快照使用类似 `trial/idea-0001/trial-001` 的 tag。
- 使用 `workflow/gtpj_workflow.py` 做状态检查和创建新的 workflow 记录。
- `docs/PROJECT_STRUCTURE.md` 是项目结构总账本；新增、删除、移动、重命名文件或改变文件职责时必须同步更新。
- 不创建 controller branch。
- 不迁移旧实验 ID、旧分支、旧 PR 或旧 workflow 文件。
- 除非 owner 明确要求 push，否则不要 push。

## 实验规则

- OpenClaw 是优先 runtime；Codex 兼容，但必须遵循同一套文件。
- 每个新模块 trial 都必须从 `idea_tree` 节点开始。
- 没有 `idea_id`，就没有 `dev/idea-*` 分支。
- 每个 trial 必须记录 implementation、config、review、result 和 code tag。
- Tune、ablation 和 confirmation 运行属于具体版本目录，例如 `experiments/v1/`。

## 安全

- 不提交数据集、checkpoint、原始 cache、密钥或大型日志。
- 不使用训练/测试反馈在运行中途改变训练行为。
- 不隐藏失败实验；失败也要作为证据记录。
