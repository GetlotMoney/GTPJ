# 证据说明

本目录只保存轻量证据索引，不保存原始日志或模型。

- `DIAGNOSTIC_MATRIX.csv`：老 V5 与动态路由历史代码诊断运行清单。
- 正式今天模板运行见上一级 `PARAMETER_MATRIX.csv`。
- R1 启动失败永久保存在 `FAILED_BATCH_R1.md`、`FORMAL_BATCH_R1.csv` 和 `DIAGNOSTIC_BATCH_R1.csv`；当前两张主表只列 R2 的全新待运行编号。
- 服务器完成后补充 execution 状态、逐任务清单哈希和 Warehouse 逻辑路径。

历史诊断组的 `formal_evidence=false` 表示它们用于判断代码迁移和历史高分能否在当前环境出现，不能冒充从新只读母版启动的正式确认结果，也不会自动触发框架晋级。
