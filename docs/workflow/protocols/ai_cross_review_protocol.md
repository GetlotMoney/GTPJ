# AI 交叉审核协议

本协议定义 GTPJ 中重要代码、workflow、helper、模板、训练、评估和实验决策改动的“免 owner 日常参与”审核门。

目标不是增加仪式感，而是让每个重要改动在被信任前，先经受一次独立、只读、可复现的反向审查。

## 核心规则

日常审核不要求 owner 参与。

Codex 可以实现、修复和记录反驳。Claude Code 只读审核。Codex 必须对 Claude Code 的每个发现给出三类回应之一：

```text
修复
基于证据驳回
标记 blocked
```

最终是否接受改动，由机器验证和审核证据包共同决定。

owner 不参与日常审核循环，但 push、删除、远端发布、破坏性迁移、密钥处理和用户数据操作仍必须等待 owner 明确授权。

## 必需轮次

高影响改动必须执行三轮 AI 交叉审核：

```text
第 1 轮：Claude Code 审查原始 diff 和证据包。
第 2 轮：Codex 修复或反驳，重跑验证，Claude Code 审查更新后的状态。
第 3 轮：Codex 关闭剩余问题，重跑验证，Claude Code 做最终接受性审查。
```

每一轮 Claude Code 都必须保持只读。Claude 的发现必须引用具体文件、行号范围、命令或缺失证据。没有可复现抓手的意见可以记录为 non-blocking concern，但不能只凭观点阻断。

## 触发条件

以下改动必须执行三轮 AI 交叉审核：

- workflow helper 代码改动；
- 会创建或改变硬门的 workflow 协议、模板或规范改动；
- model、forward、loss、evaluation、data、split、class-order、metric 或 training-entry 改动；
- module trial 中代码语义发生变化，且即将进入正式 Runner；
- 会影响 keep、best、rerun、confirmation、promotion、baseline 或论文 claim 的结果解释；
- owner 明确要求 Claude/Codex 审核的任何任务。

不改变硬门、代码或实验结论的小型文档修订，可以不启用本协议。

## 证据包

审核证据包应放在改动所在目录附近，或统一放在：

```text
docs/agent_reviews/YYYY-MM-DD-task-name/
```

证据包必须包含：

```text
00_task.md
01_codex_actions.md
02_diff.patch
03_validation.md
04_claims.md
05_claude_review_round_1.md
06_codex_response_round_1.md
07_claude_review_round_2.md
08_codex_response_round_2.md
09_claude_review_round_3.md
10_final_decision.md
```

模板位置：

```text
experiments/templates/ai_cross_review_template.md
```

证据包正文必须使用中文；命令、字段名、文件名、代码标识和必要英文接口名可以保留原文。

## Claude Code 调用方式

推荐本地命令形态：

```powershell
$prompt = "阅读审核证据包。不要修改文件。只报告能用文件路径、行号、缺失测试、未支撑 claim 或可复现命令证明的问题。"
$prompt | claude -p --bare --permission-mode plan --output-format json --disallowedTools Edit Write
```

`ultrareview` 可以作为额外审查，但不能替代审核证据包和最终决定文件。

## 通过条件

审核包只有同时满足下面条件时，才能通过：

```text
ai_cross_review_status: pass
owner_participation: not_required
rounds_completed: 3
claude_code_read_only: true
codex_fixes_or_rebuttals_recorded: true
machine_gates_passed: true
unresolved_blocking_issues: 0
```

只要仍有 blocking issue，最终决定必须写成：

```text
ai_cross_review_status: blocked
```

blocked 的改动不能进入正式 Runner、keep/best 决策、confirmation、promotion、baseline claim 或论文 claim。

## 校验命令

信任审核包前必须运行：

```powershell
python workflow\gtpj_workflow.py validate-ai-cross-review --path docs\agent_reviews\YYYY-MM-DD-task-name
```

这个 helper 检查结构、最终字段、每轮 Claude verdict 是否全部为 `pass`。它不判断 Claude 是否一定正确；它只保证审核循环完整、可追踪、且没有被最终决定文件伪装成通过。

## 自动运行命令

需要自动生成证据包、运行机器验证、调用 Claude Code 三轮只读审核并写回结果时，使用：

```powershell
python workflow\gtpj_workflow.py run-ai-cross-review --slug task-name --task-title "任务标题"
```

默认会写入：

```text
docs/agent_reviews/YYYY-MM-DD-task-name/
```

默认会运行不启动训练的 workflow 机器验证：

```text
python workflow\gtpj_workflow.py validate
python workflow\gtpj_workflow.py validate-workflow-consistency
python workflow\gtpj_workflow.py audit-boundary
python -m py_compile workflow\gtpj_workflow.py
```

如需加入额外验证命令，可重复传入：

```powershell
--validation-command "python -m pytest tests\test_gtpj_workflow.py -q -p no:cacheprovider"
```

如果只想生成证据包但不调用真实 Claude Code，可传入 `--skip-claude`；这种情况下最终状态必须是 blocked，不能当作正式通过。

## 快速审核优化

默认 Claude Code 审核不再直接读取完整 diff。`run-ai-cross-review` 必须同时生成：

```text
02_diff.patch
02_focused_diff.md
02_review_brief.md
```

字段规则：

```text
prompt_profile: focused | full
review_mode: blocking-only | full
```

默认值：

```text
prompt_profile: focused
review_mode: blocking-only
```

`focused` 模式下，Claude Code 默认只读 `CLAUDE.md`、`docs/workflow/CLAUDE_CONTEXT.md`、`02_review_brief.md`、`02_focused_diff.md`、`03_validation.md` 和 `04_claims.md`。完整 `02_diff.patch` 仍然必须保留在证据包中，但只作为追查备用证据。

`blocking-only` 模式下，Claude Code 只报告会导致行为错误、证据污染、验证失败、正式实验结论不可靠的 blocking issues。非阻断命名、风格和微小测试粒度建议不要展开。

需要完整旧模式时，显式使用：

```powershell
python workflow\gtpj_workflow.py run-ai-cross-review --slug task-name --prompt-profile full --review-mode full
```
