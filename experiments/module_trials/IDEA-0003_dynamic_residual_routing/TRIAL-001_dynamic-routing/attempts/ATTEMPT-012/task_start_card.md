# ATTEMPT-012 Task Start Card

## 任务判定

- owner_request: 继续实验，做 50 轮，由 Coordinator 规划并开始。
- workflow_task_type: trial_internal_confirmation
- experiment_type: confirmation / multi-seed stability
- base_version: v5
- trial: IDEA-0003 / TRIAL-001 dynamic residual routing
- attempt_id: ATTEMPT-012
- run_id: RUN-20260706-0005-h76-followup50-multiseed-2gpu
- profile: h76-followup50-multiseed

## 启动边界

- activation_mode: role_only
- agent_instance_mode: role_only
- formal_runtime_backend: server_detached_role_only
- thread_creation_allowed: false
- runner_target: lab4090
- local_shutdown_safe: true
- promotion_gate: blocked

本轮不创建 Codex 子线程，不使用右侧临时 agents，也不把当前聊天上下文当作长期监控依赖。正式运行事实以服务器 batch 文件为准。
