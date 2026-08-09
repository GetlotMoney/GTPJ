# 运行证据位置

仓库只保存轻量索引，不复制 checkpoint、完整训练日志、缓存或其他大文件。

真实运行证据已分别放在：

```text
.runtime/runs/v5/innovation/V5-INNOVATION-002_scale_consistent_fusion/RUN-001/
...
.runtime/runs/v5/innovation/V5-INNOVATION-002_scale_consistent_fusion/RUN-006/
```

每个已完成 RUN 至少核对：

- `training.log`
- `metrics.json`
- `config_snapshot.yaml`
- `run_identity.json`
- `model_best.pth`
- `checkpoint_last.pth`

## 已完成 RUN 的轻量索引

| RUN | metrics.json SHA-256 | training.log SHA-256 | run_identity.json SHA-256 |
|---|---|---|---|
| RUN-001 | `817dd5381375e9b493434e474d920cafdfaf0f156fdf792395656e2c1712b1ef` | `46b7c8de9558c366b945d7276da350798b1443d74fed31cbf0dbd1d6f3ee91b9` | `ef3aa3d2507eb12140e7ee2f46362952696bb491ec2394b81becc22304c676d2` |
| RUN-002 | `c13362dd2a5da6d9b08556b32f360c927221ddf517371d60fb94d2575c35b3d5` | `01aa86390eb0a2b6a6aa5a368696e8c8305fb4e6613db0b1e99e83d2008a7b34` | `5c70445adc7e1255a8600f2104e01bef9a04e931c682dcca5bda539518c8c60c` |
| RUN-003 | `8209b05ec2b804f6a9a031a54c76e455ef37f1df8ad1781f58217edd0d67561e` | `a752889bccd70e5f723f2c14bfb1855053777d037e9211c5f96c82e78f1cfffc` | `d129329d164f31ea23909572c8f393844dea62692bd0ee132467f8bcec2ff79e` |
| RUN-004 | `fbc50f566212488cc476b376cd0924dbbe9c3061132738e5ab53c2695dfaf555` | `9fea59af5085d2879323d96fb8370a285285fe3f38fa03ee2b64b9cfa81be693` | `5b37125c398b0f88fef05cd3b227a5a3c713dd159f74c17fe5a95b6ac9acd54d` |
| RUN-005 | `6bb5f67da1741cccd2372ed259af042975850d9f0c416ef2e8271a0f44d9e77f` | `5bbf11134c76ac41bac3ab4c25f2fa109663bad0a32b21aa4229f790672b4a43` | `bdb9ca709df651ea5e05e6de0f66c22f0cbf150d14e6ddd2e528296fcbb50aa2` |
| RUN-006 | `09cf584a3378d5d8cc5424fa68702bc2fac06bdeadcc64b7981e6a89ffffb921` | `f5c86594330e112bf0619130e02790a75a6e2277e51a0d54554756aff8ce11c9` | `514f10355d4b640e6f3214ff10b87a66c5c38227ad542df507e5b5881fdef8cd` |

目标 RUN 目录在开跑前均不存在。第一阶段失败后，`RUN-007` 至 `RUN-010` 没有创建目录，只在参数表和结果文件中记为 `stage1_gate_failed_not_started`。

当前状态：`completed_stage1_gate_failed`。checkpoint、完整日志和缓存仍不进 Git。
