# Experiment Issue Memory

具体问题已经拆分到日期化问题库：

```text
docs/workflow/issues/
```

新对话默认读取：

```text
docs/workflow/issues/README.md
docs/workflow/issues/<最近日期>.md
```

不要每次全量阅读所有历史问题；只有当最近文档无法解释当前问题时，再按关键词检索旧文档。

## 最近问题

- `docs/workflow/issues/2026-06-27-trial001-batch-runner-and-tag-boundary.md`
- `docs/workflow/issues/2026-06-26-trial001-sweep-preflight-and-runner.md`

## 记录规则

- 每个问题必须包含症状、影响范围、根因、解决方案、预防规则。
- 同类问题出现 2 次，补到 `docs/workflow/runbook.md`。
- 同类问题出现 3 次，优先沉淀到 `workflow/gtpj_workflow.py` helper。
- raw log、checkpoint、长 traceback 不复制进 Git；只记录 artifact id、路径、摘要和解决方案。
