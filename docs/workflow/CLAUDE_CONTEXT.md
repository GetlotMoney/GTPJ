# Claude Code 共享项目上下文

## 当前审核分层

- 机器验证永远优先于模型意见。
- `fast` 不调用 Claude Code，但必须有机器验证通过和命名 Codex 线程预审通过。
- `review-1` 只需要 1 轮 Claude Code，用于普通 workflow/helper/template 修补。
- `strict-3` 才需要 3 轮 Claude Code，只用于会污染正式实验结论、promotion、baseline 或论文 claim 的改动。
- Claude Code 前必须读取 `02_codex_named_thread_pre_review.md`，确认命名 Codex 线程已 `completed_archived`。
- Claude Code 若连接拒绝、超时或空输出，该调用不算审核轮次；可以由相同数量的独立只读 Codex Reviewer 备用，但必须明确标注 fallback，不得冒充 Claude。

本文件是 GTPJ 给 Claude Code 的轻量共享上下文。它只记录稳定规则，当前事实仍以本次审核包、仓库文件、验证命令和实验 artifact 为准。

## 项目目标

GTPJ 是面向 GZSL（广义零样本学习）实验的研究 workflow。GitHub 仓库只保存轻量治理、配置、结果账本和证据索引；原始日志、checkpoint、生成图和大文件留在 Warehouse 或 Research 目录。

## 核心硬规则

- 机器验证优先于模型意见。
- Claude Code 只读审核，Codex 负责实现和修复。
- 正式实验不能绕过 `agent_runtime.yaml`、`validate-agent-runtime`、`multi-agent-preflight` 和 cleanup 记录。
- raw artifacts 不能进入 GitHub；GitHub 只记录 artifact id、URI、sha256、size、config、manifest、result 和 quality。
- exact repeat 必须固定原始 seed；正式复现必须写 `repeat_type: exact_repeat`、`original_seed`、`max_attempts: 5`、`max_attempts_hard_cap: true`、`early_stop_on_best_hit: true`、`restore_target_H`、`near_miss_tolerance_H`、`near_miss_not_restored`。同一候选无论是否还原成功都最多 5 次；多 seed / `seed_sweep` / `multi_seed_stability` 必须写 `not_confirmation_evidence: true`，不算 exact repeat。
- `best_observed_H` 表示历史最高观察值；`confirmed_H` 表示确认复现实验的确认值，二者不能混用。
- promotion 必须有完整 result、quality、artifact、confirmation 和 promotion evidence；普通调参或未确认结果不能自动升版本。

## Claude 快速审核策略

默认使用 focused 审核：

- 先读 `CLAUDE.md` 和本文件。
- 再读审核包中的 `02_review_brief.md`、`02_focused_diff.md`、`03_validation.md`、`04_claims.md`。
- 只在 focused diff 不足以定位阻断问题时读取完整 `02_diff.patch`。

默认使用 blocking-only 审核：

- 只报告会导致行为错误、证据污染、验证失败、正式实验结论不可靠的问题。
- 命名、风格、非关键测试粒度建议可以省略，除非它会隐藏真实行为风险。

## 常见阻断问题

- 训练入口、评估语义、label mapping、seen/unseen split、class order、logits shape 或 U/S/H/ZS 指标语义不清。
- helper 生成的正式 evidence 与实际 run、attempt、artifact 或 warehouse 路由不一致。
- `agent_runtime.yaml` 中 agent id、UI 显示名、role 映射、output refs 或 cleanup 记录缺失。
- 将 debug/smoke 或 seed sweep 伪装成正式 confirmation。
- 用当前主会话或隐藏记忆冒充真实 `real_multi_agent` 证据。
