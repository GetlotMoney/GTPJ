ai_cross_review_status: pass
decision_scope: previous_directory_binding_candidate_28185a0_only
owner_participation: not_required
review_tier: strict-3
rounds_completed: 3
claude_rounds_required: 3
claude_rounds_completed: 0
claude_code_read_only: false
independent_codex_fallback_read_only: true
codex_named_thread_pre_review: pass
codex_named_thread_lifecycle: completed_archived
codex_fixes_or_rebuttals_recorded: true
machine_gates_passed: true
unresolved_blocking_issues: 0
accepted_by: machine_gates_plus_ai_cross_review
blocked_reason:

# 最终决定

`V5-ABLATION-001` 的运行目录修复候选 `28185a0f1f1c2bdc9b6239cbbc919165a84077df` 可以进入运行前冻结。三路独立只读 Codex 后备审核均为 `pass`；本地 342 项全仓测试中 337 项通过、5 项 Linux 专属用例在 Windows 按设计跳过，服务器 45 项控制器测试与 5 项 Linux 真实测试共 50 项全部通过。真实 bundle 的 13 项引用、命名实验分支、实验起点和工作流门均通过，没有遗留阻断。

本轮关闭了两个根因：FULL 不再偷跑旧母版入口，两个代码副本也不再创建会被误判或换向的 `data`/`train_log` 链接。两组都使用候选运行入口，数据和结果根目录由 Linux 目录文件描述符固定，FULL 的科学代码仍与冻结母版等价。

这个历史决定只放行当时尚未领取的 R3 六个正式 RUN，不覆盖后续类别编号修复与 R4。R3 后来已在模型初始化阶段失败并停用；当前 R4 必须完成本轮新审核与新冻结后才能启动，也不等于已经得到局部分支的精度结论。
