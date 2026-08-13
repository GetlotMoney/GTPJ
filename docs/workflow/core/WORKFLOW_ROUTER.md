# GTPJ V6 任务路由

| 请求 | 当前执行卡 |
|---|---|
| 读论文、找创新点 | `playbooks/paper_intake.md` |
| 论文到实验 | `playbooks/paper_to_experiment.md` |
| 调参 | `playbooks/tune.md` |
| 消融 | `playbooks/ablation.md` |
| 复现、确认 | `playbooks/confirmation.md` |
| 新机制、新模块 | `playbooks/innovation.md` |
| 升版 | `playbooks/promotion.md` |
| 组合实验 | `playbooks/mixed_campaign.md` |
| 长周期研究 | `playbooks/autonomous_campaign.md` |

只读查询不进入实验流程。正式实验先确定所属 `FRAMEWORK-VX` 和准确母版；tune、ablation、innovation、confirmation 分别写入所属框架目录。创新经 confirmation 并由 owner 接纳后，才注册新的同级正式框架。

旧 Router 全文见 `../archive/specs/WORKFLOW_PRE_V6_ARCHIVE.md`，没有当前命令权。
