# AI 交叉审核协议

> 当前规则：只改账本、说明文档或已审核代码支持的普通参数，机器检查通过即可；任何实验代码、模型、训练、数据、loss、eval、workflow/helper、模板或训练配置生成逻辑改动，目标测试通过后必须完成 2 轮不同子 Agent 的对抗式只读审核。旧 `review-1`、`strict-3` 和完整 Claude Code evidence pack 只保留给历史兼容或 owner 当前明确要求的特殊审计，不再是普通新实验代码的默认门槛。

机器测试仍不能省：目标测试、配置检查和真实最小样例优先于 Reviewer 数量。审核总耗时不得超过训练准备上限；参数实验 10 分钟、代码或评估实验 30 分钟，超时后只处理唯一真实阻断，不继续增加审核层。

本协议定义 GTPJ 中代码、workflow、helper、模板、训练入口、评估语义和实验结论相关改动的 AI 审核门。目标不是增加仪式感，而是让重要改动在被信任前，先经过机器验证和两轮独立反方检查。

## 不可跳过规则

- 机器验证永远必须运行。
- 两轮 Reviewer 都只读，不改文件、不启动训练、不 push、不删除用户数据。Claude Code 可以作为其中一轮 Reviewer；Claude 不可用时，直接使用不同的只读 Codex 子 Agent，不把失败调用算作审核轮次。
- Codex 负责实现、修复、反驳、重跑验证和写回证据。
- owner 不参与日常审核；但 push、删除、远端发布、破坏性迁移、密钥处理和用户数据操作仍必须等待 owner 明确授权。
- 第 1 轮主动寻找实现、接口、shape、梯度、数据与评估错误；实现者修复、重跑测试并由第 1 轮 Reviewer 复核通过后，才能启动第 2 轮。
- 第 2 轮必须检查同一份最终代码，并从反方立场寻找反例、隐藏耦合、回归和测试盲区。若第 2 轮导致代码再次修改，原两轮结论失效，仍由这两个 Reviewer 按第 1 轮 -> 第 2 轮重新检查。
- 两轮必须绑定同一个 `reviewed_code_id`，并绑定相同的 `reviewed_extra_files`。两轮都明确通过、`unresolved_blockers: 0` 且机器测试通过，代码才算完成并允许进入正式训练。
- 代码审核不被 `server_frozen_runner` 豁免。服务器 detached 训练可以不创建运行期命名线程，但代码、workflow、helper、模板或训练配置生成逻辑的改动仍必须完成本协议。

## 审核分层

当前新实验默认只分两类：

```text
docs_or_parameter_only: 0 轮外部 Reviewer，机器检查通过即可
experiment_code_change: 2 轮不同子 Agent 只读审核
```

旧 helper 和旧审核包仍可能出现下面三个兼容字段：

```text
fast: 0 轮只读外部 Reviewer
review-1: 1 轮 Claude Code；Claude 不可用时为 1 个独立 Codex Reviewer
strict-3: 3 轮 Claude Code；Claude 不可用时为 3 个彼此独立的 Codex Reviewer
```

兼容使用规则：

- `fast` 只用于普通说明文档、账本和低风险轻量说明修补。
- `review-1` 和 `strict-3` 是历史审核包字段；新实验代码默认不靠这两个词决定轮数，而是直接执行两轮不同子 Agent 审核。
- owner 明确要求特殊审计时，可以继续使用旧完整 evidence pack；此时仍必须保证机器验证通过、Reviewer 只读、发现已修复、最终结论不伪装。

## 旧完整审核包兼容：命名 Codex 线程预审

只有 owner 当前明确要求 Claude Code 或旧完整 evidence pack 时，才需要先创建或绑定一个命名 Codex 线程做只读预审。普通新实验代码审核直接使用两轮不同子 Agent 只读记录即可，不为了形式创建命名线程。

旧完整包里，Claude Code 之前必须先创建或绑定一个命名 Codex 线程做只读预审。该线程只检查当前 diff、验证证据和结论风险，不改文件、不启动训练。

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
independent_codex_fallback_read_only: false
codex_named_thread_pre_review: pass
codex_named_thread_lifecycle: completed_archived
codex_fixes_or_rebuttals_recorded: true
machine_gates_passed: true
unresolved_blocking_issues: 0
```

若全部轮次由独立 Codex Reviewer 备用完成，上面两行必须改为：

```text
claude_code_read_only: false
independent_codex_fallback_read_only: true
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
