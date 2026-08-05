# AI 交叉审核协议

本协议定义 GTPJ 中代码、workflow、helper、模板、训练入口、评估语义和实验结论相关改动的 AI 审核门。目标不是增加仪式感，而是让重要改动在被信任前，先经过机器验证、命名 Codex 线程预审和必要的 Claude Code 只读审核。

## 不可跳过规则

- 机器验证永远必须运行。`run-ai-cross-review` 在没有验证命令时必须失败。
- Claude Code 只读审核，不改文件、不启动训练、不 push、不删除用户数据。若 Claude Code 已登录但连续出现连接拒绝、超时或空输出，这些失败不算审核轮次；改用彼此独立的只读 Codex Reviewer，每轮必须记录真实 reviewer instance id、独立上下文和 `fallback_reason: claude_code_unavailable`，不得伪装成 Claude。
- Codex 负责实现、修复、反驳、重跑验证和写回证据。
- owner 不参与日常审核；但 push、删除、远端发布、破坏性迁移、密钥处理和用户数据操作仍必须等待 owner 明确授权。
- `--skip-claude` 只能生成 blocked 证据包，不能当作正式通过。
- Claude 备用路线不是 `--skip-claude`：它仍需完成对应 tier 的 1 或 3 个独立只读审核轮次，且每轮 verdict 都必须为 pass；校验器会拒绝没有真实 instance id 或没有独立上下文声明的手写占位文件。
- 代码审核不被 `server_frozen_runner` 豁免。服务器 detached 训练可以不创建运行期命名线程，但代码、workflow、helper、模板或训练配置生成逻辑的改动仍必须先在专用代码审核分支完成本协议。
- 如果改动已经先发生在旧脏分支，后补切分支只能算草稿隔离；正式 Runner 前必须重新从干净基线切专用分支，迁移最小 diff，通过本协议和机器验证后再做 `pre-run freeze commit`。

## 审核分层

`review_tier` 只有三档：

```text
fast: 0 轮只读外部 Reviewer
review-1: 1 轮 Claude Code；Claude 不可用时为 1 个独立 Codex Reviewer
strict-3: 3 轮 Claude Code；Claude 不可用时为 3 个彼此独立的 Codex Reviewer
```

使用规则：

- `fast` 只允许 `risk_level: low` 的普通文档或轻量 workflow 修补；仍必须有机器验证通过和命名 Codex 线程预审通过。
- `review-1` 用于普通 workflow/helper/template 修补，不直接改变正式实验结论、训练入口、评估语义、promotion 或论文 claim。
- `strict-3` 只用于会污染正式实验结论的改动，包括训练入口、forward/loss/evaluation、data/split/label/class order/logits/metric、Runner、Warehouse、confirmation、promotion、baseline claim 和论文 claim。
- `risk_level: high` 或 scope/title/reason 中出现正式实验结论风险时，低于 `strict-3` 必须被 helper 拦截。

## 命名 Codex 线程预审

Claude Code 之前必须先创建或绑定一个命名 Codex 线程做只读预审。该线程只检查当前 diff、验证证据和结论风险，不改文件、不启动训练。

预审完成后必须立刻归档该线程，并写入：

```text
02_codex_named_thread_pre_review.md
```

必需字段：

```text
codex_named_thread_pre_review: pass
named_thread_required: true
thread_id: <真实 thread id>
thread_title: <左侧栏线程标题>
lifecycle: completed_archived
archived_before_claude: true
archive_result_confirms_completion: true
archive_result: <archive 返回内容或包含 thread_id、previous_status=completed、archived:true 的摘要>
verdict: pass
```

如果命名线程未归档、没有真实 id、没有 UI 显示名、没有 archive_result，或者 verdict 不是 `pass`，审核包必须 blocked。
`archive_result` 不能只写 `archived`、`pass`、`done` 这类普通字符串；helper 会校验其中的 thread id、`previous_status`、`completed` 和 `archived:true`。

## 验证 Profile

默认验证 profile 是：

```text
validation_profile: default-core
```

默认会运行不启动训练的核心命令：

```powershell
python workflow\gtpj_workflow.py validate
python workflow\gtpj_workflow.py validate-workflow-consistency
python workflow\gtpj_workflow.py audit-boundary
python -m py_compile workflow\gtpj_workflow.py
```

如果使用 `--no-default-validation`，必须至少提供一条 `--validation-command`，并记录：

```text
validation_profile: custom-debug | custom-full-equivalent
```

`medium` / `high` 风险或 `strict-3` 审核不能使用弱自定义验证冒充完整验证；需要 `default-core` 或 `custom-full-equivalent`。
`custom-full-equivalent` 必须真实包含核心 gate 命令，不能用 `echo`、`print`、`python -c` 等自报方式把命令名称打印出来冒充验证。

## 证据包

默认位置：

```text
docs/agent_reviews/YYYY-MM-DD-task-name/
```

所有证据包都必须包含：

```text
00_task.md
01_codex_actions.md
02_codex_named_thread_pre_review.md
02_diff.patch
02_focused_diff.md
02_review_brief.md
03_validation.md
04_claims.md
10_final_decision.md
```

按 `claude_rounds_required` 追加：

```text
review_tier: fast
claude_rounds_required: 0
```

```text
review_tier: review-1
claude_rounds_required: 1
05_claude_review_round_1.md
```

```text
review_tier: strict-3
claude_rounds_required: 3
05_claude_review_round_1.md
06_codex_response_round_1.md
07_claude_review_round_2.md
08_codex_response_round_2.md
09_claude_review_round_3.md
```

模板位置：

```text
experiments/templates/ai_cross_review_template.md
```

## 通过条件

最终决定文件必须满足：

```text
ai_cross_review_status: pass
owner_participation: not_required
review_tier: fast | review-1 | strict-3
claude_rounds_required: 0 | 1 | 3
claude_rounds_completed: 0 | 1 | 3
claude_code_read_only: true
codex_named_thread_pre_review: pass
codex_named_thread_lifecycle: completed_archived
codex_fixes_or_rebuttals_recorded: true
machine_gates_passed: true
unresolved_blocking_issues: 0
```

任一 blocking issue 未关闭时，最终决定必须是：

```text
ai_cross_review_status: blocked
```

blocked 改动不能进入正式 Runner、keep/best 决策、confirmation、promotion、baseline claim 或论文 claim。

## 快速审核优化

默认使用：

```text
prompt_profile: focused
review_mode: blocking-only
```

`focused` 模式下，Claude Code 默认只读 `CLAUDE.md`、`docs/workflow/CLAUDE_CONTEXT.md`、`02_codex_named_thread_pre_review.md`、`02_review_brief.md`、`02_focused_diff.md`、`03_validation.md` 和 `04_claims.md`。完整 `02_diff.patch` 必须保留，但只在 focused diff 无法定位问题时读取。

`blocking-only` 模式下，Claude Code 只报告会导致行为错误、证据污染、验证失败或正式实验结论不可靠的 blocking issues。

## 命令

生成审核包：

```powershell
python workflow\gtpj_workflow.py run-ai-cross-review --slug task-name --task-title "任务标题"
```

校验证据包：

```powershell
python workflow\gtpj_workflow.py validate-ai-cross-review --path docs\agent_reviews\YYYY-MM-DD-task-name
```
