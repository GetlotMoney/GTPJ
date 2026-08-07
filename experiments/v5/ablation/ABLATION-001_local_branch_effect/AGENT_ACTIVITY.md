# Agent 活动记录

subject_id: V5-ABLATION-001
runtime_backend: server_detached_role_only
named_training_threads: none

## 2026-08-07 开跑前

- runner_monitor：确认双 GPU 固定队列、STOP 机制、一次性运行身份和失败恢复规则，结论 `allow`；
- interface_checker：确认两组只相差局部子系统，三个 seed 严格配对，结论 `allow`；
- evidence_quality_checker：确认数据清单、收据和结果边界，结论 `allow`；
- 正式训练尚未启动；启动后由当前主任务读取 `status.json`、GPU 进程和日志向用户汇报；
- 训练阶段不创建命名 Codex 任务，因此没有需要归档的训练任务。

## 2026-08-08 正式运行与结果收口

- runner_monitor：确认 `RUN-013…016` 在两张 GPU 上按队列启动并全部返回 0；控制器最终状态为 `completed`，四个进程树均已停止；
- log_analyst：从四份中文最佳成绩结尾读取 seed 17、29 的 U/S/H/ZS 与最佳 epoch，并与封口日志和结束收据核对；
- evidence_quality_checker：为四个 R5 任务逐一固定启动收据、结束收据、封口日志、内部日志和最佳模型的文件大小与 SHA-256；
- result_analyst：三种子 H 配对差值为 `+0.25/-0.09/+0.09`，均值 `+0.08`，当前证据不支持稳定 H 增益；
- 训练阶段没有创建命名任务；训练后正式结论另走 strict-3 独立复核。
- strict-3 训练后复核：`/root/r5_recovery_audit@a9f8a83`、`/root/scientific_semantics_review@a9f8a83`、`/root/release_reliability_review@a9f8a83` 三路均为 PASS，无阻断。
