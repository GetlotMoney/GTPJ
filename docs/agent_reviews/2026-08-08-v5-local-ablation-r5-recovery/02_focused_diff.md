# 重点差异

- `workflow/gtpj_workflow.py`：支持当前 V5 中文最佳成绩汇总行，保留旧英文格式。
- `PARAMETER_MATRIX.csv`：完整保留 R3/R4，恢复 `RUN-007/010`，新增四个 R5 身份；两项完成历史固定证据清单 SHA-256。
- `tools/run_v5_ablation_001_server_controller.py`：正式启动前核对完成历史的清单、job/run、命令、收据、日志、退出码、指标、证据路径和逐文件哈希。
- `tests/`：覆盖中文解析、缺清单、错误清单哈希和证据文件被替换等失败路径。
- 训练模型、训练入口、数据、评估和 R5 配置没有变化。

完整差异见 `02_diff.patch`。
