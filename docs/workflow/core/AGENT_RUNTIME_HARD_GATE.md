# Agent Runtime 历史兼容说明

`SYS-WORKFLOW-V6` 不把命名线程、`agent_runtime.yaml`、状态迁移链或多 Agent preflight 作为默认开跑门；本文件不是 V6 默认开跑门。

只有 owner 明确要求多智能体实时监控，或当前任务出现必须隔离上下文的真实并行风险时，才按需启用旧机制。完整旧规则保存在 `../archive/specs/WORKFLOW_PRE_V6_ARCHIVE.md`，没有当前命令权。

普通正式实验使用：唯一冻结 commit、配置/参数矩阵、一次 clean/data/GPU/输出目录检查、独立 RUN 目录和结果回填。
