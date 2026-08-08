# 运行证据位置

仓库只保存轻量索引，不复制 checkpoint、完整训练日志、缓存或其他大文件。

真实运行证据应分别放在：

```text
.runtime/runs/v5/innovation/V5-INNOVATION-002_scale_consistent_fusion/RUN-001/
...
.runtime/runs/v5/innovation/V5-INNOVATION-002_scale_consistent_fusion/RUN-010/
```

每个已完成 RUN 至少核对：

- `training.log`
- `metrics.json`
- `config_snapshot.yaml`
- `run_identity.json`
- `model_best.pth`
- `checkpoint_last.pth`

目标 RUN 目录在开跑前必须不存在。若第一阶段失败，`RUN-007` 至 `RUN-010` 不创建目录，只在参数表和结果文件中记为 `stage1_gate_failed_not_started`。

当前状态：`not_started`，尚无运行证据。
