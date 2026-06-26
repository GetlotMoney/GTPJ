# GTPJ-v1 Confirmation 索引

ID 规范：`CONFIRM-001_slug`；目录：`experiments/v1/confirmation/CONFIRM-001_slug/`。

创建前先确认 working tree clean，再从当前 `main` 开建议分支；helper 会拒绝在脏工作区、
`main` 或错误分支上创建实验目录：

```bash
git switch main
git status --short
git switch -c exp/v1-confirm-001-v1-seed5
python workflow/gtpj_workflow.py new-experiment --version v1 --kind confirmation --exp-id CONFIRM-001 --slug v1_seed5
```

## 实验记录

| 实验 | 状态 | 目录 | 说明 |
|---|---|---|---|
| `CONFIRM-001_v1_seed5` | keep | `experiments/v1/confirmation/CONFIRM-001_v1_seed5` | H=73.77, delta_H=-0.16; Warehouse artifacts registered. |
