# GTPJ V6 启动卡

正式实验只需要记录：

```yaml
question:
baseline:
run_commit:
experiment_type:
config_snapshot:
parameter_matrix:
data_split_identity:
seed:
evaluation:
output_directory:
machine_checks:
review_status:
```

代码、workflow、helper、模板或生成逻辑修改必须在机器测试后完成两轮依次进行的只读审核；普通参数或 seed 修改不改变语义时只做直接检查。正式训练从 clean、冻结的唯一 commit 启动，结果写入独立 RUN 目录。

旧版完整启动卡见 `../archive/specs/WORKFLOW_PRE_V6_ARCHIVE.md`，没有当前命令权。
