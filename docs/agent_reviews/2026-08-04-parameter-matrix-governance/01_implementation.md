# 实施记录

## 正式入口

- 规范：`docs/workflow/protocols/parameter_matrix_protocol.md`
- 总看板：`experiments/PARAMETER_MATRIX_CATALOG.md`
- 模板：`experiments/templates/PARAMETER_MATRIX_template.csv`
- 工作流版本：`SKILL-GTPJ-WORKFLOW-V2.1`

## 已实现的保护

- `new-experiment` 自动生成一行 draft 参数表。
- `freeze-parameter-matrix` 把某一行实际配置快照、配置指纹和种子写回 CSV，并重建 Markdown 阅读版。
- `validate-parameter-matrix --require-ready` 做整批字段、配置快照、重复配置、复跑来源和阅读版一致性检查。
- `refresh-parameter-matrix-view` 用 CSV 重建阅读版，防止两份表分别手改。
- `record-result`、`record-module-attempt` 只有在实际配置、seed 和选中行都一致时才写正式结果；已完成行不能被覆盖。
- 动态路由的 `prepare-dynamic-routing-matrix`、正式计划和 `sync-dynamic-routing-matrix` 共同核对 Attempt、计划任务集合和 Warehouse 结果来源。

## 未做的事

- 没有补造 v3→v4 或 ATTEMPT-001 至 ATTEMPT-018 的历史行；它们保留在迁移队列，后续只能从 Warehouse 资料恢复。
- 本次不是技术栈、渲染、框架或核心依赖变更，因此未更新 `docs/TECH_STACK_HISTORY.md`。
