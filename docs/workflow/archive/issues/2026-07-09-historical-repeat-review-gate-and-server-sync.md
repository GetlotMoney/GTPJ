# 2026-07-09 历史复现实验审核门与服务器同步问题

## ISSUE-20260709-015: DR-095 历史 exact repeat 复现前仍有审核门和服务器漂移

### 状态

open / blocking

### 症状

- 本地决策仓库已整理到干净 checkpoint：`codex/attempt017-server-frozen-escape100`，`8890cf0312131446871b9e9deccf8b78c4c3c7ed`。
- 本地机器验证已经通过：`tests/test_gtpj_workflow.py`、`validate`、`validate-workflow-consistency`、`audit-boundary`、`git diff --check`。
- 最新严格审核包 `docs/agent_reviews/2026-07-09-2026-07-09-historical-repeat-source-control-gate` 仍是 blocked 包，因为创建时使用了 `--skip-claude`；`validate-ai-cross-review` 正确失败。
- Claude Code CLI 存在，但 `~/.claude/settings.json` 指向 `http://127.0.0.1:15721`，该端口当前未监听；当前进程、用户级、机器级环境中没有可见的 `ANTHROPIC_API_KEY` / `DEEPSEEK_API_KEY`。
- 服务器 `/data/lby/projects/cv_project/GTPJ` 仍在旧分支 `codex/h76-campaign-20260704`，HEAD 为 `d505e992492eb6fe7272edf0f0dc1d15a5932434`，并有 tracked 修改和 untracked runtime 文件。
- GPU 0/1 当前空闲，但不能因为 GPU 空闲就绕过 formal gate 直接跑复现。

### 影响范围

- DR-095 的 `H=75.11` 仍只能算搜索/调参单次结果，不能算 restore confirmation evidence。
- 任何“20 轮复现”在 strict-3 审核和服务器源代码同步完成前都不能标记为 formal evidence。
- 如果直接在服务器旧脏工作树上跑，会重新引入“代码到底是不是同一份”的账单问题。

### 根因

- 先前历史复现路径存在“用旧训练 commit 跑、但用新工作树配置生成”的风险；当前 helper 已在本地 checkpoint 中修复为从目标训练 commit 读取 base config，并要求显式 `--allow-historical-training-commit`。
- Claude Code 审核依赖外部网关或 API key，但当前本机配置指向不可用的本地代理；该依赖没有被 formal run preflight 提前拦截。
- 本地决策仓库与服务器运行副本是两个独立 checkout，服务器不会自动继承本地 commit、branch、review pack 或干净状态。

### 修复方案

1. 恢复真实 Claude Code strict-3 审核能力：启动或修复 `127.0.0.1:15721` 对应代理，或在受控会话中配置有效的 Anthropic-compatible API key 和 base URL。不得从历史日志、备份或聊天记录中抽取旧密钥。
2. 重新运行最新变更的 `run-ai-cross-review`，不能使用 `--skip-claude`；随后 `validate-ai-cross-review --path docs/agent_reviews/2026-07-09-2026-07-09-historical-repeat-source-control-gate` 必须通过。
3. 将服务器同步到本地干净 checkpoint 或其后续记录 commit，并清理或隔离服务器旧 runtime 脏文件；启动前必须确认服务器 `git rev-parse HEAD` 与 formal plan 的 `commit` 一致。
4. 对 DR-095 做历史 exact repeat 时，必须显式记录训练源分支、训练 commit、当前 workflow commit 和 base config commit 读取来源。
5. 用户要求 20 轮复现时，若单候选 max attempts 仍为 5，必须在 plan 中明确 20 轮的组成方式，例如 4 个候选各 5 次，不能把同一候选私自扩展到 20 次冒充规则内 confirmation。

### 预防规则

- formal runner preflight 应检查 Claude Code 审核 gate 是否是真实 pass，而不是只存在 review pack。
- formal runner preflight 应检查服务器 tracked worktree 是否干净，并把允许的 runtime-only untracked 项列成白名单。
- 历史复现 plan 中必须同时记录 `workflow_commit`、`training_commit`、`source_branch` 和 `base_config_source`。
- 发现同类外部 Claude gate 问题再次出现时，优先沉淀为 helper 级 doctor/check，而不是只靠人工记忆。
