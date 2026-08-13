# GTPJ V6 最小启动摘要

只有创建实验、改训练/评估含义、冻结运行、启动训练、记录正式结果或晋级版本时，才写下面的最小摘要：

```yaml
question:
baseline_commit:
experiment_type:
config_or_parameter_matrix:
data_and_split_identity:
seed_and_eval:
output_directory:
blocking_issue:
```

能直接确认的字段由 Agent 自动填写；只报告唯一真实阻断，不让 owner 填长表。旧启动卡字段见 `../archive/specs/WORKFLOW_PRE_V6_ARCHIVE.md`。
