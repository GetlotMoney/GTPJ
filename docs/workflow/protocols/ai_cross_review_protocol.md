# AI 交叉审核协议

本协议定义 GTPJ 中代码、workflow、helper、模板、训练入口、评估语义和实验结论相关改动的 AI 审核门。目标不是增加仪式感，而是让重要改动在被信任前，先经过机器验证、临时 Codex 预审和必要的 Claude Code 只读审核。

## 不可跳过规则

- 机器验证永远必须运行。`run-ai-cross-review` 在没有验证命令时必须失败。
- Claude Code 只读审核，不改文件、不启动训练、不 push、不删除用户数据。
- Codex 负责实现、修复、反驳、重跑验证和写回证据。
- owner 不参与日常审核；但 push、删除、远端发布、破坏性迁移、密钥处理和用户数据操作仍必须等待 owner 明确授权。
- `--skip-claude` 只能生成 blocked 证据包，不能当作正式通过。

## 审核分层

`review_tier` 只有三档：

```text
fast: 0 轮 Claude Code
review-1: 1 轮 Claude Code
strict-3: 3 轮 Claude Code
```

使用规则：

- `fast` 只允许 `risk_level: low` 的普通文档或轻量 workflow 修补；仍必须有机器验证通过和临时 Codex agent 预审通过。
- `review-1` 用于普通 workflow/helper/template 修补，不直接改变正式实验结论、训练入口、评估语义、promotion 或论文 claim。
- `strict-3` 只用于会污染正式实验结论的改动，包括训练入口、forward/loss/evaluation、data/split/label/class order/logits/metric、Runner、Warehouse、confirmation、promotion、baseline claim 和论文 claim。
- `risk_level: high` 或 scope/title/reason 中出现正式实验结论风险时，低于 `strict-3` 必须被 helper 拦截。

## 临时 Codex 预审

Claude Code 之前必须先启动一个临时 Codex agent 做只读预审。该 agent 只检查当前 diff、验证证据和结论风险，不改文件、不启动训练。

预审完成后必须立刻关闭该 agent，并写入：

```text
02_codex_temp_agent_pre_review.md
```

必需字段：

```text
codex_temp_agent_pre_review: pass
temporary_agent_required: true
agent_instance_id: <真实 agent id>
ui_display_name: <右侧栏显示名>
lifecycle: completed_closed
closed_before_claude: true
close_result_confirms_completion: true
close_result: <close_agent 返回内容或包含 agent_id、previous_status=completed、closed:true 的摘要>
verdict: pass
```

如果临时 agent 未关闭、没有真实 id、没有 UI 显示名、没有 close_result，或者 verdict 不是 `pass`，审核包必须 blocked。
`close_result` 不能只写 `closed`、`pass`、`done` 这类普通字符串；helper 会校验其中的 agent id、`previous_status`、`completed` 和 `closed:true`。

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
02_codex_temp_agent_pre_review.md
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
codex_temp_agent_pre_review: pass
codex_temp_agent_lifecycle: completed_closed
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

`focused` 模式下，Claude Code 默认只读 `CLAUDE.md`、`docs/workflow/CLAUDE_CONTEXT.md`、`02_codex_temp_agent_pre_review.md`、`02_review_brief.md`、`02_focused_diff.md`、`03_validation.md` 和 `04_claims.md`。完整 `02_diff.patch` 必须保留，但只在 focused diff 无法定位问题时读取。

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
