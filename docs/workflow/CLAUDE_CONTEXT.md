# Claude Code 共享项目上下文

## 当前审核规则

- 机器验证永远优先于模型意见。
- 任何代码修改固定由两个不同的只读子 Agent 依次做两轮对抗式审核。
- 第 1 轮查实现、接口、shape、梯度、数据与评估边界；修复、重测并复核通过后，第 2 轮查反例、隐藏耦合、回归和测试盲区。
- 两轮必须绑定同一个最终 `reviewed_code_id`，均为 `pass` 且未解决阻断为 0。
- Claude Code 只有在被明确选为某一轮子 Agent Reviewer 时才参与；连接失败或空输出不算完成该轮，也不能冒充另一个 Reviewer。

本文件是 GTPJ 给 Claude Code 的轻量共享上下文。它只记录稳定规则，当前事实仍以任务说明、仓库文件、代码 diff、验证命令和实验 artifact 为准。

## 项目目标

GTPJ 是面向 GZSL（广义零样本学习）实验的研究 workflow。GitHub 仓库只保存轻量治理、配置、结果账本和证据索引；原始日志、checkpoint、生成图和大文件留在 Warehouse 或 Research 目录。

## 核心硬规则

- 机器验证优先于模型意见。
- Claude Code 只读审核，Codex 负责实现和修复。
- 正式实验默认不把 `agent_runtime.yaml`、`validate-agent-runtime`、`multi-agent-preflight` 或 cleanup 记录当作开跑硬门；这些机制仅在 owner 明确要求多智能体实时监控或真实并行隔离风险时按需启用。
- raw artifacts 不能进入 GitHub；GitHub 只记录 artifact id、URI、sha256、size、config、manifest、result 和 quality。
- exact repeat 必须固定原始 seed；正式复现必须写 `repeat_type: exact_repeat`、`original_seed`、`max_attempts: 5`、`max_attempts_hard_cap: true`、`early_stop_on_best_hit: true`、`restore_target_H`、`near_miss_tolerance_H`、`near_miss_not_restored`。同一候选无论是否还原成功都最多 5 次；多 seed / `seed_sweep` / `multi_seed_stability` 必须写 `not_confirmation_evidence: true`，不算 exact repeat。
- `best_observed_H` 表示历史最高观察值；`confirmed_H` 表示确认复现实验的确认值，二者不能混用。
- promotion 必须有完整 result、quality、artifact、confirmation 和 promotion evidence；普通调参或未确认结果不能自动升版本。

## Claude 快速审核策略

- 先读 `CLAUDE.md`、本文件、`docs/workflow/protocols/ai_cross_review_protocol.md` 和本轮任务说明。
- 阅读完整审核范围、代码 diff 和机器测试结果。
- 第 2 轮另读第 1 轮结论、修复说明，并确认 `reviewed_code_id` 未变。

默认使用 blocking-only 审核：

- 只报告会导致行为错误、证据污染、验证失败、正式实验结论不可靠的问题。
- 命名、风格、非关键测试粒度建议可以省略，除非它会隐藏真实行为风险。

## 常见阻断问题

- 训练入口、评估语义、label mapping、seen/unseen split、class order、logits shape 或 U/S/H/ZS 指标语义不清。
- helper 生成的正式 evidence 与实际 run、attempt、artifact 或 warehouse 路由不一致。
- 仅在 owner 明确要求多智能体协作时：`agent_runtime.yaml` 中 agent id、UI 显示名、role 映射、output refs 或 cleanup 记录缺失。
- 将 debug/smoke 或 seed sweep 伪装成正式 confirmation。
- 用当前主会话或隐藏记忆冒充独立的只读子 Agent 审核轮次。
