# GTPJ-v1 Ablation 索引

ID 规范：`ABL-001_slug`；目录：`experiments/v1/ablation/ABL-001_slug/`。

创建前先确认 working tree clean，再从当前 `main` 开建议分支；helper 会拒绝在脏工作区、
`main` 或错误分支上创建实验目录。
不要在本索引里预占未来实验 ID，避免 helper 把计划项误判为已存在实验。

```bash
git switch main
git status --short
git switch -c exp/v1-ablation-001-disable-jepa
python workflow/gtpj_workflow.py new-experiment --version v1 --kind ablation --exp-id ABL-001 --slug disable_jepa
```

## 实验记录

| 实验 | 状态 | 目录 | 说明 |
|---|---|---|---|
| 暂无 | - | - | 由 `workflow/gtpj_workflow.py new-experiment` 创建后追加。 |
