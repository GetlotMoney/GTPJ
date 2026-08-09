# Quality Check（运行前）

```text
runtime: server_detached_role_only
decision: pre_run_ready_pending_campaign_review_gate
promotion_decision: not_applicable
evidence_level: pre_run_only
confirmation_status: not_applicable
subject_id: V5-ABLATION-004
subject_type: campaign_task
```

## 已检查

- [x] 实验直接继承 `MODEL-V5-TEMPLATE-V1`，没有继承其他实验代码。
- [x] 参数表只含 seed 5/17、repeat 1/2 的冻结任务。
- [x] 配置、代码和数据清单均由 campaign 在启动前重算哈希。
- [x] Runner、接口和证据检查使用三个不同文件。
- [x] 原始日志、checkpoint、cache 和图像不进入 GitHub。
- [x] 服务器停止文件与失败范围已经写入统一 campaign 控制器。
- [ ] 真实服务器 Linux、数据和 GPU 小跑待 campaign 统一完成。
- [ ] U/S/H/ZS、结果判断和 artifact 收据待真实任务完成后填写。

## 决定

当前只允许进入 campaign 最终审核门；不构成结果证据，不允许 promotion。
