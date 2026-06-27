# Experiment Issue Knowledge Base

本目录是 GTPJ 实验执行问题的持久经验库。

## 读取规则

- 新对话默认先读本文件，再读最近日期的问题文档。
- 不要每次全量阅读所有历史问题；只有当最近文档无法解释当前问题时，再按关键词检索旧文档。
- 每个问题文档必须写清：症状、影响范围、根因、解决方案、预防规则、是否需要沉淀到 helper。
- 如果同类问题出现 2 次，同步补充 `docs/workflow/runbook.md`。
- 如果同类问题出现 3 次，优先沉淀到 `workflow/gtpj_workflow.py` helper，而不是继续靠聊天记忆。

## 命名规则

```text
YYYY-MM-DD-<short-topic>.md
```

同一天多个问题可以放在同一日期文件里。每个问题块使用稳定 ID：

```text
ISSUE-YYYYMMDD-001
```

## 当前最近文档

- `2026-06-27-trial001-batch-runner-and-tag-boundary.md`
- `2026-06-26-trial001-sweep-preflight-and-runner.md`

## 问题索引

| ID | 日期 | 主题 | 文档 | 状态 |
|---|---|---|---|---|
| ISSUE-20260626-001 | 2026-06-26 | PowerShell heredoc mismatch | `2026-06-26-trial001-sweep-preflight-and-runner.md` | fixed |
| ISSUE-20260626-002 | 2026-06-26 | L2SP belongs to a new trial | `2026-06-26-trial001-sweep-preflight-and-runner.md` | guarded |
| ISSUE-20260626-003 | 2026-06-26 | Post-run overhead must be helper-first | `2026-06-26-trial001-sweep-preflight-and-runner.md` | active |
| ISSUE-20260626-004 | 2026-06-26 | Multi-line python -c is fragile in PowerShell | `2026-06-26-trial001-sweep-preflight-and-runner.md` | fixed |
| ISSUE-20260626-005 | 2026-06-26 | Runtime state must stay under `.gtpj_runtime/` | `2026-06-26-trial001-sweep-preflight-and-runner.md` | fixed |
| ISSUE-20260626-006 | 2026-06-26 | Background runner must capture launch-time errors | `2026-06-26-trial001-sweep-preflight-and-runner.md` | fixed |
| ISSUE-20260627-007 | 2026-06-27 | Long batch stopped at ATTEMPT-021 | `2026-06-27-trial001-batch-runner-and-tag-boundary.md` | retry-needed |
| ISSUE-20260627-008 | 2026-06-27 | Trial tag and attempt tag boundary confusion | `2026-06-27-trial001-batch-runner-and-tag-boundary.md` | fixed |
| ISSUE-20260627-009 | 2026-06-27 | Trial/root indexes drift from current best attempt | `2026-06-27-trial001-batch-runner-and-tag-boundary.md` | fixed |

## 快速处置原则

```text
环境/命令问题 -> 先看最近问题文档，再看 runbook。
证据/账本问题 -> 先看 trial README/result/quality，再看 issues。
指标异常问题 -> 先看 attempt result/log artifact，再看 issues。
workflow 规则争议 -> 先看 docs/workflow/git_policy.md、module_trial_protocol.md，再看 issues。
```
