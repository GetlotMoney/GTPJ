# ATTEMPT-017 Pre-Run Plan

## 目标

当前纯 `h48 + direction_sample + weight_s2v / anchor` 调参已经出现平台期：ATTEMPT-015 能产生 H>=75 的单次结果，但 ATTEMPT-016 的已完成 exact repeat 暂未还原原水平。因此本轮不继续单纯加密二维网格，而是探索已经由现有代码支持的动态路由机制组合。

## 计划

| 项目 | 值 |
|---|---|
| run_id | RUN-20260709-0001-h76-escape100-supported-routing-server-frozen-2gpu |
| profile | h76-escape100-supported-routing |
| jobs | 100 |
| execution | server_frozen_runner |
| start_policy | detached screen；先等待 ATTEMPT-016 结束和 GPU 空闲，再启动 |
| local_batch_dir | .gtpj_runtime/batches/RUN-20260709-0001-h76-escape100-supported-routing-server-frozen-2gpu |
| server_batch_dir | /data/lby/projects/cv_project/GTPJ/.gtpj_runtime/batches/RUN-20260709-0001-h76-escape100-supported-routing-server-frozen-2gpu |
| python | /data/lby/.conda/envs/dvsr_gpu/bin/python |

## 100 jobs 分配

| 组 | 数量 | 内容 | 证据边界 |
|---|---:|---|---|
| h76_escape_direction_micro | 30 | 围绕 ATTEMPT-015 top2 和一条 ridge 做纯 direction 微调 | tune single only |
| h76_escape_hidden_sweep | 15 | 在 3 个热点上扫 h=40/44/52/56/64 | tune single only |
| h76_escape_local_sample_tune | 15 | 小权重 local sample 组合 | tune single only |
| h76_escape_pse_class_tune | 15 | PSE class 组合，不使用 unsupported sample | tune single only |
| h76_escape_icsa_guarded_tune | 10 | 小比例 ICSA guarded 探针 | tune single only |
| h76_escape_ablate_mechanism | 10 | direction fixed、anchor、weight 的窄消融 | mechanism check only |
| h76_escape_sentinel_control | 5 | 静态、fixed 和桥接控制点 | sanity/control only |

## 启动前检查

- `validate-agent-runtime` 必须通过。
- `multi-agent-preflight` 必须通过。
- `agent-cleanup-plan` 必须显示无命名线程需要处理。
- `py_compile`、focused pytest、`validate`、`validate-workflow-consistency`、`git diff --check` 必须通过。
- 服务器当前还有 ATTEMPT-016 运行；ATTEMPT-017 supervisor 必须等待 ATTEMPT-016 训练进程结束、GPU 空闲、目标 run 目录不存在或未污染后再启动。

## 停止和恢复

- 停止：在服务器 run 目录创建 `STOP_REQUESTED`，已运行 job 允许完成，pending job 不再启动。
- 恢复检查：见 `monitor_handoff.md`。
