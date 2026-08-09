# ATTEMPT-010 Task Start Card

## 启动摘要

- 任务类型：trial 内部复现确认。
- subject_id：`ATTEMPT-010`。
- 目标：复现 ATTEMPT-009 中 H76 100 组搜索得到的前四个候选。
- repeat 类型：`same_seed_min5_exact_repeat`。
- 基于版本：`v5`。
- 基于代码：服务器运行分支 `codex/h76-campaign-20260704`，来源 run commit `d505e992492eb6fe7272edf0f0dc1d15a5932434`。
- 来源 run：`RUN-20260704-0002-h76-existing-routing-100-2gpu`。
- 新 run：`RUN-20260705-0001-confirm-dr020-051-041-047-sameseed5x-2gpu`。
- workflow profile：`h76-top4-min5-repeat`。
- jobs：20 个，`DR-020 / DR-051 / DR-041 / DR-047` 各 5 次。
- seed：全部固定为来源 seed `5`。
- GPU：`0,1`。
- formal evidence：是，但 promotion 仍阻断，必须等待复现结果和质量检查。

## 复现对象

| 来源 job | 来源配置 | 来源 H | 本轮 repeats |
|---|---|---:|---:|
| `DR-020` | `direction_sample_h48_w0.525_a0.003` | 75.00 | 5 |
| `DR-051` | `direction_sample_h48_w0.545_a0.004` | 74.96 | 5 |
| `DR-041` | `direction_sample_h48_w0.515_a0.002` | 74.83 | 5 |
| `DR-047` | `direction_sample_h48_w0.535_a0.002` | 74.82 | 5 |

## 硬门

- `agent_runtime.yaml` 必须通过。
- `multi-agent-preflight` 必须通过。
- `agent-cleanup-plan` 必须可读。
- Interface Checker 已允许：不改变 GZSL split、class order、label mapping、logits shape、U/S/H/ZS 语义。
- Evidence Quality Checker 已允许启动 repeat runner，但阻断 promotion。
- Runner Monitor 已允许：服务器 GPU 空闲，旧 100 组已完成。

