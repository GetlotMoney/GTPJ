# ATTEMPT-011 Pre-run Plan

## 目标

本轮验证 `H=76` 动态路由后续搜索的正式服务器离线 workflow：本地只负责治理账本、冻结 batch、写 gate 证据和启动远端 detached supervisor；训练实际在 `lab4090` 上连续运行，即使本地电脑关机也不依赖当前 Codex 线程。

## 实验组成

| Batch | Run ID | Profile | Jobs | 组成 |
|---|---|---|---:|---|
| b01 | `RUN-20260706-0001-h76-mixed200-b01-search50-2gpu` | `h76-mixed200-b01-search50` | 50 | search 50 |
| b02 | `RUN-20260706-0002-h76-mixed200-b02-search50-2gpu` | `h76-mixed200-b02-search50` | 50 | search 50 |
| b03 | `RUN-20260706-0003-h76-mixed200-b03-search20-repeat20-ablate10-2gpu` | `h76-mixed200-b03-search20-repeat20-ablate10` | 50 | search 20 + repeat 20 + ablation 10 |
| b04 | `RUN-20260706-0004-h76-mixed200-b04-repeat20-ablate30-2gpu` | `h76-mixed200-b04-repeat20-ablate30` | 50 | repeat 20 + ablation 30 |

总计 200 jobs：120 search、40 same-seed exact repeat、40 ablation。

## 固定训练设置

```text
base_version: v5
batch_size: 64
seed: 5
Config epochs field: 30
Planned train epochs: 50
Epoch schedule source: lr_stages
LR stages: 20 + 20 + 10
GPUs: 0,1
```

## 候选来源

repeat 和 ablation 固定围绕当前 top4 候选：

| Source | Config | Source H | 本轮用途 |
|---|---|---:|---|
| DR-020 | `direction_sample_h48_w0.525_a0.003` | 75.00 | repeat + ablation |
| DR-051 | `direction_sample_h48_w0.545_a0.004` | 74.96 | repeat + ablation |
| DR-041 | `direction_sample_h48_w0.515_a0.002` | 74.83 | repeat + ablation |
| DR-047 | `direction_sample_h48_w0.535_a0.002` | 74.82 | repeat + ablation |

ATTEMPT-010 已证明 workflow smoke 可以跑通并写回结果，但它只完成 4/20 jobs，因此不作为完整 confirmation 证据。

## 启动边界

- formal runner 启动前必须通过 `agent_runtime.yaml`、`validate-agent-runtime`、`multi-agent-preflight`、`agent-cleanup-plan`。
- 不允许使用 `temporary_subagent` 或右侧栏临时 agents。
- 只有左侧命名 Codex 线程证据通过后，才能上传并启动服务器 detached supervisor。
- 本轮 promotion 继续 blocked；结果只进入 search/repeat/ablation 证据表。

## 停止机制

每个 batch runner 生成时已带 `STOP_REQUESTED` 检查。需要停止时，在对应 batch 目录创建 `STOP_REQUESTED` 文件即可。已开始的 job 允许完成；未开始的 job 会被标记为 `skipped`，避免 controller 抢跑后续任务。
