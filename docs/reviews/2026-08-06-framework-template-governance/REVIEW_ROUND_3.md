# 第三轮：文档、Skill、Runner 证据与页面事实

```text
reviewer: runner_evidence_review
decision: allow
final_head: fd6921992b873a2d01db73010479340f67e59060
```

## 复核范围

- 根 `README.md`、`AGENTS.md`、项目状态与结构说明；
- 活跃 workflow 文档、参数矩阵协议、晋级协议；
- 本地 `gtpj-workflow` Skill；
- helper、测试、各框架 `TEMPLATE.yaml` 与 `EXPERIMENT.yaml`；
- UI-V1、UI-V2、UI-V3。

## 结论

- 历史 `framework/vX` 只作来源回查，新实验从准确冻结母版独立分叉；
- 晋级必须先瘦身和行为对照，再建立母版分支、Tag 和独立治理登记；
- 活跃文档扫描覆盖 manifest 的 `active`、`active_reference`，并额外覆盖根入口、参数矩阵协议、`workflow/README.md` 和本地 Skill；
- UI-V1 指向 UI-V3，UI-V3 的 14 个本地链接全部存在，四个框架的实验数量与账本一致；
- 原 `run-workflow --formal --experiment-dir` 检查被更严格的退役规则取代，正式入口是标准实验参数行冻结与启动收据。

无阻断、警告或未处理建议。
