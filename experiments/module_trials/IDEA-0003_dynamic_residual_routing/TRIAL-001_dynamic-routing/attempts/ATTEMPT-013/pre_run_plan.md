# ATTEMPT-013 Pre-Run Plan

## 结论

本轮计划 50 jobs，用本地多 agent 工作流完成 planning gate。当前不启动训练。

## 实验拆分

| 组 | 候选 | 配置 | seeds | jobs | 来源 |
|---|---|---|---|---:|---|
| A | DR047 | `direction_sample_h48_w0.535_a0.002` | 6-15 | 10 | ATTEMPT-011 top repeat |
| B | DR020 | `direction_sample_h48_w0.525_a0.003` | 6-15 | 10 | ATTEMPT-011 top repeat |
| C | DR041 | `direction_sample_h48_w0.515_a0.002` | 6-15 | 10 | ATTEMPT-011 top repeat |
| D | A011DR042 | `direction_sample_h48_w0.515_a0.004` | 6-15 | 10 | ATTEMPT-011 best single cluster |
| E | A011DR020 | `direction_sample_h48_w0.555_a0.0045` | 6-15 | 10 | ATTEMPT-011 h48 hotspot |

## 运行边界

- 当前阶段只写本地计划和 gate evidence。
- 不创建服务器 batch。
- 不执行 `start_batch.sh`。
- 不把 ATTEMPT-012 partial result 合并进 ATTEMPT-013 正式结果。

## 后续启动条件

后续若 owner 要求真正运行，需要再执行 runner 启动 gate：

1. 生成 frozen batch plan。
2. 确认本地和 lab4090 commit 对齐。
3. 确认 GPU 空闲、同 run id 无进程。
4. 确认 STOP_REQUESTED 机制存在。
5. 再由 owner 明确选择本地监控 runner 或服务器 detached runner。

