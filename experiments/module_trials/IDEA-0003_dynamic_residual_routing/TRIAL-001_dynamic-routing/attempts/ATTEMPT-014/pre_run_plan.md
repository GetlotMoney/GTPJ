# ATTEMPT-014 Pre-Run Plan

## 目标

本轮做 100 个严格复现 jobs，目标是验证 ATTEMPT-011 的高分 source single 是否能原样还原。训练准备走 `server_frozen_runner`：本地只做账本、gate、frozen plan 和后续上传启动；真实训练只在 lab4090 上跑。

## 复现规则

- repeat_type: `exact_repeat`
- seed: 保持 source seed=5
- config: 保持 source config，不换任何参数
- 每个候选最多 5 次
- 任一 clean repeat 达到该候选自己的 `restore_target_H=source_H`，只停止该候选剩余 repeat
- 接近但未达到只记 `near_miss_not_restored`，不能 confirmation，不能 early stop
- ATTEMPT-013 不作为复现证据，因为它换 seed

## 预算

| 项目 | 数量 |
|---|---:|
| source candidates | 20 |
| max repeats per candidate | 5 |
| total jobs | 100 |
| GPUs | 0,1 |

## 候选来源

候选来源见 `attempts/ATTEMPT-011/result.yaml` 的 `attempt014_source_candidates`。本轮只选纯 `direction_sample + h48 + fixed local/ICSA/PSE` source single，避免把 local+pse 组合机制混进复现问题。

## 批次

当前计划生成一个 100-job frozen batch：

```text
RUN-20260708-0001-h76-restore100-exact-repeat-2gpu
profile: h76-restore100-exact-repeat
```

后续若需要更细的服务器恢复控制，可以在上传前拆成 5 个 20-job batch；本地 helper 当前先生成单个 100-job plan。

## 启动边界

本文件只是前置计划。当前不上传、不启动服务器。启动前必须再做：

- `validate-agent-runtime`
- `multi-agent-preflight`
- `agent-cleanup-plan`
- `validate`
- `validate-workflow-consistency`
- `git diff --check`
- 服务器 branch/commit/GPU/旧进程/目标目录预检
