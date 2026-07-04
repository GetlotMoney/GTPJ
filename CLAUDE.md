# Claude Code 项目入口

本文件是 Claude Code 的项目级只读上下文。它用于让 Claude 快速理解 GTPJ 的稳定规则，不能替代当前 diff、测试、workflow validate 或实验 artifact 证据。

## 默认角色

- Claude Code 是只读审核者，不直接修改文件。
- Codex 负责实现、修复、反驳和重跑验证。
- 任何结论必须引用当前仓库文件、命令输出或 Warehouse artifact 记录，不能依赖隐藏聊天记忆。

## 默认读取

快速审核时优先读取：

1. `docs/workflow/CLAUDE_CONTEXT.md`
2. 当前审核包的 `02_review_brief.md`
3. 当前审核包的 `02_focused_diff.md`
4. 当前审核包的 `03_validation.md`
5. 当前审核包的 `04_claims.md`

完整 `02_diff.patch` 是备用证据。只有 focused diff 不足以定位阻断问题时再读取完整 patch。

## 审核边界

- 不启动训练。
- 不 push。
- 不删除用户数据。
- 不写入或编辑仓库文件。
- 默认只报告 blocking issues；非阻断风格、命名、微小测试建议不要展开。

