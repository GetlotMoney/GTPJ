# ATTEMPT-015 Pre-Run Plan

## 目标

本轮是 `live_multi_agent_monitor` 正式工作流下的 100 组调参搜索，训练在 `lab4090` 服务器运行，当前 owner 对话负责治理、gate、上传、启动和监控。

## 类型边界

- experiment_type: `tune_search`
- profile: `h76-hotspot100-tune`
- jobs: 100
- seed: 固定 `5`
- 目标: 找到新的 `GZSL H >= 75.0` 单点
- 不是 confirmation，不是 promotion，不是 baseline-grade evidence
- 若出现 H>=75，只能进入下一轮 same-seed same-config exact repeat 复现

## 调参范围

本轮只动两个已允许的配置参数：

- `weight_s2v`
- `dynamic_gate_anchor_lambda`

固定不动：

- `dynamic_direction_mode: sample`
- `dynamic_gate_hidden: 48`
- `dynamic_local_mode: fixed`
- `dynamic_icsa_mode: fixed`
- `dynamic_pse_mode: fixed`
- CUB split、seen/unseen label mapping、class order、GZSL metric evaluator、training/eval logits interface

## 证据来源

主要依据 `ATTEMPT-014/result.yaml` 和 `ATTEMPT-014/quality_check.md`：

- best single: H=74.99 at `w=0.500, anchor=0.003`
- promising near-miss: `w=0.550, anchor=0.003`
- stable restored lower-target region: `w=0.545, anchor=0.002`
- low-anchor ridge: `w=0.535, anchor=0.0015~0.0025`

ATTEMPT-014 没有 H>=75，因此它只支持 follow-up tuning，不支持 promotion。

## Multi-Agent Gate

已使用左侧命名 Codex 线程输出独立 pre-run allow：

- Tune Planner
- Evidence Quality Checker
- Result Comparator
- Runner Monitor
- Interface Checker

禁止使用右侧 `temporary_subagent` / `spawn_agent`。本轮 `agent_runtime.yaml` 只记录左侧命名线程。

## 启动边界

启动前必须通过：

- `validate-agent-runtime`
- `multi-agent-preflight`
- `agent-cleanup-plan`
- `validate-evidence-routing`
- `validate`
- `validate-workflow-consistency`
- `git diff --check`
- lab4090 只读预检：server commit、GPU0/1 idle、同 run id 无旧进程、目标 run 目录未污染

启动后以服务器 `batch_status.json`、`summary.csv/jsonl`、`events.jsonl` 和 controller logs 为准。
