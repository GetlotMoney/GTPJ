# GTPJ-v1 Tune 索引

ID 规范：`TUNE-001_slug`；目录：`experiments/v1/tune/TUNE-001_slug/`。

创建前先确认 working tree clean，再从当前 `main` 开建议分支；helper 会拒绝在脏工作区、
`main` 或错误分支上创建实验目录：

```bash
git switch main
git status --short
git switch -c exp/v1-tune-001-topo008
python workflow/gtpj_workflow.py new-experiment --version v1 --kind tune --exp-id TUNE-001 --slug topo008
```

## 实验记录

| 实验 | 状态 | 目录 | 说明 |
|---|---|---|---|
| 暂无 | - | - | 由 `workflow/gtpj_workflow.py new-experiment` 创建后追加。 |
