# Focused Diff

本文件是给 Claude Code 默认读取的精简 diff。完整证据仍保留在 `02_diff.patch`。

## Changed Files

- AGENTS.md
- docs/workflow/CLAUDE_CONTEXT.md
- docs/workflow/README.md
- docs/workflow/START_HERE.md
- docs/workflow/WORKFLOW_KERNEL.md
- docs/workflow/agents/README.md
- docs/workflow/agents/by_experiment/ablation/agents/README.md
- docs/workflow/agents/by_experiment/confirmation/agents/README.md
- docs/workflow/agents/by_experiment/innovation/agents/README.md
- docs/workflow/agents/by_experiment/promotion/agents/README.md
- docs/workflow/agents/by_experiment/tune/agents/README.md
- docs/workflow/agents/long_term_memory.md
- docs/workflow/core/AGENT_RUNTIME_HARD_GATE.md
- docs/workflow/core/CHANGELOG.md
- docs/workflow/core/QUICK_START.md
- docs/workflow/core/TASK_START_CARD.md
- docs/workflow/core/TASK_START_MINI.md
- docs/workflow/core/WORKFLOW_ROUTER.md
- docs/workflow/core/WORKFLOW_VERSION.md
- docs/workflow/playbooks/ablation.md
- docs/workflow/playbooks/confirmation.md
- docs/workflow/playbooks/innovation.md
- docs/workflow/playbooks/mixed_campaign.md
- docs/workflow/playbooks/paper_to_experiment.md
- docs/workflow/playbooks/tune.md
- docs/workflow/protocols/agent_cleanup_protocol.md
- docs/workflow/protocols/agent_orchestration.md
- docs/workflow/protocols/agent_report_policy.md
- docs/workflow/protocols/ai_cross_review_protocol.md
- docs/workflow/protocols/autonomous_research_campaign.md
- docs/workflow/protocols/experiment_protocol.md
- docs/workflow/protocols/innovation_code_review_protocol.md
- docs/workflow/protocols/mixed_experiment_campaign_protocol.md
- docs/workflow/protocols/module_template_selection.md
- docs/workflow/protocols/module_trial_protocol.md
- docs/workflow/protocols/promotion.md
- experiments/README.md
- experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/ATTEMPTS.md
- experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/README.md
- experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/agent_summary.md
- experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/manifest.yaml
- experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/quality_check.md
- experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/result.md
- experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/result.yaml
- experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/review_round_2.md
- experiments/module_trials/INDEX.md
- experiments/templates/TRIAL_ATTEMPTS_template.md
- experiments/templates/TRIAL_README_template.md
- experiments/templates/VERSION_template.md
- experiments/templates/agent_summary_template.md
- experiments/templates/ai_cross_review_template.md
- experiments/templates/implementation_template.md
- experiments/templates/modules/README.md
- experiments/templates/modules/architecture_change_template.md
- experiments/templates/modules/auxiliary_loss_template.py
- experiments/templates/modules/composite_module_template.py
- experiments/templates/modules/feature_adapter_template.py
- experiments/templates/modules/fusion_gate_template.py
- experiments/templates/modules/module_source_template.md
- experiments/templates/modules/standard_gzsl_module_framework_template.py
- experiments/templates/modules/standard_gzsl_training_template.py
- experiments/templates/modules/standard_trial_config_template.yaml
- experiments/templates/quality_check_template.md
- experiments/templates/run_receipt_template.yaml
- idea_tree/idea_tree.json
- tests/test_gtpj_workflow.py
- workflow/gtpj_workflow.py
- docs/workflow/reference/GENERAL_GZSL_EXPERIMENT_PROTOCOL.md
- experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/attempts/ATTEMPT-010/
- experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/attempts/ATTEMPT-011/
- experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/attempts/ATTEMPT-012/
- experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/attempts/ATTEMPT-013/
- experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/attempts/ATTEMPT-014/
- experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/attempts/ATTEMPT-015/
- experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/attempts/ATTEMPT-016/
- experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/attempts/ATTEMPT-017/
- scripts/

## Diff Stat

```text
 AGENTS.md                                          |   52 +-
 docs/workflow/CLAUDE_CONTEXT.md                    |    6 +-
 docs/workflow/README.md                            |   13 +-
 docs/workflow/START_HERE.md                        |  142 +-
 docs/workflow/WORKFLOW_KERNEL.md                   |  165 +-
 docs/workflow/agents/README.md                     |    2 +-
 .../agents/by_experiment/ablation/agents/README.md |    2 +-
 .../by_experiment/confirmation/agents/README.md    |    4 +-
 .../by_experiment/innovation/agents/README.md      |    4 +-
 .../by_experiment/promotion/agents/README.md       |    2 +-
 .../agents/by_experiment/tune/agents/README.md     |    4 +-
 docs/workflow/agents/long_term_memory.md           |   14 +-
 docs/workflow/core/AGENT_RUNTIME_HARD_GATE.md      |  210 +-
 docs/workflow/core/CHANGELOG.md                    |   14 +-
 docs/workflow/core/QUICK_START.md                  |   27 +-
 docs/workflow/core/TASK_START_CARD.md              |   67 +-
 docs/workflow/core/TASK_START_MINI.md              |   31 +-
 docs/workflow/core/WORKFLOW_ROUTER.md              |   26 +-
 docs/workflow/core/WORKFLOW_VERSION.md             |    6 +-
 docs/workflow/playbooks/ablation.md                |    7 +-
 docs/workflow/playbooks/confirmation.md            |   39 +-
 docs/workflow/playbooks/innovation.md              |   11 +-
 docs/workflow/playbooks/mixed_campaign.md          |   20 +-
 docs/workflow/playbooks/paper_to_experiment.md     |    4 +-
 docs/workflow/playbooks/tune.md                    |    8 +-
 docs/workflow/protocols/agent_cleanup_protocol.md  |  102 +-
 docs/workflow/protocols/agent_orchestration.md     |  119 +-
 docs/workflow/protocols/agent_report_policy.md     |   41 +-
 .../workflow/protocols/ai_cross_review_protocol.md |   42 +-
 .../protocols/autonomous_research_campaign.md      |   27 +-
 docs/workflow/protocols/experiment_protocol.md     |   50 +-
 .../protocols/innovation_code_review_protocol.md   |   16 +-
 .../mixed_experiment_campaign_protocol.md          |   31 +-
 .../protocols/module_template_selection.md         |   22 +-
 docs/workflow/protocols/module_trial_protocol.md   |   36 +-
 docs/workflow/protocols/promotion.md               |   26 +-
 experiments/README.md                              |   15 +
 .../TRIAL-001_dynamic-routing/ATTEMPTS.md          |   50 +
 .../TRIAL-001_dynamic-routing/README.md            |   10 +-
 .../TRIAL-001_dynamic-routing/agent_summary.md     |   68 +-
 .../TRIAL-001_dynamic-routing/manifest.yaml        |   48 +-
 .../TRIAL-001_dynamic-routing/quality_check.md     |   14 +-
 .../TRIAL-001_dynamic-routing/result.md            |   20 +-
 .../TRIAL-001_dynamic-routing/result.yaml          |   36 +-
 .../TRIAL-001_dynamic-routing/review_round_2.md    |   24 +-
 experiments/module_trials/INDEX.md                 |    2 +-
 experiments/templates/TRIAL_ATTEMPTS_template.md   |   29 +-
 experiments/templates/TRIAL_README_template.md     |   45 +-
 experiments/templates/VERSION_template.md          |   14 +-
 experiments/templates/agent_summary_template.md    |   69 +-
 experiments/templates/ai_cross_review_template.md  |   50 +-
 experiments/templates/implementation_template.md   |   58 +-
 experiments/templates/modules/README.md            |   30 +-
 .../modules/architecture_change_template.md        |   17 +-
 .../templates/modules/auxiliary_loss_template.py   |    8 +-
 .../templates/modules/composite_module_template.py |   44 +-
 .../templates/modules/feature_adapter_template.py  |   13 +-
 .../templates/modules/fusion_gate_template.py      |    8 +-
 .../templates/modules/module_source_template.md    |   16 +-
 .../standard_gzsl_module_framework_template.py     |   29 +-
 .../modules/standard_gzsl_training_template.py     |   34 +-
 .../modules/standard_trial_config_template.yaml    |    8 +-
 experiments/templates/quality_check_template.md    |   16 +-
 experiments/templates/run_receipt_template.yaml    |   12 +-
 idea_tree/idea_tree.json                           |    2 +-
 tests/test_gtpj_workflow.py                        | 1277 ++++++++-
 workflow/gtpj_workflow.py                          | 2884 ++++++++++++++++++--
 67 files changed, 5276 insertions(+), 1066 deletions(-)
```

## Focused Patch

```diff
diff --git a/AGENTS.md b/AGENTS.md
index b8d28d4..54672c3 100644
--- a/AGENTS.md
+++ b/AGENTS.md
@@ -20,62 +20,81 @@
 - 回答 owner 不知道什么意思的问题时，从第一性原理出发解释。
 - 动手前先阅读相关文件和已有约定。
 - 修改范围尽量小，不做与任务无关的重构。
 - 遇到 owner 已经修改过的文件，先理解现状再继续。
 - 发现需求含糊时，先提出最关键的问题。
 - 能直接验证的结果，优先用命令或测试验证。
 - 交付时说明改了什么、验证了什么；测试不能跑时说明原因。
 - 标出仍然存在的风险和下一步建议。
 
 ## 沟通
 
 - 与 owner 协作时默认使用中文。
-- 新增或修改项目文档、workflow 文档、模板说明和审核报告时，正文必须使用中文；命令、字段名、文件名、代码标识和必要英文接口名可以保留原文。
+- 新增或修改项目文档、workflow 文档、模板说明和审核报告时，正文必须使用中文；不允许整段英文说明。
+- 英文只允许作为必要名词或机器标识保留，例如论文标题、方法名、角色名、命令、字段名、文件名、代码标识、指标名、URL 和 helper 依赖的结构 marker。
+- 如果标题必须保留英文 marker，例如 `Framework Diagram`、`Trial Flow`、`Code Flow Diagram`，同一节必须用中文解释它的含义和填写规则。
 - 先说结论，再说关键原因。
 - 复杂任务在编辑前先给简短计划。
 - 直接说明不确定性和风险。
 - 交付流程图、框架图、代码路径图或实验链路图时，默认额外生成一个可本地打开的 HTML 文件，并在回复中用 `file:///D:/.../xxx.html` 的绝对本地链接给 owner。Markdown/Mermaid 可以作为仓库权威记录，但不能替代 owner 可直接打开的 HTML 视图。
 
 ## AI 审核规范
 
 - 重要代码修改、workflow/helper/template 修改、训练入口、评估语义、实验结论、promotion 或论文 claim 相关决策，默认不要求 owner 参与日常审核，但必须按 `review_tier` 分层执行 AI 交叉审核。
 - 机器验证永远优先且永远必跑；AI 审核不能替代测试、workflow validate、audit-boundary、schema 或 helper gate。
 - Codex 负责实现、修复、反驳和重跑验证；Claude Code 只读审查，不直接改文件、不启动训练、不执行 push/delete/发布。
-- `fast`：0 轮 Claude Code，只允许低风险轻量文档或 workflow 修补；仍必须有机器验证和临时 Codex agent 预审。
+- `fast`：0 轮 Claude Code，只允许低风险轻量文档或 workflow 修补；仍必须有机器验证和命名 Codex 线程预审。
 - `review-1`：1 轮 Claude Code，用于普通 workflow/helper/template 修补，不直接污染正式实验结论。
 - `strict-3`：3 轮 Claude Code，只用于训练入口、评估语义、正式实验结论、promotion、baseline 或论文 claim 等会污染正式结论的改动。
-- Claude Code 前必须先开临时 Codex agent 做只读预审；预审完成后立刻关闭，并在 evidence pack 记录真实 `agent_instance_id`、UI 显示名和结构化 `close_result`。
+- Claude Code 前必须先创建或绑定命名 Codex 线程做只读预审；预审完成后立刻归档，并在 evidence pack 记录真实 `thread_id`、UI 显示名和结构化 `archive_result`。
+- 代码审核不被 `server_frozen_runner` 豁免。`server_frozen_runner` 只表示训练运行期不创建命名线程；一旦修改代码、workflow、helper 或模板，仍必须先切专用代码审核分支，完成命名 Codex 线程预审、Claude Code 只读审核和 `validate-ai-cross-review`。
 - AI 交叉审核必须留下中文 evidence pack，并通过 `python workflow\gtpj_workflow.py validate-ai-cross-review --path <review_pack>` 后，才能进入正式 Runner、keep/best、confirmation、promotion、baseline 或 paper claim。
 - push、删除、远端发布、破坏性迁移、密钥处理或用户数据操作仍然必须等待 owner 明确授权。
 
+## 流程设计原则
+
+- 每次新增或修改 workflow 规范、状态机、helper、模板、playbook、protocol 或 agents 调度规则时，必须先从第一性原理出发说明：它要解决的最小真实问题是什么，现有流程为什么不够，最小闭环是什么。
+- 默认选择最简单可验证实现：能用一个字段解决的，不新增一个文件；能用一个 helper 子命令解决的，不新增一套协议；能复用现有状态机和证据链的，不另建平行流程。
+- 瘦身优先：新增或修改规范、流程、文档、模板、helper 或 agent 调度规则时，默认写最短可读版本；能合并到现有入口就不新建文件，能删旧冗余就先删冗余，能用一条规则表达就不拆成多层流程。
+- 新流程必须服务于闭环，不服务于形式。至少要说明输入、输出、责任角色、状态变化、验证命令、失败退出条件和回滚方式；说不清这些，就先停在建议，不写入正式规范。
+- 不为“看起来完整”而增加文档层级。新增文档必须满足至少一项：能被机器校验、能驱动状态机、是正式 evidence 必需模板、是 owner/agent 的权威入口。
+- 每个实验类型可以有不同规范，但必须通过统一 router 和统一状态机进入；差异放在 playbook/profile/config 中，不要复制出互相污染的独立流程。
+- 任何自动化都先做最小可用闭环，再逐步加能力。优先顺序是：可读状态 -> 可验证 gate -> 可回滚执行 -> 可审计证据 -> 自动优化；不要一开始就堆复杂调度。
+- 新规范写入前要给 owner 一个短摘要：为什么需要、最小实现是什么、会改哪些文件、哪些复杂设计被刻意不做。
+
 ## 最简 GTPJ 工作流
 
 1. 先查状态：确认分支、HEAD、dirty 文件、远端/服务器是否需要同步；只读问题先只读回答。
 2. 再定任务：按 `START_HERE.md` 判断是查状态、读论文、创新、调参、消融、复现、promotion 还是混合 campaign。
 3. 明确基线：所有实验必须写清 `base_version` / `base_code_tag`；论文到实验必须先有 owner 指定的代码版本。
 4. 选模板：新创新优先用模块模板热插拔；owner 明确要求“新模板重建”时，使用 `standard_gzsl_training_template.py` 生成 trial-local 训练入口，不继续堆旧训练脚本。
-5. 先写计划：正式写入或训练前生成 mini 启动摘要；需要正式证据时再展开完整 task card。
-6. 走状态机：正式证据对象必须绑定 `subject_id` / `subject_type`；`TRANSITIONS.jsonl` 是 append-only 权威历史，`evidence_routing.yaml` 只能由 chain head 派生，不能手写抬高状态。
-7. 正式 Runner 前开真实临时 agents：写 `agent_runtime.yaml`，记录真实 agent id、UI 显示名、role 映射、output refs，并依次跑 `validate-agent-runtime`、`multi-agent-preflight`、`agent-cleanup-plan`。
-8. 严格命名 agents：右侧临时 agent 显示名必须按 `<subject_id> | <Role Label>`，例如 `ATTEMPT-007 | Runner Monitor`；禁止使用 Herschel、Galileo、Feynman 等随机英文昵称。
-9. 跑实验：Runner 串行锁 GPU；GitHub 只记轻量账本；raw logs、checkpoint、generated figures 和 cache 进 Warehouse/Research，不进 GitHub。
-10. 收结果：写 `manifest.yaml`、`result.yaml`、`result.md`、`quality_check.md`、`agent_summary.md`、`AGENT_ACTIVITY.md`；必须报告 mean/min/max/range，不能只报 best。
-11. 做审核：普通 workflow 修补走 `review-1`，正式结论污染风险走 `strict-3`；所有机器验证照跑。
-12. 收尾清理：每阶段报告 `keep / close / unknown agents`，关闭 completed agents，记录 `close_result`，右侧栏只保留当前 active agents。
+5. 记录框架：只有产生或改变方法框架的代码模块变动才要求框架记录；调参、复现、只关闭既有模块的窄消融不新增框架，只记录结果证据。凡是新增/改写 module、forward、loss、eval、data view 或接口语义的代码变动，都归入创新 / module trial，必须有 `module_source.md`、`implementation.md`、`framework_diagram.md`，必要时还要有 `Code Flow Diagram`。
+6. 先写计划：正式写入或训练前生成 mini 启动摘要；需要正式证据时再展开完整 task card。
+7. 走状态机：正式证据对象必须绑定 `subject_id` / `subject_type`；`TRANSITIONS.jsonl` 是 append-only 权威历史，`evidence_routing.yaml` 只能由 chain head 派生，不能手写抬高状态。
+8. 先选运行等级：`debug_smoke` 只能测试代码、服务器、GPU 和 helper 链路，必须写 `activation_mode: role_only`、`formal_evidence: false`、`real_agent_instances_started_by_helper: false`；`formal` 进入正式证据时允许两条路径：`real_multi_agent`，或 `server_detached_role_only`。两者都必须写 `formal_evidence: true`、`agent_runtime_gate_satisfied: true`。
+8a. 只要本轮会改代码、workflow、helper、模板或训练配置生成逻辑，必须在修改前切到专用代码审核分支；在旧脏分支上补切只能算草稿隔离，不能作为正式 freeze / Runner 启动依据。
+9. 正式 Runner 前先写 `agent_runtime.yaml` 并依次跑 `validate-agent-runtime`、`multi-agent-preflight`、`agent-cleanup-plan`。如果是 `real_multi_agent`，必须记录真实 thread id、UI 显示名、role 映射和 output refs；如果是 `server_detached_role_only`，必须记录独立 sequential role outputs、server_detached preflight 和 `thread_creation_allowed: false`。
+10. 创建命名线程前先检查左侧栏：如果 owner 报告左侧栏仍有历史 agents，或者当前工具不能确认左侧栏干净，禁止继续启动新的命名线程；本轮 `real_multi_agent` 阻断。此时可以改走 `server_detached_role_only` formal，或降级为不进证据的 `debug_smoke`。
+10a. owner 说“开启多agents智能体工作流”“多agents智能体工作流，开始”“跑N轮”或“做N轮实验”时，视为明确选择 `live_multi_agent_monitor` 并授权执行；不要反复确认 workflow 模式或启动意图。只有模式冲突、侧边栏干净状态缺失且无法验证、硬门失败或安全边界动作，才允许再问一次。
+11. 严格命名 agents：左侧命名 Codex 线程显示名必须按 `<subject_id> | <Role Label>`，例如 `ATTEMPT-007 | Runner Monitor`；禁止使用 Herschel、Galileo、Feynman 等随机英文昵称。
+12. 跑实验：Runner 串行锁 GPU；GitHub 只记轻量账本；raw logs、checkpoint、generated figures 和 cache 进 Warehouse/Research，不进 GitHub。
+13. 收结果：`live_multi_agent_monitor` 运行中必须持续汇报每个新增 completed job，使用 `monitor-workflow --report-new-completions --activity-log <attempt_dir>\AGENT_ACTIVITY.md` 或等价证据写入；每条至少记录 `job_id`、H/U/S/ZS、当前 best、H>=75/H>=76、证据位置和下一步。closeout 时写 `manifest.yaml`、`result.yaml`、`result.md`、`quality_check.md`、`agent_summary.md`、`AGENT_ACTIVITY.md`；复现必须是 `repeat_type: exact_repeat`，锁定 `original_seed`、原始 config、代码 commit、数据/缓存、训练日程和评估口径，不允许换 seed 或换任何参数；默认 `max_attempts: 5`、`max_attempts_hard_cap: true`、`early_stop_on_best_hit: true`。必须声明 `restore_target_H`；`near_miss_tolerance_H` 只能用于记录“接近但未还原”。复现结果必须分成 `best_hit`、`near_miss_not_restored` 和 `stable_confirm`：`best_hit` 只看任一 clean repeat 是否真正达到原水平，回答“有没有还原”；`near_miss_not_restored` 只能说明实验有效果、还有希望，不能停止、不能 confirmation；`stable_confirm` 才看 mean/min/max/range，回答“能不能作为稳定 confirmed / promotion / baseline 证据”。`seed_sweep` / `score_search` / `multi_seed_stability` 必须写 `not_confirmation_evidence: true`，不能冒充复现。
+14. 做审核：普通 workflow 修补走 `review-1`，正式结论污染风险走 `strict-3`；所有机器验证照跑。
+15. 收尾清理：Runner 仍有 running/pending job 时，当前阶段 active 左侧命名线程必须保持可见；只有 closeout/handoff 完成、输出已入账后，才报告 `keep / archive / unknown agents`，归档 completed threads，记录 `archive_result`，左侧栏只保留当前 active agents。
 
 ## 仓库规则
 
 - `main` 是唯一长期分支。
 - `v1`、`v2`、`v3`、`v4`、`v5` 是永久版本 tags；当前正式确定版本以 `README.md`、`docs/PROJECT_STATUS.md` 和 `experiments/VERSION_TREE.md` 为准。`v4` 是历史 config-only tag，不作为以后“只调参也能开新 vX”的模板。
-- min3 复现实验中，同一候选至少 3 次 clean completed/ok 且有 H 指标时，即可按 `docs/workflow/protocols/promotion.md` 自动 promotion；多个 min3-confirmed 候选同时存在时，按 `confirmed_H` 最高者确定为正式版本，`best_observed_H` 只作平局辅助。promotion 表示确定正式版本/tag，不等于自动执行 `activate-version` 或切换 active runtime alias。
+- 复现实验必须先记录 `best_hit`：只有任意 clean completed/ok exact repeat 的单次 H 达到 `restore_target_H`，才标记为还原命中，并更新 `best_observed_H` / `best_single_H`；命中后必须停止后续 pending repeat。`max_attempts: 5` 是 `max_attempts_hard_cap`：不管有没有还原成功，同一候选最多跑 5 次；5 次仍未达到 `restore_target_H` 就收口为 not restored / near miss 状态，不能继续加跑。落在 `near_miss_tolerance_H` 内但没达到 `restore_target_H`，只能写 `near_miss_not_restored`，表示实验有效果、还有希望，不能写成复现通过，不能停止后续 repeat。`stable_confirm` 是另一层：只有质量门另行要求多 run 稳定性时，才用同一 `original_seed`、同一配置的 clean repeats 计算 mean/min/max/range，并按 `docs/workflow/protocols/promotion.md` 进入 promotion 判断。多个 stable-confirmed 候选同时存在时，按 `confirmed_H` 最高者确定为正式版本；`best_observed_H` 只回答“最高跑到过多少”，不能单独决定 promotion。promotion 表示确定正式版本/tag，不等于自动执行 `activate-version` 或切换 active runtime alias。
 - 训练产生的 checkpoint 不进 GitHub。一次 campaign 收口后，只保留 H 排名前 3 的 `model_best`/best-model checkpoint；其余训练 checkpoint 可在写入 retention manifest 后删除。日志、receipt、summary、manifest、registry 和配置证据不能随 checkpoint 清理一起删除。
 - Trial 代码快照使用类似 `trial/idea-0001/trial-001` 的 tag。
 - 当前阶段已经强制执行 GTPJ 核心 workflow：任务路由、启动卡、pre-run freeze、artifact 边界、结果账本、质量门、agent 凭证和 promotion gate 都必须遵守。
 - OpenClaw / Codex 只是不同 runtime 入口；它们必须共享同一套 GitHub 事实源和 workflow 规范。
 - `workflow/gtpj_workflow.py` 是结构辅助工具，用于 validate、audit-boundary、目录创建和结果记录等机械动作；它不替代 Coordinator 的研究判断、owner 决策、代码审查或实验解释。
 - `docs/PROJECT_STRUCTURE.md` 是项目结构总账本；新增、删除、移动、重命名文件或改变文件职责时必须同步更新。
 - 不创建 controller branch。
 - 不迁移旧实验 ID、旧分支、旧 PR 或旧 workflow 文件。
 - 除非 owner 明确要求 push，否则不要 push。
 
 ## 实验规则
 
@@ -87,30 +106,31 @@
 - 只有版本级 tune、ablation 和 confirmation 才写入正式版本目录，例如 `experiments/v1/`。
 - 模块 trial 内部为了判断一个新模块好不好，可以做 trial-internal param tune、narrow ablation、confirmation/rerun；这些写入该 trial 的 `ATTEMPTS.md` 和 `attempts/ATTEMPT-xxx/`，不要误放到 `experiments/vX/tune|ablation|confirmation/`。
 - 如果 trial 内部尝试已经改变实现假设、forward 路径、新 loss 机制或评估语义，就新开 `TRIAL-002`，不要继续堆在同一个 `TRIAL-001`。
 - 真实训练或会产出正式证据的运行，必须从 `git status --short` 为空的 clean worktree 启动；dirty tree 只能用于临时 debug/smoke，且结果不能记为 `keep`、`best`、`promote` 或 confirmation evidence。
 - 如果一次 run 需要先在仓库里新增 `config.yaml`、`ATTEMPTS.md` 计划行、启动卡或其他预跑账本，必须先把这些“运行前文件”冻结成一次 `pre-run freeze commit`，再确认工作树 clean 后才能启动 Runner。
 - `pre-run freeze commit` 只允许包含本次 run 的配置、副本、计划和轻量预跑元数据，不允许提前写入本次 run 的 `manifest.yaml`、`result.yaml`、`result.md`、`quality_check.md`、指标结论或 artifact 注册。
 - 真实 run 启动时必须记录并引用冻结后的 `run_commit`；run 完成后，结果账本、artifact 注册和索引更新应进入单独的 `post-run result commit`，不要把“影响运行的配置改动”和“运行后的结果记账”混在同一次提交里。
 
 ## Multi-agent 规则
 
 - GTPJ 真实实验 workflow 默认使用 `real_multi_agent`。核心原因是一个长期角色对应一个独立上下文；把规划、执行、日志解析、质量检查、结果解释和复核放进同一个上下文，会污染证据链和决策。
 - 每次 GTPJ workflow 启动卡必须写明 `agents.activation_mode`，只能是 `role_only` 或 `real_multi_agent`。
-- 正式 `real_multi_agent` 默认使用 `agents.agent_instance_mode: temporary_subagent` 和 `lifecycle: workflow_scoped`。长期 agent 不是“永久在线聊天窗口”，而是 `profile.md`、`memory.md`、by-experiment 调用规则、历史 `agent_summary/review_round`、issues 和当前 workflow 的独立活上下文共同构成。
-- `temporary_subagent` 是本轮 workflow 或 campaign 阶段的活上下文；它可以持续到本轮工作结束，但结论必须沉淀到 repo、log、artifact、Research、Warehouse、result、quality 或 `agent_summary.md`。
+- 正式 `real_multi_agent` 默认使用 `agents.agent_instance_mode: named_owner_thread` 和 `lifecycle: workflow_scoped`。如果目标是服务器 detached 连续训练、owner 明确不希望创建线程，则允许 `activation_mode: role_only` + `formal_runtime_backend: server_detached_role_only` 作为第二条正式路径。
+- `named_owner_thread` 是本轮 workflow 或 campaign 阶段的活上下文；它可以持续到本轮工作结束，但结论必须沉淀到 repo、log、artifact、Research、Warehouse、result、quality 或 `agent_summary.md`。
 - `persistent_thread` 只在角色需要跨多个 workflow 连续追踪、owner 明确要求可见长期线程，或长周期 campaign 的 Coordinator/Monitor 需要跨天连续上下文时启用。线程上下文可能压缩或漂移，所以任何结论进入正式 evidence 前仍必须回到 repo、log、artifact 或 Research 验证。
-- `role_only` 表示一个主 agent 按 Coordinator、Runner、Quality Checker 等角色清单串行执行；必须在 `agent_summary.md` 里说明为什么没有启动真实多 agents。
+- `role_only` 表示一个主 agent 按 Coordinator、Runner、Quality Checker 等角色清单串行执行；如果结果进入正式证据，必须显式声明 `formal_runtime_backend: server_detached_role_only`，并在 `agent_summary.md` 里说明为什么没有启动真实多 agents。
 - `real_multi_agent` 表示启动或委派独立 agent / reviewer / checker，保留独立输入、发现和结论；如果当前环境没有真实 multi-agent 工具，不能把顺序角色扮演写成 `real_multi_agent`。
+- `real_multi_agent` 必须分文件复核：每个只读角色要在自己的输出里写 `files_reviewed`、`decision` 和 `uncovered_scope`，并指向独立 output file。入口规则、hard gate、helper 测试和本地 skill 镜像必须分别有人看，不能由一个上下文代替全部检查。
 - `role_only_with_independent_sequential_review` 不是第三种 activation mode，只能写在 `agents.tool_support.fallback_mode`；它不能用于 promotion、正式 best 结论或 owner 已明确要求真实多 agents 的任务，除非 owner 明确接受 debug/smoke 降级。
 - owner 明确要求多 agents、启动真实 Runner、产出正式 evidence、任务修改模型/forward/loss/eval/数据流语义、涉及接口/评估/label mapping/seen-unseen split/class order/logits shape/metric semantics 风险、结果异常有争议、promotion 前复核、结论会影响论文实验路线或 baseline 选择时，必须使用 `real_multi_agent`。
 - 窄范围 rerun / confirmation 准备、训练前候选 triage、只读解释、配置查看、debug/smoke 或不改变结论的账本格式整理时，可以使用 `role_only`，但必须记录代执行的角色和升级条件；debug/smoke 结果不能进入 keep、best、promotion 或 confirmation evidence。
 - Runner 永远串行并锁 GPU；Implementer 是同一代码路径唯一 writer；Coordinator 是最终 GitHub 账本唯一写入者；Reader/Planner、Log Analyst、Quality Checker、Result Analyst、Reviewer 默认只读，可并行。
 - Agent 不能把隐藏聊天记忆当实验事实源。Codex memory 或历史会话摘要只能用于定位，必须回到当前 repo、日志或 artifact 验证后才能写入结果、质量门或 promotion 证据。
-- `agent_summary.md` 必须记录 `activation_mode`、`agent_instance_mode`、`agent_instance_type`、`lifecycle`、`persistent_thread_id`（如启用）、`temporary_subagent_reason`、`independence_scope`、`output_locations`、`memory_used`、`memory_sources` 和 `verified_against_current_repo`。
+- `agent_summary.md` 必须记录 `activation_mode`、`agent_instance_mode`、`agent_instance_type`、`lifecycle`、`persistent_thread_id`（如启用）、`named_thread_reason`、`independence_scope`、`output_locations`、`memory_used`、`memory_sources` 和 `verified_against_current_repo`。
 - 如果 owner 对 agent 模式提出异议，先暂停真实 run，修正启动卡或升级为 `real_multi_agent` 后再继续。
 
 ## 安全
 
 - 不提交数据集、checkpoint、原始 cache、密钥或大型日志。
 - 不使用训练/测试反馈在运行中途改变训练行为。
 - 不隐藏失败实验；失败也要作为证据记录。
diff --git a/docs/workflow/CLAUDE_CONTEXT.md b/docs/workflow/CLAUDE_CONTEXT.md
index a03653b..2d12ec7 100644
--- a/docs/workflow/CLAUDE_CONTEXT.md
+++ b/docs/workflow/CLAUDE_CONTEXT.md
@@ -1,35 +1,35 @@
 # Claude Code 共享项目上下文
 
 ## 当前审核分层
 
 - 机器验证永远优先于模型意见。
-- `fast` 不调用 Claude Code，但必须有机器验证通过和临时 Codex agent 预审通过。
+- `fast` 不调用 Claude Code，但必须有机器验证通过和命名 Codex 线程预审通过。
 - `review-1` 只需要 1 轮 Claude Code，用于普通 workflow/helper/template 修补。
 - `strict-3` 才需要 3 轮 Claude Code，只用于会污染正式实验结论、promotion、baseline 或论文 claim 的改动。
-- Claude Code 前必须读取 `02_codex_temp_agent_pre_review.md`，确认临时 Codex agent 已 `completed_closed`。
+- Claude Code 前必须读取 `02_codex_named_thread_pre_review.md`，确认命名 Codex 线程已 `completed_archived`。
 
 本文件是 GTPJ 给 Claude Code 的轻量共享上下文。它只记录稳定规则，当前事实仍以本次审核包、仓库文件、验证命令和实验 artifact 为准。
 
 ## 项目目标
 
 GTPJ 是面向 GZSL（广义零样本学习）实验的研究 workflow。GitHub 仓库只保存轻量治理、配置、结果账本和证据索引；原始日志、checkpoint、生成图和大文件留在 Warehouse 或 Research 目录。
 
 ## 核心硬规则
 
 - 机器验证优先于模型意见。
 - Claude Code 只读审核，Codex 负责实现和修复。
 - 正式实验不能绕过 `agent_runtime.yaml`、`validate-agent-runtime`、`multi-agent-preflight` 和 cleanup 记录。
 - raw artifacts 不能进入 GitHub；GitHub 只记录 artifact id、URI、sha256、size、config、manifest、result 和 quality。
-- exact repeat 必须固定原始 seed；多 seed 只能称为 seed sweep 或 stability，不算 exact repeat。
+- exact repeat 必须固定原始 seed；正式复现必须写 `repeat_type: exact_repeat`、`original_seed`、`max_attempts: 5`、`max_attempts_hard_cap: true`、`early_stop_on_best_hit: true`、`restore_target_H`、`near_miss_tolerance_H`、`near_miss_not_restored`。同一候选无论是否还原成功都最多 5 次；多 seed / `seed_sweep` / `multi_seed_stability` 必须写 `not_confirmation_evidence: true`，不算 exact repeat。
 - `best_observed_H` 表示历史最高观察值；`confirmed_H` 表示确认复现实验的确认值，二者不能混用。
 - promotion 必须有完整 result、quality、artifact、confirmation 和 promotion evidence；普通调参或未确认结果不能自动升版本。
 
 ## Claude 快速审核策略
 
 默认使用 focused 审核：
 
 - 先读 `CLAUDE.md` 和本文件。
 - 再读审核包中的 `02_review_brief.md`、`02_focused_diff.md`、`03_validation.md`、`04_claims.md`。
 - 只在 focused diff 不足以定位阻断问题时读取完整 `02_diff.patch`。
 
 默认使用 blocking-only 审核：
diff --git a/docs/workflow/README.md b/docs/workflow/README.md
index 118d52e..9671e51 100644
--- a/docs/workflow/README.md
+++ b/docs/workflow/README.md
@@ -23,25 +23,25 @@
 | `WORKFLOW_KERNEL.md` | 不可破坏的核心规则：证据、agents、版本、保留策略和安全边界。 |
 | `WORKFLOW_MANIFEST.yaml` | 机器可读文档索引。 |
 | `WORKFLOW_FILE_MAP.md` | 说明哪些文件是有效入口、参考资料、历史记录或模板。 |
 
 ## Core 文件
 
 | 文件 | 用途 |
 |---|---|
 | `core/QUICK_START.md` | 人话短口令备忘。 |
 | `core/WORKFLOW_ROUTER.md` | 完整路由表。任务类型模糊或混合时再读。 |
 | `core/TASK_START_MINI.md` | 给 owner 看的精简启动摘要。 |
 | `core/TASK_START_CARD.md` | 正式写入或运行前的完整 Coordinator 启动卡。 |
-| `core/AGENT_RUNTIME_HARD_GATE.md` | 正式 Runner 启动前的真实右侧临时 agents 硬门。 |
+| `core/AGENT_RUNTIME_HARD_GATE.md` | 正式 Runner 启动前的左侧命名 Codex 线程硬门。 |
 
 ## 执行卡 Playbooks
 
 每种任务只选一个执行卡：
 
 ```text
 docs/workflow/playbooks/paper_intake.md
 docs/workflow/playbooks/paper_to_experiment.md
 docs/workflow/playbooks/tune.md
 docs/workflow/playbooks/ablation.md
 docs/workflow/playbooks/confirmation.md
 docs/workflow/playbooks/innovation.md
@@ -75,24 +75,35 @@ GitHub 仍然是工作流规范的权威来源。本地 Codex skill 只是执行
 
 ```text
 START_HERE.md
 -> WORKFLOW_KERNEL.md
 -> 相关 playbook
 -> core/TASK_START_CARD.md
 -> core/AGENT_RUNTIME_HARD_GATE.md
 -> validate-agent-runtime
 -> multi-agent-preflight
 -> Runner
 ```
 
+正式待跑实验的最短查询链是：
+
+```text
+experiments/vX/<type>/INDEX.md
+或 experiments/module_trials/.../TRIAL-xxx/ATTEMPTS.md
+-> attempts/ATTEMPT-xxx/manifest.yaml
+-> .gtpj_runtime/batches/<run_id> 只核对执行状态
+```
+
+`.gtpj_runtime` 不是正式待跑表；没有正式表格行的运行目录统一视为 `orphan_runtime_plan`。
+
 组合实验用同一个入口自动路由：
 
 ```bash
 python workflow/gtpj_workflow.py start --phrase "跑2创新+8调参"
 ```
 
 论文到实验闭环用桥接执行卡，不直接从 paper intake 开训；正式实验必须由 owner 指定 base version：
 
 ```bash
 python workflow/gtpj_workflow.py start --phrase "基于 v5 从论文开始做实验"
 ```
 
diff --git a/docs/workflow/START_HERE.md b/docs/workflow/START_HERE.md
index dccdac2..3c042a1 100644
--- a/docs/workflow/START_HERE.md
+++ b/docs/workflow/START_HERE.md
@@ -1,31 +1,58 @@
 # GTPJ 工作流入口
 
 这是每个 GTPJ 任务的精简入口，用来取代“每次都读完整 workflow 目录”的旧习惯。
 
+## 0. Owner 简单入口
+
+owner 不需要背 `workflow_mode`、`agent_runtime.yaml` 或线程字段。下面三句就是正式入口：
+
+| owner 口令 | Coordinator 必须解释成 | 允许动作 |
+|---|---|---|
+| `本地正式，干净` | `workflow_mode=live_multi_agent_monitor` | 先确认侧边栏干净；允许创建本轮左侧命名 Codex 线程；不启动服务器 runner。 |
+| `开启多agents智能体工作流，开始` / `开启多agents智能体工作流，跑N轮` / `开启多agents智能体工作流，做N轮实验` | `workflow_mode=live_multi_agent_monitor` | owner 已明确选择动态多 agents 工作流；不得反复确认 workflow 模式或启动意图；通过硬门后继续创建角色、生成计划并启动对应 runner。 |
+| `服务器冻结，开始` | `workflow_mode=server_frozen_runner` | 不创建命名线程；走本地规划、gate、冻结计划和服务器 detached runner。 |
+| `只做本地规划` | `activation_mode=role_only` | 只做状态检查、账本整理、计划和 debug/smoke；不进入正式证据。 |
+
+硬规则：只有 `本地正式，干净` 这句同时表达“侧边栏干净”和“允许创建本轮命名线程”。如果 owner 只说“本地正式”但没有说“干净”，Coordinator 只问一句：`侧边栏干净吗？回复：干净。`
+
+明确入口硬规则：owner 已经说出 `开启多agents智能体工作流`、`多agents智能体工作流，开始`、`跑N轮` 或 `做N轮实验` 时，Coordinator 必须把它当作执行授权，而不是只做规划。只有四类情况允许再问一次：运行模式仍然不明、侧边栏干净状态从未确认且工具无法验证、硬门失败、或动作涉及 push / 删除 / 覆盖数据 / 密钥等安全边界。除此之外，不得反复确认规范、不得把“开始/跑N轮”降级成 `pre_run_planned` 后停止。
+
+代码审核硬规则：代码审核不被 `server_frozen_runner` 豁免。`server_frozen_runner` 只说明训练运行期不创建命名线程；凡是修改代码、workflow、helper、模板或训练配置生成逻辑，仍必须先切专用代码审核分支，再执行命名 Codex 线程预审、Claude Code 只读审核、机器验证和 `validate-ai-cross-review`。在旧脏分支上先改后补切，只能视为草稿，不能进入 `pre-run freeze commit` 或正式 Runner。
+
+通用话规划入口：
+
+| owner 说 | Coordinator 必须解释成 | 允许动作 |
+|---|---|---|
+| `规划下一轮实验` / `下一轮怎么跑` | `experiment_planning` | 只读自动生成 Evidence Summary、Candidate Decision、Current Run Plan；不启动 Runner。 |
+| `批量规划50轮实验` / `给我规划50轮` | `experiment_planning` with budget 50 | 只读规划批量候选、预算、阻塞和 ledger_target；不创建 batch。 |
+| `规划10创新+100调参` / `跑10创新+100调参` | `mixed_experiment_campaign` planning | 拆成 workstreams；先过 planning gate，再进入 campaign gate。 |
+| `按这个计划开多agents工作流` | `live_multi_agent_monitor` | 需要真实左侧命名线程、`agent_runtime.yaml` 和 preflight；通过后才能启动正式 Runner。 |
+| `按这个计划服务器冻结跑` | `server_frozen_runner` | 训练运行期不创建命名线程；若计划涉及代码/helper/template 改动，先完成代码审核门；通过 server-detached gate 后才能启动 detached Runner。 |
+
 ## 1. 先判断模式
 
 使用仍然合规的最小模式：
 
 | 请求 | 模式 |
 |---|---|
 | 解释、检查、汇报状态、列候选 | `role_only` |
 | 启动或监控真实 runner、记录正式证据、比较 best、影响下一轮高成本实验、改变代码/配置语义、准备 promotion | `real_multi_agent` |
 | 不计入证据的 debug/smoke | 可以 `role_only`，但结果不能作为正式 evidence |
 
 正式实验默认：
 
 ```yaml
 activation_mode: real_multi_agent
-agent_instance_mode: temporary_subagent
+agent_instance_mode: named_owner_thread
 lifecycle: workflow_scoped
 formal_runner_allowed: true
 formal_evidence_allowed: true
 owner_monitor_mode: true
 owner_role: monitor
 owner_visible_reporting: true
 ```
 
 `persistent_thread` 只是可选的可见长期上下文，不是正式证据。
 
 Owner 是默认监控者。正式 Runner 启动后，Coordinator 不能只发一次 final 就结束可见流程；
 必须持续用当前对话或明确的 Monitor 线程汇报：
@@ -37,28 +64,76 @@ Owner 是默认监控者。正式 Runner 启动后，Coordinator 不能只发一
 下一步动作
 如果主对话暂停，去哪里接着看
 ```
 
 正式 Runner 启动还必须通过：
 
 ```text
 docs/workflow/core/AGENT_RUNTIME_HARD_GATE.md
 agent_runtime.yaml
 python workflow/gtpj_workflow.py validate-agent-runtime --path <agent_runtime.yaml>
 ```
 
-没有右侧临时 agents、没有真实 agent id、没有 pre-run allow/check，就不能启动正式 Runner。
+创建命名线程 前必须先确认左侧栏干净。若 owner 报告左侧栏已有历史 agents，
+或者当前工具只能关闭本轮已知 id、不能枚举 UI 中全部旧 agent，则不能继续开新的
+`real_multi_agent`。正确动作是先 cleanup；无法 cleanup 的旧 UI agent 必须记为
+`unknown_ui_agent`，正式 Runner 阻断。只有 owner 明确接受非正式排障时，才可走
+`debug_smoke`，且结果不能进入 keep / best / confirmation / promotion。
+
+没有左侧命名 Codex 线程、没有真实 agent id、没有 pre-run allow/check，就不能启动正式 Runner。
 这种情况必须阻断正式工作；只有 owner 明确接受非正式排障时，才可以另开 `debug_smoke`
 路径，且结果不能进入 keep / best / confirmation / promotion / version 判断。
 
+统一调度入口必须显式区分两种运行等级，不能默认猜：
+
+```text
+debug_smoke：测试代码、服务器、GPU 和 helper 链路；activation_mode=role_only；formal_evidence=false。
+formal：正式证据实验；允许 `activation_mode=real_multi_agent`，或 `activation_mode=role_only + formal_runtime_backend=server_detached_role_only`；两者都必须先通过 agent_runtime gate。
+```
+
+因此 `run-workflow` 这类统一入口必须二选一：
+
+```bash
+python workflow/gtpj_workflow.py run-workflow ... --workflow-mode live_multi_agent_monitor --debug-smoke
+python workflow/gtpj_workflow.py run-workflow ... --workflow-mode live_multi_agent_monitor --formal --agent-runtime-gate <agent_runtime.yaml>
+python workflow/gtpj_workflow.py run-workflow ... --workflow-mode server_frozen_runner --formal --agent-runtime-gate <agent_runtime.yaml>
+```
+
+正式实验必须显式选择 `workflow_mode`，不能由 Coordinator 默认猜测：
+
+| `workflow_mode` | 中文含义 | 适用场景 | gate 要求 |
+|---|---|---|---|
+| `live_multi_agent_monitor` | 动态多 agents 监控工作流 | owner 要求边跑边监控、质量检查、结果解释、best/promotion 判断，且接受命名 Codex 线程参与 | `activation_mode=real_multi_agent`，`agent_instance_mode=named_owner_thread` |
+| `server_frozen_runner` | 本地规划 + 服务器冻结训练工作流 | owner 要求本地只做规划/gate/账本/frozen plan，训练在 `lab4090` detached 跑，本地可以关机 | `activation_mode=role_only`，`formal_runtime_backend=server_detached_role_only`，`thread_creation_allowed=false` |
+
+owner 只说“用工作流”但没有指定模式时，Coordinator 必须先确认：
+
+```text
+这次用 workflow_mode=live_multi_agent_monitor，还是 workflow_mode=server_frozen_runner？
+```
+
+如果 owner 已经明确说“多agents智能体工作流”，它不属于“只说用工作流”的模糊入口，直接解释为 `live_multi_agent_monitor`。
+
+不能把 `server_frozen_runner` 的底层 `plan-dynamic-routing-batch + scp + screen` 当成 `live_multi_agent_monitor`，也不能把 `live_multi_agent_monitor` 降级成服务器离线训练。
+
+没有 `--formal` 和通过的 `agent_runtime.yaml`，即使服务器真的跑了训练，也只能算 runner/debug 事实，不能算正式工作流证据。
+
+## 1.1 文档语言边界
+
+项目文档、workflow 文档、模板说明和审核报告的正文必须使用中文，不允许整段英文说明。
+
+英文只保留为必要名词或机器标识，例如论文标题、方法名、角色名、命令、字段名、文件名、代码标识、指标名、URL 和 helper 依赖的结构 marker。
+
+如果必须保留 `Framework Diagram`、`Trial Flow`、`Code Flow Diagram` 这类英文结构 marker，同一节必须用中文说明它是什么、为什么需要、应该填写什么。新模板不得只给英文标题和英文正文。
+
 ## 2. 最小阅读顺序
 
 除非任务需要更多细节，否则只读这条链：
 
 ```text
 1. START_HERE.md
 2. WORKFLOW_KERNEL.md
 3. docs/workflow/playbooks/ 下的相关 playbook
 4. 只有路由模糊时才读 docs/workflow/core/WORKFLOW_ROUTER.md
 5. 正式写入或运行前读 docs/workflow/core/TASK_START_CARD.md
 6. 正式 Runner 前读 docs/workflow/core/AGENT_RUNTIME_HARD_GATE.md
 ```
@@ -70,25 +145,25 @@ python workflow/gtpj_workflow.py validate-agent-runtime --path <agent_runtime.ya
 ```bash
 python workflow/gtpj_workflow.py list-workflow-files
 ```
 
 ## 3. 用户人话路由
 
 | 用户说 | 默认路由 | 执行卡 |
 |---|---|---|
 | `汇报`, `查状态`, `现在怎么样` | 只读状态检查 | 无，使用 `WORKFLOW_KERNEL.md` |
 | `读论文`, `找创新点` | 论文读取 / idea discovery | `playbooks/paper_intake.md` |
 | `基于 vX 从论文开始做实验`, `论文到实验闭环`, `读论文并验证创新` | paper -> idea -> module trial 闭环；缺 `vX` 时只做候选创新 | `playbooks/paper_to_experiment.md` |
 | `调参` | 调参 Tune | `playbooks/tune.md` |
-| `消融` | 消融 Ablation | `playbooks/ablation.md` |
+| `消融` | 消融 Ablation；只允许关闭/旁路/替换既有因素，不新增方法模块 | `playbooks/ablation.md` |
 | `复现`, `确认这个结果` | 复现确认 Confirmation | `playbooks/confirmation.md` |
 | `开新模块`, `试这个想法` | 创新 / module trial | `playbooks/innovation.md` |
 | `升版本` | 升版 Promotion | `playbooks/promotion.md` |
 | `跑10创新+100调参` 或任意数量组合 | 混合实验 campaign | `playbooks/mixed_campaign.md` |
 | `全自动研究campaign`, `从论文到最终结果都接管` | 全自动研究 campaign | `playbooks/autonomous_campaign.md` |
 
 helper 会自动解析 `跑2创新+8调参` 这类组合短语：
 
 ```bash
 python workflow/gtpj_workflow.py start --phrase "跑2创新+8调参"
 ```
 
@@ -142,24 +217,31 @@ chain head 推导出来。聊天结论、服务器状态和 `agent_summary.md` 
 从论文获得创新时，多一段前置闭环，但仍然只接入同一个实验闭环：
 
 ```text
 paper_inbox -> source_review -> idea_candidate -> formal_IDEA -> selected_queue
 -> trial_preflight -> runner_evidence -> idea_feedback
 ```
 
 进入 `trial_preflight` 前必须由 owner 明确指定 `base_version` / `base_code_tag`，例如
 `基于 v5 从论文开始做实验`。不能默认使用当前 active version。
 
 混合实验目录只做调度索引；正式结果必须写回各自归属的 attempt / version / trial。
 
+框架记录只跟“方法框架变动”绑定，不跟每个代码文件绑定：
+
+```text
+调参 / 复现 / 只关闭既有组件的窄消融 -> 不新增 framework_diagram，只记录结果证据。
+新增或改写 module / forward / loss / eval / data view / 接口语义 -> 创新 / module trial，必须记录框架和模块来源。
+```
+
 ## 6. 证据优先
 
 不要让聊天记忆变成正式证据。
 
 正式证据只来自：
 
 ```text
 manifest.yaml
 result.yaml
 result.md
 quality_check.md
 agent_summary.md
@@ -170,55 +252,101 @@ Warehouse logs/checkpoints/receipts
 ```
 
 如果某个结论会影响 keep/drop/best/repeat/promotion/versioning 或下一轮高成本实验，就必须能追溯到文件或 artifact。
 
 debug/smoke 结果必须显式锁定为：
 
 ```yaml
 evidence_level: debug_smoke
 formal_evidence: false
 eligible_for_keep_best_promotion_confirmation: false
 ```
 
+## 6.1 正式待跑实验入口
+
+Owner 问“现在有哪些待跑实验”时，只读正式 ledger，不从 `.gtpj_runtime/` 反推。正式待跑实验必须能在对应类型的正式表格里看到：
+
+| 实验类型 | 正式待跑表格 | 说明 |
+|---|---|---|
+| 版本级 tune | `experiments/vX/tune/INDEX.md` | 只记录正式 baseline 的调参计划和结果。 |
+| 版本级 ablation | `experiments/vX/ablation/INDEX.md` | 只记录正式 baseline 的消融计划和结果。 |
+| 版本级 confirmation | `experiments/vX/confirmation/INDEX.md` | 只记录正式 baseline 或版本级 candidate 的确认计划和结果。 |
+| module trial 内部 attempt | `experiments/module_trials/.../TRIAL-xxx/ATTEMPTS.md` | 记录同一 trial 内的调参、窄消融、rerun、confirmation 和 debug-fix。 |
+| mixed campaign | `experiments/campaigns/.../WORK_ITEMS.md` / `RESULT_INDEX.md` | 只做 derived index；每个 work item 仍要回指上面某个正式表格。 |
+
+待跑实验的判定规则：
+
+```text
+formal_pending = 正式表格中有 subject 行
+              + subject 有明确实验类型、run_id 或计划目录
+              + 状态为 planned / pending / pre_run / pre_run_gated / ready_to_run
+              + 不是 debug_smoke，或已明确标注 formal_evidence: true
+```
+
+`.gtpj_runtime/batches/<run_id>` 只是 runner 执行缓存；它可以证明运行包存在、事件是否发生、summary 是否产出，但不能单独决定“待跑实验”。如果 runtime 目录存在而正式表格没有对应行，统一标为 `orphan_runtime_plan`，只能作为历史参考或排障线索，不能自动续跑、不能进入 keep / best / confirmation / promotion。
+
 ## 7. 免 owner 日常参与的 AI 交叉审核
 
 重要代码、workflow/helper/template、训练入口、评估语义、实验结论或 promotion 相关改动，默认不需要 owner 参与日常审核。
 
 改动必须按 `review_tier` 走 Claude Code + Codex 分层交叉审核：
 
 ```text
 机器验证永远必跑
-Codex 临时 agent 预审并关闭 -> Claude Code 只读审核 -> Codex 回应/重跑验证
+Codex 命名线程 预审并关闭 -> Claude Code 只读审核 -> Codex 回应/重跑验证
 fast: 0 轮 Claude，仅低风险轻量修补
 review-1: 1 轮 Claude，普通 workflow/helper/template 修补
 strict-3: 3 轮 Claude，训练入口、评估语义、正式实验结论、promotion、baseline 或论文 claim 风险
 validate-ai-cross-review -> 通过后才信任改动
 ```
 
 正式通过条件记录在 `docs/workflow/protocols/ai_cross_review_protocol.md`。通过包必须包含：
 
 ```text
 owner_participation: not_required
 rounds_completed: 3
 claude_code_read_only: true
 machine_gates_passed: true
 unresolved_blocking_issues: 0
 ```
 
-## 8. 临时 agent 命名
+## 8. 命名线程
 
-正式 `real_multi_agent` 不能使用随机英文昵称。右侧栏临时 agent 必须按任务命名：
+正式 `real_multi_agent` 不能使用随机英文昵称。左侧栏命名 Codex 线程必须按任务命名：
 
 ```text
 <subject_id> | <Role Label>
 ```
 
 示例：
 
 ```text
 ATTEMPT-007 | Runner Monitor
 ATTEMPT-007 | Interface Checker
 ATTEMPT-007 | Evidence Quality Checker
 ```
 
-命名必须写入 `agent_runtime.yaml` 的 `temporary_subagent_display_names`，并由
+命名必须写入 `agent_runtime.yaml` 的 `named_thread_titles`，并由
 `validate-agent-runtime` 校验。随机昵称或只写 `Runner` / `Quality` 这种泛名，不能启动正式 Runner。
+
+创建线程前还必须满足：
+
+```text
+left_sidebar_named_threads_ready: true
+owner_visible_sidebar_count: 0 或只包含本阶段 active threads
+unknown_ui_agents: none
+```
+
+## 9. Live Monitor 逐实验汇报
+
+`live_multi_agent_monitor` 不是“启动服务器后结束”。在 Runner 仍处于 running/pending 时，本轮左侧命名 Codex 线程必须保持可见，尤其是 Runner Monitor、Log Analyst、Result Analyst、Quality Checker 和 Interface Checker；只有 closeout/handoff 完成、输出写回账本后，才归档这些线程。
+
+监控每个新增 completed job 时使用统一入口：
+
+```powershell
+python workflow\gtpj_workflow.py monitor-workflow --run-dir <run_dir> --report-new-completions --activity-log <attempt_dir>\AGENT_ACTIVITY.md
+```
+
+每次报告至少写清 `job_id`、H/U/S/ZS、当前 best、是否出现 H>=75/H>=76、证据位置和下一步。`monitor_seen_completed_jobs.json` 只用于去重，不是正式结果源。
+
+如果 owner 看到的左侧栏数量与 `agent-cleanup-plan` 不一致，以 owner 可见 UI 为准；
+Coordinator 不得再开新的命名线程来“补 gate”。
diff --git a/docs/workflow/WORKFLOW_KERNEL.md b/docs/workflow/WORKFLOW_KERNEL.md
index 2f8c12f..7b0788c 100644
--- a/docs/workflow/WORKFLOW_KERNEL.md
+++ b/docs/workflow/WORKFLOW_KERNEL.md
@@ -1,126 +1,249 @@
 # GTPJ 工作流内核
 
 本文件是精简后的硬规则层，应该保持短而稳定。
 
 ## 1. 权威来源
 
 - GitHub 是可复现控制面、治理账本和轻量结果索引。
 - `GTPJ_Research` 保存长推理、论文/来源笔记和完整 idea 历史。
 - `GTPJ_Warehouse` 保存 raw logs、checkpoints、生成图、运行 receipt 和大型 artifact。
-- 聊天上下文、临时 agent 上下文、persistent thread 上下文和 Codex memory 只能辅助定位，不能作为正式证据。
+- 聊天上下文、命名线程 上下文、persistent thread 上下文和 Codex memory 只能辅助定位，不能作为正式证据。
+
+## 1.1 文档语言硬规则
+
+- 项目文档、workflow 文档、模板说明和审核报告的正文必须使用中文。
+- 不允许新增或改出整段英文说明；英文只能作为必要名词或机器标识保留。
+- 允许保留的英文包括：论文标题、方法名、角色名、命令、字段名、文件名、代码标识、指标名、URL，以及 helper 当前依赖的结构 marker。
+- 如果标题保留英文 marker，例如 `Framework Diagram`、`Trial Flow`、`Code Flow Diagram`，同一节必须用中文解释含义、用途、填写要求和阻断条件。
+- 新增模板必须先通过文档语言检查；历史 archive 可以保持原样，但不能作为新文档的写法模板。
 
 ## 2. 正式证据边界
 
 只要任务会影响下面任一内容，就属于正式证据工作：
 
 ```text
 manifest/result/quality/agent_summary
 ATTEMPTS keep/drop/reject/rerun
 best 或 top-k 选择
 repeat/confirmation
 promotion/version/tag 判断
 论文或 baseline 表述
 下一轮高成本实验
 代码/配置/评估语义
 ```
 
 正式证据工作必须使用 `real_multi_agent`。
 正式 Runner 启动前还必须满足 `docs/workflow/core/AGENT_RUNTIME_HARD_GATE.md`。也就是说，
-状态机记录和服务器 runner 都不能替代真实右侧临时 agents；没有 `agent_runtime.yaml`
+状态机记录和服务器 runner 都不能替代真实左侧命名 Codex 线程；没有 `agent_runtime.yaml`
 和通过的 `validate-agent-runtime` / `multi-agent-preflight`，正式 Runner 必须阻断。
 owner 只能把本轮目标改成非正式 `debug_smoke` 排障；`debug_smoke` 不能回填为正式证据。
 
 正式证据对象必须绑定 `subject_id` 和 `subject_type`。`evidence_state` 只能由
 tamper-evident append-only `TRANSITIONS.jsonl` 派生，`evidence_routing.yaml`
 只是当前状态缓存，不能手写覆盖。
 
 debug/smoke 只能用于排障或环境探针，必须记录：
 
 ```yaml
 evidence_level: debug_smoke
 formal_evidence: false
 eligible_for_keep_best_promotion_confirmation: false
 ```
 
+统一调度入口必须强制选择运行等级：
+
+```yaml
+debug_smoke:
+  activation_mode: role_only
+  formal_evidence: false
+  real_agent_instances_started_by_helper: false
+
+formal:
+  activation_mode: real_multi_agent
+  formal_evidence: true
+  agent_runtime_gate_satisfied: true
+```
+
+`run-workflow` 还必须显式选择 `workflow_mode`，禁止 Coordinator 猜测：
+```yaml
+workflow_mode:
+  required: true
+  allowed:
+    - live_multi_agent_monitor
+    - server_frozen_runner
+  no_default_guess: true
+```
+
+Owner 简单口令优先按下列映射解释：
+```text
+本地正式，干净 -> live_multi_agent_monitor；侧边栏干净；授权创建本轮左侧命名 Codex 线程；禁止启动服务器 runner
+开启多agents智能体工作流，开始 / 跑N轮 / 做N轮实验 -> live_multi_agent_monitor；不得反复确认 workflow 模式或启动意图；通过硬门后继续执行
+服务器冻结，开始 -> server_frozen_runner；不创建命名线程；允许服务器 detached runner
+只做本地规划 -> role_only；不进入正式证据
+```
+
+如果 owner 只说 `本地正式` 但没有说 `干净`，Coordinator 只问一次侧边栏是否干净；不能展开成长授权模板。
+
+- `live_multi_agent_monitor` 表示动态多 agents 监控工作流。它必须使用 `activation_mode: real_multi_agent`、`agent_instance_mode: named_owner_thread`，并通过左侧命名 Codex 线程 gate。
+- `server_frozen_runner` 表示本地规划、冻结计划、服务器 detached 训练工作流。它必须使用 `activation_mode: role_only`、`formal_runtime_backend: server_detached_role_only`、`thread_creation_allowed: false`，不能自动创建线程。
+- 如果 owner 只说“用工作流”但没有说明是哪一种，必须先问清楚；不能把服务器冻结训练当成动态多 agents 工作流，也不能把动态多 agents 工作流偷偷降级成离线训练。
+- 如果 owner 已经说“开启多agents智能体工作流”“多agents智能体工作流，开始”“跑N轮”或“做N轮实验”，它不是模糊的“用工作流”。Coordinator 必须按 `live_multi_agent_monitor` 执行，不得反复确认规范，不得只写 planning gate 后停止。只有运行模式仍冲突、侧边栏干净状态未确认且无法验证、硬门失败、或 push / 删除 / 覆盖数据 / 密钥等安全边界动作，才允许再问一次。
+
+代码审核不被 `server_frozen_runner` 豁免。`server_frozen_runner` 只豁免训练运行期的命名线程创建；它不能豁免代码、workflow、helper、模板或训练配置生成逻辑的 AI 交叉审核。此类改动必须先在专用代码审核分支完成，审核包通过后才能进入 `pre-run freeze commit`。如果改动已经在旧脏分支上发生，本轮正式启动必须阻断，除非重新从干净基线切分支并迁移最小 diff。
+
+没有显式 `--debug-smoke` 或 `--formal` 时必须阻断。选择 `--formal` 时必须提供并通过
+`agent_runtime.yaml`；选择 `--debug-smoke` 时结果只能证明工程链路可运行，不能回填为正式证据。
+
+## 2.1 正式待跑 ledger 硬规则
+
+正式待跑实验由正式 ledger 决定，不由运行缓存决定。任何“待跑”结论必须先读对应类型的表格：
+
+```text
+version-level tune        -> experiments/vX/tune/INDEX.md
+version-level ablation    -> experiments/vX/ablation/INDEX.md
+version-level confirmation -> experiments/vX/confirmation/INDEX.md
+trial-internal attempt    -> experiments/module_trials/.../TRIAL-xxx/ATTEMPTS.md
+mixed campaign            -> experiments/campaigns/.../WORK_ITEMS.md / RESULT_INDEX.md，只作 derived index
+```
+
+正式表格中的一行只有同时满足下面条件，才算 `formal_pending`：
+
+```text
+有 subject_id 或实验 id
+有实验类型
+有 run_id、计划目录或 attempt 目录
+状态是 planned / pending / pre_run / pre_run_gated / ready_to_run
+不属于 debug_smoke，或明确 formal_evidence: true
+```
+
+`.gtpj_runtime/` 只保存运行中状态和 runner 执行包。目录存在、`batch_status.status=planned`
+或旧 `events.jsonl` 为空，不能单独构成待跑实验。若 runtime 目录没有正式 ledger 行，统一记为
+`orphan_runtime_plan`；它可以用于历史参考或排障，但不得自动续跑、不得写入 keep / best /
+confirmation / promotion。
+
+## 2.2 实验规划门（Experiment Planning Gate）
+
+正式 batch、Runner、server frozen run 或 promotion-prep run 生成前，必须先通过 `experiment_planning`。
+这个阶段必须自动读取当前项目状态，而不是让 owner 手填计划。
+
+最小自动扫描：
+
+```text
+repo branch / HEAD / dirty
+current_version 和 baseline_repro_status
+正式待跑 ledger：experiments/vX/*/INDEX.md、TRIAL-xxx/ATTEMPTS.md、campaign derived index
+已完成 result / quality / agent_summary
+.gtpj_runtime 只作 debug context，不作规划权威
+```
+
+输出只保留三张表：
+
+```text
+Evidence Summary：证据从哪里来，能支持什么，不能支持什么。
+Candidate Decision：哪些候选值得跑，阻塞是什么，允许声称什么。
+Current Run Plan：本轮 work item、fingerprint_policy、预算、停止条件和 ledger_target。
+```
+
+每个 planned job 必须引用正式 `evidence_ref`，声明 `claim_scope`、`fingerprint_policy`、`budget`、
+`stop_condition` 和 `ledger_target`。没有 planning gate，不得生成 batch、启动 Runner 或写入
+formal evidence。只读 helper 入口：
+
+```bash
+python workflow/gtpj_workflow.py plan-experiments --phrase "<owner 口令>"
+```
+
+单项和批量规划使用同一个入口。显式组合口令如 `跑10创新+100调参` 会拆成多个 workstream；
+只给总量如 `做50轮实验` 时，planning gate 只能根据当前证据给出候选分配、阻塞和预算建议，
+不得在缺少实验类型和 evidence_ref 时直接生成 Runner batch。
+
 ## 3. Agent 规则
 
 正式任务默认：
 
 ```yaml
 activation_mode: real_multi_agent
-agent_instance_mode: temporary_subagent
+agent_instance_mode: named_owner_thread
 lifecycle: workflow_scoped
 owner_monitor_mode: true
 owner_role: monitor
 owner_visible_reporting: true
 ```
 
 含义：
 
 - Owner 是默认监控者。正式 Runner 启动后，工作流必须持续给 owner 可见汇报，
   不能把服务器离线训练、状态机文件或 agent_summary 当作 owner 已经看见过程。
 - 每次可见汇报必须说明：哪个智能体在做什么、当前状态、证据位置、下一步动作。
 - 如果 Coordinator 需要结束当前主对话，必须先给出监控交接位置、下一次检查条件和恢复命令。
 - 每个角色在当前 workflow 或 campaign 阶段拥有独立活上下文。
-- 正式运行必须记录真实 `agent_instance_id` 或可见 thread id；`temporary_subagent` 这类占位词不能冒充实例。
+- 正式运行必须记录真实 `agent_instance_id` 或可见 thread id；`named_owner_thread` 这类占位词不能冒充实例。
 - 需要长期保留的经验必须写回 `agent_summary.md`、角色 `memory.md`、workflow issues、result 文件或 campaign 账本。
 - `persistent_thread` 只是跨 workflow 可见追踪的可选上下文，不是 evidence。
 - 不要给每个实验 run 创建一个永久 agent/thread。
 - 每轮 workflow 结束或阶段结束时，Coordinator 必须先确认已完成 agents 的结论写入
   `agent_summary.md` / `AGENT_ACTIVITY.md` / result / quality / issues / memory 等正式位置，
-  然后关闭这些已完成 agents。右侧栏默认只保留当前阶段仍在工作的 active agents。
-- 右侧栏临时 agent 显示名必须严格按 `<subject_id> | <Role Label>` 命名，例如 `ATTEMPT-007 | Runner Monitor`、`ATTEMPT-007 | Interface Checker`、`ATTEMPT-007 | Evidence Quality Checker`。
+  然后关闭这些已完成 agents。左侧栏默认只保留当前阶段仍在工作的 active agents。
+- 多 agents 必须分文件复核：每个只读角色都要记录 `files_reviewed`、独立输出文件、allow/block/propose 结论和未覆盖范围。Coordinator 不能用一个上下文一次性“看过所有文件”来冒充独立复核，也不能漏掉 skill 镜像、active docs、helper 测试三类同步面。
+- 左侧栏命名线程 显示名必须严格按 `<subject_id> | <Role Label>` 命名，例如 `ATTEMPT-007 | Runner Monitor`、`ATTEMPT-007 | Interface Checker`、`ATTEMPT-007 | Evidence Quality Checker`。
 - 禁止使用与任务无关的随机英文昵称，例如 `Herschel`、`Galileo`、`Feynman`、`Bohr`；只写 `Runner` / `Quality` 这种泛名也不合格。
 - 角色名要清晰，例如 `运行监控 (Runner Monitor)`、`日志分析 (Log Analyst)`、`证据质量检查 (Evidence Quality Checker)`、`结果比较 (Result Comparator)`。
 - `Experiment Runner` 表示实际启动训练命令的运行角色；`Runner Monitor` 表示监控服务器、队列、GPU slot 和失败隔离的运行监控角色。小任务中二者可以由同一 Runner family 承担，但在启动卡和 `agent_summary.md` 里必须写清楚显示名和职责。
 
 写入边界：
 
 - 总控 (Coordinator) 是最终 GitHub 账本 writer。
 - 总控 (Coordinator) 是唯一可以 apply evidence transition 的角色。
 - 日志/结果角色可以 propose transition；接口/质量/复核角色可以 check transition。
 - 运行者 (Runner) 管理服务器/GPU 运行状态。
 - 同一个代码路径只能有一个实现者 (Implementer)。
 - 阅读/规划 (Reader/Planner)、日志分析 (Log Analyst)、质量检查 (Quality Checker)、结果分析 (Result Analyst)、接口检查 (Interface Checker) 和复核者 (Reviewer) 默认只读，除非明确授权。
 
 ## 4. 版本规则
 
 - 只调参数不能开新的 `vX`。
 - 新 `vX` 需要 confirmed promoted framework 或 method state，不能只是 tuned config。
-- `exact_repeat` 必须固定原始 seed；改变 seed 的多次运行只能叫 `seed_sweep` /
-  `score_search` / `multi_seed_stability`，不能叫严格复现。
-- confirmation 默认跑 3 次，但必须声明 repeat 类型。复现通过后，正式单值取 3 次中的最高 H，
-  同时保留 mean/min/max 作为稳定性证据。
+- `exact_repeat` 必须固定 `original_seed`、原始 config、代码 commit、data/cache、epoch schedule、batch size 和评估口径；改变 seed 或任何参数的多次运行只能叫 `seed_sweep` /
+  `score_search` / `multi_seed_stability`，必须写 `not_confirmation_evidence: true`，不能叫严格复现。
+- confirmation 默认 `repeat_type: exact_repeat`、`max_attempts: 5`、`max_attempts_hard_cap: true`、`early_stop_on_best_hit: true`。必须声明
+  `restore_target_H`；`near_miss_tolerance_H` 只用于标记接近但未还原。复现判定分三层：
+  `best_hit` 只看任一 clean repeat 是否达到 `restore_target_H`，用来回答“有没有还原”；`near_miss_not_restored`
+  表示接近目标、有希望，但不能停止、不能作为 confirmation；`stable_confirm`
+  看同一 `original_seed`、同一配置的 mean/min/max/range 是否满足预设门槛，用来回答“能不能作为稳定 confirmed / promotion / baseline 证据”。
+- `max_attempts_hard_cap` 表示同一候选无论是否还原成功最多跑 5 次；达到 `restore_target_H` 可以提前停止，5 次未达到则收口为 not restored / near miss，不能继续追加复现轮数。
+- 复现通过 `best_hit` 后，必须记录 `best_single_H` / `best_observed_H`；如果 `stable_confirm` 未通过，
+  结论只能是命中候选或继续复现，不能写成稳定确认。
 - promotion 和 baseline claim 默认比较 `confirmed_H` / repeat mean，不能只凭 best repeat。
 - 不能把未确认的 `best_observed_H` 说成 confirmed baseline。
 - 每个正式版本 `experiments/vX/` 必须有版本级 `framework_diagram.md` 和 `MODULES.md`；`VERSION.md` 必须链接它们并包含 `## Framework Diagram`。模块说明不能只列名字，必须解释 purpose、input、output、config switch 和 baseline-off behavior。
-- 创新代码、forward、loss、evaluation 或输入输出逻辑发生变化时，所属 Trial 的 `README.md` 必须包含 `## Code Flow Diagram`，用简洁流程图说明代码实际输入、输出、关键张量流向、分支开关和最终 logits/metric 出口；完整变量/方法说明仍放在 `framework_diagram.md`。
+- 框架记录绑定“方法框架”，不是绑定每个代码文件。调参、复现、只关闭或旁路既有组件的窄消融不新增框架图；它们只记录 config、manifest、result、quality 和 agent summary。
+- 凡是新增或改写 module、forward、loss、evaluation、data view、input/output、tensor flow、接口语义或模块分支逻辑，都视为创新 / module trial 代码变动，而不是普通 tune/ablation。此时必须记录 `module_source.md`、`implementation.md`、`framework_diagram.md`，并说明每个模块来源、接入点、输入输出、baseline-off 行为和 GZSL 语义边界。
+- 上述创新代码变动所属 Trial 的 `README.md` 必须包含 `## Code Flow Diagram`，用简洁流程图说明代码实际输入、输出、关键张量流向、分支开关和最终 logits/metric 出口；完整变量/方法说明仍放在 `framework_diagram.md`。
 - 批量实验 / mixed campaign 不能单独成为正式结果分支。它只能保存 routing index、run map、work item 映射和监控状态；正式结果必须自动回写到对应归属目录：version-level 写 `experiments/vX/<type>/`，trial-internal 写 `experiments/module_trials/.../TRIAL-xxx/attempts/ATTEMPT-xxx/`，真正新创新写对应 IDEA/TRIAL。
 
 ## 5. 运行安全
 
 正式运行前必须记录：
 
 ```text
 branch 和 commit
 git dirty 状态
 冻结后的 config
 agent_runtime.yaml 及 validate-agent-runtime 结果
 multi_agent_preflight 结果
 formal_runner_allowed、formal_evidence_allowed
 agent_instance_status、agent_status_refs、agent_output_refs
 owner_monitor_mode、report_channel、agent_activity_stream
-right_sidebar_retention_policy、close_completed_agents_on_stage_end、closed_agents_record
-agent-cleanup-plan 输出和 close_result 记录
+thread_archive_policy、archive_completed_threads_on_stage_end、archived_threads_record
+agent-cleanup-plan 输出和 archive_result 记录
 dataset/split/label mapping 假设
 GPU 或 runner slot 锁
 result/artifact 写入位置
 checkpoint retention 规则
 ```
 
 如果 label mapping、seen/unseen split、class order、logits shape 或 metric semantics 不清楚，必须硬阻断。
 所有正式实验必须满足 `docs/workflow/reference/GZSL_HARD_RULES.md`。
 
 ## 6. Checkpoint 保留规范
 
 工作流规范：
@@ -145,33 +268,47 @@ promotion_decision: promote
 没有未解决硬门
 ```
 
 promotion 可以按协议创建本地文件、commit 和 tag，但不能 push，除非 owner 明确要求。
 
 ## 8. 停止规则
 
 遇到下面情况要停止或降级：
 
 - 必要证据缺失。
 - 服务器/runtime 状态不清楚，可能污染结果。
 - workflow 要求正式多 agents，但当前没有真实 multi-agent 支持。
-- `activation_mode: real_multi_agent` 但没有真实右侧临时 agent 实例、pre-run allow/check 或 `agent_runtime.yaml`。
+- `activation_mode: real_multi_agent` 但没有真实左侧命名 Codex 线程实例、pre-run allow/check 或 `agent_runtime.yaml`。
 - `multi_agent_preflight` 未通过，或 `formal_runner_allowed` / `formal_evidence_allowed` 不是 true。
 - owner 改变范围。
 - 会跨越安全边界。
 
 停止时只汇报最小 unblock 动作。
 
+## Live Monitor 运行期规则
+
+`live_multi_agent_monitor` 的正式定义是：左侧命名 Codex 线程参与，Runner 可在服务器执行，但当前 owner 线程持续作为监控入口。Runner 仍在 running/pending 时，不得把本轮 active named threads 归档；归档只能发生在 closeout/handoff 后。
+
+每轮监控必须调用或等价执行：
+
+```powershell
+python workflow\gtpj_workflow.py monitor-workflow --run-dir <run_dir> --report-new-completions --activity-log <attempt_dir>\AGENT_ACTIVITY.md
+```
+
+新增 completed job 必须逐条报告并写入 agent activity。报告至少包含 `job_id`、H/U/S/ZS、当前 best、H>=75/H>=76 命中情况、证据文件和下一步。只看到 server screen 存在或目录存在，不等于监控完成。
+
 ## 9. 反膨胀规则
 
+瘦身优先：新增规范、流程或文档前，先检查能否合并、删减或复用现有入口；默认写最小可执行规则，不为完整感新增层级。
+
 新增 workflow 文件、模板或协议前，必须至少满足一项：
 
 ```text
 可机器检查
 能驱动 evidence_state transition
 是权威事实源
 是正式 evidence 必需模板
 ```
 
 如果都不满足，不进入日常 workflow。
 
 ## 免 owner 日常参与的 AI 交叉审核
diff --git a/docs/workflow/agents/README.md b/docs/workflow/agents/README.md
index 5165db4..62bde11 100644
--- a/docs/workflow/agents/README.md
+++ b/docs/workflow/agents/README.md
@@ -7,25 +7,25 @@ shared_roles/       # 共享角色定义和长期角色记忆
 by_experiment/      # 每类实验如何调用共享角色
 long_term_memory.md # 长期 agent 记忆协议
 ```
 
 规则：
 
 - 共享角色只在 `shared_roles/` 定义。
 - 每个共享角色必须同时有 `profile.md` 和 `memory.md`。
 - 每个实验类型有自己的 `by_experiment/<type>/agents/README.md`。
 - 实验类型目录只写调用顺序、启用角色、禁用角色和关键检查，不复制角色定义。
 - 本地 `gtpj-workflow` skill 必须镜像本目录。
 - 长期 agent = `profile.md` + `memory.md` + 调用协议 + 历史 `agent_summary.md` + issues。
-- 临时 sub-agent / reviewer 实例是本轮 workflow 或 campaign 的活上下文；正式结果解释、best 选择和 promotion 必须回到文件化证据。
+- 命名线程 / reviewer 实例是本轮 workflow 或 campaign 的活上下文；正式结果解释、best 选择和 promotion 必须回到文件化证据。
 - `persistent_thread` 是跨 workflow 的可选活上下文，不是正式证据源。
 
 角色别名必须映射到稳定 `role_key`，避免侧栏显示名、summary 名称和规范名互相漂移：
 
 ```yaml
 role_aliases:
   Workflow Coordinator:
     role_key: coordinator
     zh_name: 工作流总控
   Campaign Planner:
     role_key: campaign_planner
     zh_name: Campaign 规划
diff --git a/docs/workflow/agents/by_experiment/ablation/agents/README.md b/docs/workflow/agents/by_experiment/ablation/agents/README.md
index d03ff8c..2c5761e 100644
--- a/docs/workflow/agents/by_experiment/ablation/agents/README.md
+++ b/docs/workflow/agents/by_experiment/ablation/agents/README.md
@@ -1,17 +1,17 @@
 # Ablation Agents
 
 本文件用于 version-level ablation。消融可以改代码，但代码是临时实验代码，不自动进入 `main`。
 
-正式 ablation run 默认使用 `real_multi_agent` + workflow-scoped `temporary_subagent`。Interface Checker、Log Analyst、Quality Checker 和 Result Analyst 必须保留独立上下文；正式结论必须写回 `agent_summary.md`、interface、quality、result 和 artifact evidence。跨 workflow 连续追踪时才启用 `persistent_thread`。
+正式 ablation run 默认使用 `real_multi_agent` + workflow-scoped `named_owner_thread`。Interface Checker、Log Analyst、Quality Checker 和 Result Analyst 必须保留独立上下文；正式结论必须写回 `agent_summary.md`、interface、quality、result 和 artifact evidence。跨 workflow 连续追踪时才启用 `persistent_thread`。
 
 如果消融对象只是某个 module trial 当前实现假设下的局部因素，使用 `module_trial_protocol.md`
 的 trial-internal narrow `ablation`，写入该 trial 的 `ATTEMPTS.md` 和
 `attempts/ATTEMPT-xxx/`，不写入 `experiments/vX/ablation/`。
 
 ## 启用角色
 
 ```text
 Coordinator
 Reader / Planner
 Implementer
 Interface Checker
diff --git a/docs/workflow/agents/by_experiment/confirmation/agents/README.md b/docs/workflow/agents/by_experiment/confirmation/agents/README.md
index 1e134b3..398c640 100644
--- a/docs/workflow/agents/by_experiment/confirmation/agents/README.md
+++ b/docs/workflow/agents/by_experiment/confirmation/agents/README.md
@@ -1,21 +1,21 @@
 # Confirmation Agents
 
 ## 默认模式更新
 
-正式 confirmation / rerun 默认使用 `real_multi_agent` + workflow-scoped `temporary_subagent`。Runner 仍然串行，但 Log Analyst、Quality Checker、Result Analyst 必须使用独立上下文；promotion 前或争议结果还必须启用 Reviewer。
+正式 confirmation / rerun 默认使用 `real_multi_agent` + workflow-scoped `named_owner_thread`。Runner 仍然串行，但 Log Analyst、Quality Checker、Result Analyst 必须使用独立上下文；promotion 前或争议结果还必须启用 Reviewer。
 
 `role_only` 只允许用于准备冻结配置、查看复现状态，或明确不登记正式证据的 debug/smoke。
 
-`temporary_subagent` 可以覆盖本轮 confirmation workflow；正式复现结论、best 复核和 promotion-facing 结论必须回到 `agent_summary.md`、result、quality 和 artifact evidence。跨 workflow 连续追踪时才启用 `persistent_thread`。
+`named_owner_thread` 可以覆盖本轮 confirmation workflow；正式复现结论、best 复核和 promotion-facing 结论必须回到 `agent_summary.md`、result、quality 和 artifact evidence。跨 workflow 连续追踪时才启用 `persistent_thread`。
 
 本文件用于 version-level confirmation。重新复现用于验证已有 baseline 或版本级结果是否可信。
 
 如果确认对象是某个 module trial 的 `best_attempt_id`，使用 `module_trial_protocol.md` 的
 trial-internal clean `confirmation`，写入该 trial 的 `ATTEMPTS.md` 和
 `attempts/ATTEMPT-xxx/`，不写入 `experiments/vX/confirmation/`。
 
 ## 启用角色
 
 ```text
 Coordinator
 Runner
diff --git a/docs/workflow/agents/by_experiment/innovation/agents/README.md b/docs/workflow/agents/by_experiment/innovation/agents/README.md
index 8770db8..0973cbb 100644
--- a/docs/workflow/agents/by_experiment/innovation/agents/README.md
+++ b/docs/workflow/agents/by_experiment/innovation/agents/README.md
@@ -26,26 +26,26 @@ Coordinator
   -> Runner
   -> Review 3: Log Analyst + Quality Checker + Result Analyst + Reviewer
   -> Coordinator
 ```
 
 ## 关键规则
 
 - 只读取 `idea_tree/versions/<base_version>.md` 中已选中的 idea。
 - 不从总创意表直接启动 trial。
 - 只要 idea / 创新 / module trial 会落成代码改动，必须遵守
   `docs/workflow/protocols/innovation_code_review_protocol.md`。
 - 本类任务默认 `activation_mode: real_multi_agent`，不得用单 agent 顺序执行冒充真实多 agents。
-- 本类任务默认 `agent_instance_mode: temporary_subagent`、`lifecycle: workflow_scoped`；Reader/Planner、Interface Checker、Quality Checker、Result Analyst、Reviewer 等角色必须保留独立上下文。
-- 临时 sub-agent 必须加载对应长期角色的 `profile.md`、`memory.md` 和本文件，并把结论写入 review 文件、`agent_summary.md`、issues 或 memory。跨 workflow 连续追踪时才启用 `persistent_thread`。
+- 本类任务默认 `agent_instance_mode: named_owner_thread`、`lifecycle: workflow_scoped`；Reader/Planner、Interface Checker、Quality Checker、Result Analyst、Reviewer 等角色必须保留独立上下文。
+- 命名线程 必须加载对应长期角色的 `profile.md`、`memory.md` 和本文件，并把结论写入 review 文件、`agent_summary.md`、issues 或 memory。跨 workflow 连续追踪时才启用 `persistent_thread`。
 - Review 0 产出 `idea_intent_check.md`，确认 source intent 和 hypothesis。
 - Review 1 产出 `interface_precheck.md`，在写代码前确认接口设计。
 - Review 2 产出 `review_round_1.md`，在 Runner 前检查 code diff。
 - Review 3 产出 `review_round_2.md`，在结果入账、best 或 promotion 前检查证据。
 - Implementer 只改当前 trial 代码路径。
 - Interface Checker 必须检查 off switch、shape、loss、eval、logits、label mapping、seen/unseen split 和 class order。
 - Runner 串行运行。
 - Runner 只写 Warehouse raw artifacts，GitHub 只保存 manifest/result/quality/code.diff 等轻量证据。
 - Reviewer 独立检查污染、遗漏和误判。
 - Coordinator 必须写 `agent_summary.md`；Reviewer 或长报告可进入 Warehouse，由 GitHub 引用 artifact id。
 - 失败 trial 保留证据，不合并失败代码。
 - `trial_decision: promote` 且 `promotion_decision: promote` 时，转交 promotion agents。
diff --git a/docs/workflow/agents/by_experiment/promotion/agents/README.md b/docs/workflow/agents/by_experiment/promotion/agents/README.md
index 2339e5e..d59ff10 100644
--- a/docs/workflow/agents/by_experiment/promotion/agents/README.md
+++ b/docs/workflow/agents/by_experiment/promotion/agents/README.md
@@ -1,20 +1,20 @@
 # Promotion Agents
 
 Promotion agents 在实验记录已经写出 `promotion_decision: promote`、`promote_to: vX`、
 `evidence_level: baseline_grade` 和 `confirmation_status: confirmed` 后启动。
 
 Promotion 必须保留 `agent_summary.md`，记录 Quality Checker、Interface Checker、Result Analyst 和 Reviewer 的准入结论。长报告放 Warehouse，GitHub 只保存摘要和 artifact id。
 
-Promotion 默认使用 `real_multi_agent` + workflow-scoped `temporary_subagent`。最终通过结论必须写入 `agent_summary.md`、quality、result/promotion evidence 和 version ledger；跨 workflow 连续追踪时才启用 `persistent_thread`。
+Promotion 默认使用 `real_multi_agent` + workflow-scoped `named_owner_thread`。最终通过结论必须写入 `agent_summary.md`、quality、result/promotion evidence 和 version ledger；跨 workflow 连续追踪时才启用 `persistent_thread`。
 
 ## 启用角色
 
 ```text
 Coordinator
 Quality Checker
 Interface Checker
 Result Analyst
 Reviewer
 ```
 
 ## 编排
diff --git a/docs/workflow/agents/by_experiment/tune/agents/README.md b/docs/workflow/agents/by_experiment/tune/agents/README.md
index 1ea1ef7..7c3e710 100644
--- a/docs/workflow/agents/by_experiment/tune/agents/README.md
+++ b/docs/workflow/agents/by_experiment/tune/agents/README.md
@@ -1,21 +1,21 @@
 # Tune Agents
 
 ## 默认模式更新
 
-正式 tune run 默认使用 `real_multi_agent` + workflow-scoped `temporary_subagent`。Reader/Planner、Runner、Log Analyst、Quality Checker、Result Analyst 必须按角色隔离上下文；Runner 仍然串行。
+正式 tune run 默认使用 `real_multi_agent` + workflow-scoped `named_owner_thread`。Reader/Planner、Runner、Log Analyst、Quality Checker、Result Analyst 必须按角色隔离上下文；Runner 仍然串行。
 
 `role_only` 只允许用于训练前最多 3 个候选建议、纯配置查看，或明确不登记正式证据的 debug/smoke。
 
-`temporary_subagent` 可以覆盖本轮 tune workflow；正式结果解释、best 候选判断和 promotion-facing 结论必须回到 `agent_summary.md`、result、quality 和 artifact evidence。跨 workflow 连续追踪时才启用 `persistent_thread`。
+`named_owner_thread` 可以覆盖本轮 tune workflow；正式结果解释、best 候选判断和 promotion-facing 结论必须回到 `agent_summary.md`、result、quality 和 artifact evidence。跨 workflow 连续追踪时才启用 `persistent_thread`。
 
 本文件用于 version-level tune。调参只改变正式 baseline `vX` 的参数，不改变模型结构。
 训练串行，一次只跑一个 Runner。
 
 如果调的是某个 module trial 内部的 attempt 参数，例如 heads、ratio、dropout、seed，
 使用 `module_trial_protocol.md` 的 trial-internal `param_tune`，写入该 trial 的
 `ATTEMPTS.md` 和 `attempts/ATTEMPT-xxx/`，不使用本 version-level tune agent 编排。
 
 ## 启用角色
 
 ```text
 Coordinator
diff --git a/docs/workflow/agents/long_term_memory.md b/docs/workflow/agents/long_term_memory.md
index 67ca8dd..177cab8 100644
--- a/docs/workflow/agents/long_term_memory.md
+++ b/docs/workflow/agents/long_term_memory.md
@@ -11,41 +11,41 @@
 ```text
 shared_roles/<role>/profile.md
 shared_roles/<role>/memory.md
 by_experiment/<task_type>/agents/README.md
 agent_summary.md
 review_round_*.md
 docs/workflow/archive/issues/YYYY-MM-DD-*.md
 ```
 
 运行期 agent 实例可以是：
 
 ```text
-temporary_subagent   # 本轮 workflow / campaign 的活上下文
+named_owner_thread   # 本轮 workflow / campaign 的活上下文
 persistent_thread    # 跨 workflow 的活上下文，可选
 role_only            # 主 agent 按角色清单执行，没有独立活上下文
 ```
 
-`temporary_subagent` 可以在整个 workflow 或 campaign 阶段内持续存在。它不是“短到只能做一次性检查”的工具，而是本轮独立上下文。
+`named_owner_thread` 可以在整个 workflow 或 campaign 阶段内持续存在。它不是“短到只能做一次性检查”的工具，而是本轮独立上下文。
 
 `persistent_thread` 负责跨 workflow 保留角色自己的连续对话经验和可见追踪过程，但它可能压缩、漂移或丢失局部细节，所以不能单独作为正式证据。
 
 进入 `result.yaml`、`quality_check.md`、promotion 证据或正式结论前，所有 memory/thread/context-derived fact 都必须回到当前 repo、Research、Warehouse artifact 或日志验证。
 
 正式 `real_multi_agent` 默认使用：
 
 ```yaml
 agents:
   activation_mode: real_multi_agent
-  agent_instance_mode: temporary_subagent
+  agent_instance_mode: named_owner_thread
   lifecycle: workflow_scoped
 ```
 
 长周期 autonomous research campaign 可以把 `lifecycle` 写成 `campaign_scoped`。只有跨多个 workflow 的角色才使用：
 
 ```yaml
 agents:
   agent_instance_mode: persistent_thread
   lifecycle: cross_workflow
 ```
 
 ## 每个角色的长期文件
@@ -84,49 +84,49 @@ Coordinator 激活某个角色时，必须让该角色读取或显式接收：
 2. shared_roles/<role>/memory.md
 3. by_experiment/<task_type>/agents/README.md
 4. docs/workflow/archive/issues/README.md 和最近相关问题文档
 5. 当前 task start card
 6. 如启用 persistent_thread，则提供 thread id / visible label
 ```
 
 真实多 agent 下，Coordinator 必须在 sub-agent 任务说明里写明这些输入文件，不能假设 sub-agent 自动知道主 agent 的隐藏上下文。
 
 Task Start Card 和 Agent Summary 必须记录：
 
 ```text
-agent_instance_mode: temporary_subagent | persistent_thread | role_only
+agent_instance_mode: named_owner_thread | persistent_thread | role_only
 lifecycle: workflow_scoped | campaign_scoped | cross_workflow | role_only
 persistent_thread_id: <id/label> 或 not_used
 persistent_thread_reused: yes | no | not_applicable
-temporary_subagent_reason:
+named_thread_reason:
 output_locations:
 ```
 
 ## 记忆写回规则
 
 每次任务结束时，Coordinator 检查是否需要写回长期记忆：
 
 | 触发 | 写入位置 |
 |---|---|
 | 本次具体问题、失败、修复 | `docs/workflow/archive/issues/YYYY-MM-DD-*.md` |
 | 某角色反复犯同类错误 | `shared_roles/<role>/memory.md` |
 | 多角色共同边界问题 | `docs/workflow/protocols/agent_orchestration.md` 或 `agent_report_policy.md` |
 | 重复后处理动作 | `workflow/gtpj_workflow.py` helper 或 sync check |
 
 规则：
 
 - 新问题出现 1 次，先写 issue 或本次 `agent_summary.md`。
 - 同类问题出现 2 次，写入对应角色 memory。
 - 同类手工后处理出现 3 次，升级成 helper 或自动校验。
-- 临时 agent 关闭前必须把可复用发现写回上述位置之一。
+- 命名线程 关闭前必须把可复用发现写回上述位置之一。
 
 ## 证据边界
 
 `memory.md` 是提醒和检查清单，不是实验事实源。进入正式结论前仍必须验证：
 
 ```text
 当前 repo 文件
 commit / tag
 config / manifest / result / quality_check
 Warehouse artifact
 Research source review
 server batch_status / logs
@@ -134,14 +134,14 @@ server batch_status / logs
 
 未验证的 memory-derived fact、persistent-thread-derived fact 或 temporary-context-derived fact 不能写入
 `result.yaml`、`quality_check.md`、promotion 证据或正式结论。
 
 ## 自动对齐
 
 长期 agent 体系需要被 sync check 覆盖：
 
 - GitHub `docs/workflow/agents/` 中每个角色都有 `profile.md` 和 `memory.md`。
 - 本地 `gtpj-workflow` skill 镜像这些文件。
 - Task Start Card 和 Agent Summary 记录实际读取了哪些 profile / memory 文件。
 - 如果使用 persistent thread，记录 thread id 或 visible label。
-- 如果使用 workflow-scoped temporary agents，记录 lifecycle、independence scope 和 output locations。
+- 如果使用 workflow-scoped named threads，记录 lifecycle、independence scope 和 output locations。
 - 如果 GitHub 和本地 skill 不一致，GitHub 为准，并阻断正式实验或先同步 skill 镜像。
diff --git a/docs/workflow/core/AGENT_RUNTIME_HARD_GATE.md b/docs/workflow/core/AGENT_RUNTIME_HARD_GATE.md
index e9e2c69..bbd6e8d 100644
--- a/docs/workflow/core/AGENT_RUNTIME_HARD_GATE.md
+++ b/docs/workflow/core/AGENT_RUNTIME_HARD_GATE.md
@@ -1,294 +1,248 @@
 # Agent Runtime Hard Gate
 
-本文件是 GTPJ workflow-v2 的启动闸机。它解决一个具体问题：正式实验不能由
-Coordinator 单窗口代办所有角色后直接启动 Runner。
+本文件是 GTPJ workflow-v2 的正式 Runner 启动闸机。它解决一个具体问题：正式实验不能由 Coordinator 单窗口代办所有角色，也不能再依赖旧 UI 临时 agent 面板。
 
 ## 1. 核心规则
 
-只要一次任务会启动真实 Runner、登记正式 attempt/result、选择 best、安排 repeat、
-影响下一轮高成本实验或进入 promotion 判断，就必须先通过 agent runtime hard gate。
+只要一次任务会启动真实 Runner、登记正式 attempt/result、选择 best、安排 repeat、影响下一轮高成本实验或进入 promotion 判断，就必须先通过 agent runtime hard gate。
 
 ```text
-没有真实右侧临时 agents -> 不准启动正式 Runner。
-没有独立 agent 输出 -> 不准 apply advance transition。
+没有左侧命名 Codex 线程 -> 不准启动正式 Runner。
+没有独立线程输出 -> 不准 apply advance transition。
 没有 pre-run allow/check -> 不准冻结并启动服务器 batch。
 没有 owner 可见监控流 -> 不准声称 workflow 全程接管。
 ```
 
-状态机只记录证据迁移，不能替代 agents。Runner 只执行训练，也不能替代 workflow。
-Owner 是默认监控者；正式 Runner 启动后必须持续显示“哪个智能体在做什么”。
+旧 `temporary_subagent` / `spawn_agent` / UI 临时 agent 只允许作为非正式诊断历史，不允许作为新的 formal evidence gate。状态机只记录证据迁移，不能替代 agents。Runner 只执行训练，也不能替代 workflow。
 
 ## 2. 必需启动顺序
 
 正式实验必须按这个顺序执行：
 
 ```text
 1. Coordinator 生成 task start card。
-2. Coordinator 检查真实 multi-agent 工具是否可用。
-3. Coordinator 启动右侧临时 agents，并记录 agent_instance_id。
-4. Planner / Interface / Quality / Runner Monitor 等角色独立输出 allow/block/propose。
+2. Coordinator 确认 owner 允许创建左侧命名 Codex 线程。
+3. Coordinator 为必需角色创建命名线程，标题使用 <subject_id> | <Role Label>。
+4. Planner / Interface / Quality / Runner Monitor 等角色在线程内独立输出 allow/block/propose。
 5. Coordinator 写 agent_runtime.yaml。
 6. 运行 validate-agent-runtime 和 multi-agent-preflight，通过后才允许 pre-run freeze。
 7. Coordinator apply evidence transition。
 8. Runner 生成 frozen batch 并启动服务器。
-9. Coordinator 进入 owner-visible monitor loop，按间隔汇报 agent 活动、batch 状态、证据位置和下一步。
-10. Log / Quality / Result agents 分别审查运行证据。
+9. Coordinator 进入 owner-visible monitor loop，按间隔汇报线程活动、batch 状态、证据位置和下一步。
+10. Log / Quality / Result 线程分别审查运行证据。
 11. Coordinator 写 result、quality、agent_summary 和下一条 transition。
-12. Coordinator 关闭已完成且结论已入账的 agents；右侧栏只保留当前阶段 active agents。
+12. Coordinator 归档已完成且结论已入账的命名线程；左侧栏只保留当前仍 active 的工作线程。
 ```
 
-如果第 3 步没有发生，本轮必须阻断正式 Runner。只有 owner 明确把目标改成非正式
-`debug_smoke` 排障时，才允许另走 debug 路径；该路径不能作为正式 evidence、candidate
-keep、best、confirmation、promotion 或 version 判断依据。
+如果第 3 步没有发生，本轮必须阻断正式 Runner。只有 owner 明确把目标改成非正式 `debug_smoke` 排障时，才允许另走 debug 路径；该路径不能作为正式 evidence、candidate keep、best、confirmation、promotion 或 version 判断依据。
 
 ## 3. Runtime Gate 文件
 
-每个正式 runner start 前必须有一个轻量文件：
+每个正式 Runner start 前必须有一个轻量文件：
 
 ```text
 agent_runtime.yaml
 ```
 
 推荐位置：
 
 ```text
 attempts/ATTEMPT-xxx/agent_runtime.yaml
 experiments/campaigns/CAMP-xxx/agent_runtime.yaml
 ```
 
 最小字段：
 
 ```yaml
 schema_version: gtpj.agent_runtime_gate.v0
 subject_id: ATTEMPT-xxx
 subject_type: attempt
 formal_evidence: true
 activation_mode: real_multi_agent
-agent_instance_mode: temporary_subagent
+agent_instance_mode: named_owner_thread
 lifecycle: workflow_scoped
-ui_visibility: right_sidebar_temporary_agents
+ui_visibility: left_sidebar_named_threads
 tool_support_real_multi_agent_available: true
-spawn_tool: multi_agent_v1.spawn_agent
+thread_management_tool: codex_app.create_thread
 single_agent_execution: false
 runner_start_allowed: true
 formal_runner_allowed: true
 formal_evidence_allowed: true
 owner_monitor_mode: true
 owner_role: monitor
 owner_visible_reporting: true
 report_channel: current_conversation
 report_interval_minutes: 15
 agent_activity_stream: AGENT_ACTIVITY.md
 monitor_handoff_on_pause: required
-right_sidebar_retention_policy: current_stage_active_only
-close_completed_agents_on_stage_end: true
-closed_agents_record: AGENT_ACTIVITY.md
+thread_archive_policy: archive_completed_threads_on_stage_end
+archive_completed_threads_on_stage_end: true
+archived_threads_record: AGENT_ACTIVITY.md
 
-temporary_subagent_ids:
+named_thread_ids:
   runner_monitor: 019...
   interface_checker: 019...
   evidence_quality_checker: 019...
-  result_analyst: 019...
 
-temporary_subagent_display_names:
+named_thread_titles:
   runner_monitor: "ATTEMPT-007 | Runner Monitor"
   interface_checker: "ATTEMPT-007 | Interface Checker"
   evidence_quality_checker: "ATTEMPT-007 | Evidence Quality Checker"
-  result_analyst: "ATTEMPT-007 | Result Analyst"
 
 pre_run_required_checks:
   runner_monitor: allow
   interface_checker: allow
   evidence_quality_checker: allow
 
 agent_instance_status:
   runner_monitor: running
   interface_checker: completed
   evidence_quality_checker: completed
 
 agent_status_refs:
   runner_monitor: AGENT_ACTIVITY.md
   interface_checker: AGENT_ACTIVITY.md
   evidence_quality_checker: AGENT_ACTIVITY.md
 
 agent_output_refs:
   runner_monitor: agent_outputs/runner_monitor.md
   interface_checker: agent_outputs/interface_checker.md
   evidence_quality_checker: agent_outputs/evidence_quality_checker.md
 
 multi_agent_preflight:
-  required_agents_spawned: true
+  required_threads_created: true
   agent_instance_ids_present: true
   agent_status_refs_valid: true
   independent_outputs_present: true
   agent_output_refs_valid: true
   pre_run_allow_checks_passed: true
   agent_runtime_validated: true
+  threads_archivable: true
 
 authority_refs:
   task_start_card: task_start_card.md
   agent_summary: agent_summary.md
   quality_check: quality_check.md
   transitions: TRANSITIONS.jsonl
   agent_activity: AGENT_ACTIVITY.md
 ```
 
-`temporary_subagent_ids` 不能写成 `temporary_subagent`、`not_recorded`、`role_only`、
-`current Codex session` 这类占位文本。必须记录真实实例 id、可见 thread id 或明确的
-subagent id。
+`named_thread_ids` 不能写成 `named_owner_thread`、`temporary_subagent`、`not_recorded`、`role_only`、`current Codex session` 这类占位文本。必须记录真实可见 thread id。
 
-`temporary_subagent_display_names` 必须记录右侧栏实际显示名。显示名使用严格格式：
+`named_thread_titles` 必须记录左侧栏实际线程标题。标题使用严格格式：
 
 ```text
 <subject_id> | <Role Label>
 ```
 
-示例：
+禁止使用与任务无关的随机英文昵称，例如 `Herschel`、`Galileo`、`Feynman`、`Bohr`。标题必须同时说明“属于哪个任务”和“承担哪个角色”；否则 `validate-agent-runtime` 必须阻断正式 Runner。
 
-```text
-ATTEMPT-007 | Runner Monitor
-CONFIRM-20260703-strict-template-rebuild-v5 | Interface Checker
-CAMP-20260704-workflow-v2 | Evidence Quality Checker
-```
-
-禁止使用与任务无关的随机英文昵称，例如 `Herschel`、`Galileo`、`Feynman`、`Bohr`。
-显示名必须同时说明“属于哪个任务”和“承担哪个角色”；否则 `validate-agent-runtime`
-必须阻断正式 Runner。
+## 3.1 分文件复核契约
 
-`agent_activity_stream` 是 owner 可见流程账本。它必须记录：
-
-```text
-时间
-角色名
-agent_instance_id 或执行来源
-当前动作
-证据位置
-下一步
-```
+正式 `real_multi_agent` 不能只记录“有多个 agent”。每个必需角色的输出文件必须包含：
 
-如果 Coordinator 要结束当前主对话，`monitor_handoff_on_pause: required` 表示必须先说明：
-
-```text
-当前状态
-下一次检查命令
-可见监控位置
-跑完后由哪些 agents 接手分析
+```yaml
+role:
+agent_instance_id:
+files_reviewed:
+decision: allow | block | propose
+uncovered_scope:
 ```
 
-`right_sidebar_retention_policy: current_stage_active_only` 表示右侧栏只保留当前阶段还在工作的
-temporary agents。阶段结束或 workflow 结束时，Coordinator 必须在关闭前列出保留/关闭名单，
-确认已完成 agent 的结论已经写入 `agent_summary.md` / `AGENT_ACTIVITY.md` / result /
-quality / issues / memory 等位置，然后关闭不再 active 的 agents。关闭记录写入
-`closed_agents_record`。
+`files_reviewed` 必须列出该角色实际阅读的文件或 artifact。入口规则修改至少要分成三组独立复核：owner 入口文档、runtime/orchestration hard gate、helper 测试与本地 skill 镜像。Coordinator 可以整合结论，但不能把一个 agent 的阅读结果复制给其他角色，也不能用单一上下文冒充分文件复核。
 
 ## 4. allow / block 语义
 
-`pre_run_required_checks` 只允许：
-
-```text
-allow
-pass
-block
-warn
-not_checked
-```
-
-Runner start 之前，所有 pre-run 必需角色必须是 `allow` 或 `pass`。任一 `block`、
-`not_checked` 或缺失，都必须阻断正式 run。
+Runner start 之前，所有 pre-run 必需角色必须是 `allow` 或 `pass`。任一 `block`、`not_checked` 或缺失，都必须阻断正式 run。
 
 最低必需角色族：
 
 ```text
 Runner Monitor
 Evidence Quality Checker / Quality Checker
 Interface Checker（涉及代码、配置、GZSL、评估语义或新模块时必需）
 ```
 
-Log Analyst 和 Result Analyst 可以在 run 后进入，但如果它们的结论影响 best、repeat、
-promotion 或下一轮实验，也必须是独立 agent 输出。
+Log Analyst 和 Result Analyst 可以在 run 后进入，但如果它们的结论影响 best、repeat、promotion 或下一轮实验，也必须是独立线程输出。
 
 ## 5. formal runner 判定
 
 正式 Runner 同时要求：
 
 ```text
 formal_evidence: true
 activation_mode: real_multi_agent
+agent_instance_mode: named_owner_thread
+workflow_mode_pairing: live_multi_agent_monitor
+ui_visibility: left_sidebar_named_threads
 tool_support_real_multi_agent_available: true
 single_agent_execution: false
 runner_start_allowed: true
 formal_runner_allowed: true
 formal_evidence_allowed: true
 multi_agent_preflight 全部为 true
 validate-agent-runtime 通过
 ```
 
-其中 `multi_agent_preflight` 是启动前的机器可读汇总，不替代角色输出。它必须由
-`temporary_subagent_ids`、`agent_instance_status`、`agent_status_refs`、`agent_output_refs`、
-`pre_run_required_checks`、`agent_summary.md`、`quality_check.md`、`AGENT_ACTIVITY.md`
-等文件支撑。
+其中 `multi_agent_preflight` 是启动前的机器可读汇总，不替代角色输出。它必须由 `named_thread_ids`、`named_thread_titles`、`agent_instance_status`、`agent_status_refs`、`agent_output_refs`、`pre_run_required_checks`、`agent_summary.md`、`quality_check.md`、`AGENT_ACTIVITY.md` 等文件支撑。
+
+如果 owner 明确禁止创建线程，但仍要把 detached 服务器训练计入正式 evidence，则允许第二条 formal gate：
+
+```text
+formal_evidence: true
+activation_mode: role_only
+agent_instance_mode: role_only
+formal_runtime_backend: server_detached_role_only
+workflow_mode_pairing: server_frozen_runner
+ui_visibility: current_owner_thread_only
+thread_creation_allowed: false
+formal_runner_allowed: true
+formal_evidence_allowed: true
+sequential_role_preflight 全部为 true
+validate-agent-runtime 通过
+```
+
+这条路径不是 debug/smoke。它要求独立 sequential role outputs、detached server status file、stop 机制和恢复 handoff。
+
+## Live Monitor Gate
 
-Codex 当前可用的真实 sub-agent 工具名是 `multi_agent_v1.spawn_agent`。Python helper
-不能直接查询聊天工具内部的 sandbox 列表；Coordinator 必须把 `spawn_agent` /
-`wait_agent` 返回的 agent id、状态和角色输出写入上述 refs。helper 只承认可读取、
-非空、能关联 role 或 agent id 的本地证据文件。
+`workflow_mode: live_multi_agent_monitor` 必须同时满足：
+
+```text
+agent_instance_mode: named_owner_thread
+ui_visibility: left_sidebar_named_threads
+owner_visible_reporting: true
+current_stage_status: running | closeout_complete
+report_new_completions: true
+monitor_command: monitor-workflow --report-new-completions
+active_named_threads_visible_until_closeout: true
+archive_after_closeout_only: true
+```
+
+Runner 运行期每个新增 completed job 必须通过 `monitor-workflow --report-new-completions` 或等价证据写入 `AGENT_ACTIVITY.md`。如果只能启动服务器 detached runner、不能保持左侧命名线程和逐 job 监控，则必须改走 `server_frozen_runner`，不能把它标成 live multi-agent。
 
 ## 6. 降级规则
 
-如果真实右侧临时 agents 不可用，或者 owner 明确只要 debug/smoke，必须写：
+如果 owner 不允许创建命名线程，或者当前任务只是 debug/smoke，必须写：
 
 ```yaml
 formal_evidence: false
-evidence_level: debug_smoke
 activation_mode: role_only
 agent_instance_mode: role_only
-runner_start_allowed: true
+runner_scope: debug_smoke
+evidence_level: debug_smoke
 formal_runner_allowed: false
 formal_evidence_allowed: false
-eligible_for_keep_best_promotion_confirmation: false
 ```
 
-这种运行只能定位环境、脚本、shape 或速度问题，不能进入 keep / best / confirmation /
-promotion 证据。debug/smoke 跑完后，如果 owner 要正式结论，必须重新建立
-`real_multi_agent` gate 并重跑正式 Runner，不能把 debug 结果补签为正式 evidence。
+debug/smoke 可以帮助排障，但不得升级成正式 attempt 证据。要升级，必须重新走 formal gate：`named_owner_thread` 或 `server_detached_role_only`。
 
-## 7. Helper
+## 7. 收尾归档
 
-正式 runner start 前必须运行：
+阶段结束前运行只读计划：
 
 ```bash
-python workflow/gtpj_workflow.py validate-agent-runtime --path <agent_runtime.yaml>
-python workflow/gtpj_workflow.py multi-agent-preflight --path <agent_runtime.yaml>
 python workflow/gtpj_workflow.py agent-cleanup-plan --path <agent_runtime.yaml>
 ```
 
-动态路由 batch 生成命令必须传入通过校验的 gate：
-
-```bash
-python workflow/gtpj_workflow.py plan-dynamic-routing-batch \
-  --agent-runtime-gate <agent_runtime.yaml> \
-  ...
-```
-
-只有显式 `--debug-smoke` 时可以不传 gate；该 run 自动标为非正式证据。
-
-## 8. 证据等级
-
-| 情况 | 证据等级 |
-|---|---|
-| 右侧临时 agents 已启动，gate 通过，Runner 按 frozen config 执行 | formal evidence |
-| Coordinator 单窗口代办所有角色后启动 Runner | formal evidence blocked; debug_smoke only if owner changes scope |
-| 服务器离线训练但没有 pre-run agent gate | runner evidence only，不是 workflow evidence |
-| 事后补写 agent_summary，但没有原始 agent id 和 allow/check | audit note only |
-
-一句话：状态机是账本，Runner 是执行器，agents 是工作流主体。三者缺一，不能声称完整
-workflow-v2 闭环。状态机能证明“证据状态如何迁移”，但不能证明“谁独立检查过”；这个证明来自
-真实 agents、命名清晰的右侧栏实例和 `agent_runtime.yaml`。
-
-## 9. Agent Cleanup
-
-阶段结束或 workflow 结束前必须按 `docs/workflow/protocols/agent_cleanup_protocol.md` 执行 cleanup。
-
-`agent-cleanup-plan` 只读列出 keep / close / unknown；真正关闭由 Coordinator 按名单调用可用的 close-agent 工具，并把 `closed`、`not_found`、`retained_by_owner` 或 `unknown_ui_agent` 写入 `closed_agents_record`。
-
-重复 agent id 不能代表独立角色。一个 agent id 如果同时承担多个正式角色，必须标记为历史限制或降级，不能作为完整 `real_multi_agent` 证据。
+`agent-cleanup-plan` 只读列出 keep / archive / unknown；真正归档由 Coordinator 使用线程归档能力完成，并把结果写入 `archived_threads_record`。
diff --git a/docs/workflow/core/CHANGELOG.md b/docs/workflow/core/CHANGELOG.md
index 2838db3..97ef117 100644
--- a/docs/workflow/core/CHANGELOG.md
+++ b/docs/workflow/core/CHANGELOG.md
@@ -34,44 +34,44 @@ validate-evidence-routing
 ```
 
 目标不是增加更多文档，而是让状态迁移可机器检查，并让 authority refs 清晰可追踪。
 
 ## workflow-v2 runtime gate
 
 新增正式 Runner 启动硬门：
 
 ```text
 AGENT_RUNTIME_HARD_GATE.md
 agent_runtime.yaml
 validate-agent-runtime
-right_sidebar_temporary_agents
+left_sidebar_named_threads
 ```
 
-正式实验现在要求真实 temporary agents，并在 Runner 启动前记录 `agent_instance_id`
+正式实验现在要求真实 named threads，并在 Runner 启动前记录 `agent_instance_id`
 和 pre-run allow/check。Coordinator 单窗口执行只能算 candidate/debug evidence，
 不是完整 `real_multi_agent` workflow。
 
-## workflow-v2 right-sidebar cleanup
+## workflow-v2 legacy UI-agent cleanup
 
 新增 owner 可见的 agent cleanup 规则：
 
 ```text
-right_sidebar_retention_policy: current_stage_active_only
-close_completed_agents_on_stage_end: true
-closed_agents_record: AGENT_ACTIVITY.md
+thread_archive_policy: archive_completed_threads_on_stage_end
+archive_completed_threads_on_stage_end: true
+archived_threads_record: AGENT_ACTIVITY.md
 ```
 
 在 workflow 或阶段 closeout 时，Coordinator 必须记录 keep/close lists，把已完成 agent
 结论沉淀到 `agent_summary.md` / `AGENT_ACTIVITY.md` / result / quality / issues / memory，
-然后关闭 completed temporary agents。右侧栏应该显示当前 active roles，而不是历史窗口。
+然后归档 completed named threads。左侧栏应该显示当前 active roles，而不是历史窗口。
 
 ## workflow-v2 formal multi-agent preflight
 
 收紧正式 evidence 规则：
 
 ```text
 formal_runner_allowed: true
 formal_evidence_allowed: true
 multi_agent_preflight
 agent_instance_status / agent_status_refs / agent_output_refs
 multi-agent-preflight helper
 ```
diff --git a/docs/workflow/core/QUICK_START.md b/docs/workflow/core/QUICK_START.md
index 36a3f56..338ea67 100644
--- a/docs/workflow/core/QUICK_START.md
+++ b/docs/workflow/core/QUICK_START.md
@@ -1,41 +1,66 @@
 # GTPJ 工作流快速入口
 
 现在的精简入口是：
 
 ```text
 docs/workflow/START_HERE.md
 docs/workflow/WORKFLOW_KERNEL.md
 ```
 
 本文件只作为 owner 人话短语速查表。
 
+## Owner 三句入口
+
+| owner 口令 | 含义 |
+|---|---|
+| `本地正式，干净` | 启动 `live_multi_agent_monitor`；确认侧边栏干净，并授权创建本轮左侧命名 Codex 线程；不启动服务器 runner。 |
+| `开启多agents智能体工作流，开始` / `开启多agents智能体工作流，跑N轮` | 启动 `live_multi_agent_monitor`；不再反复确认 workflow 模式或启动意图；通过硬门后继续创建角色、生成计划并启动对应 runner。 |
+| `服务器冻结，开始` | 启动 `server_frozen_runner`；不创建命名线程，允许走服务器 detached runner。 |
+| `只做本地规划` | 使用 `role_only`；只做本地计划、账本、状态和 debug/smoke，不进入正式证据。 |
+
+如果 owner 只说 `本地正式`，Coordinator 只问：`侧边栏干净吗？回复：干净。`
+
+如果 owner 已经说 `开启多agents智能体工作流`、`开始`、`跑N轮` 或 `做N轮实验`，Coordinator 不得再要求长授权模板，也不得把任务停在“只规划”。只有模式不明、侧边栏未确认且无法验证、硬门失败或安全边界动作，才允许再问一次。
+
+## 通用话入口
+
+| 你可以直接说 | Coordinator 必须做 |
+|---|---|
+| `规划下一轮实验` / `下一轮怎么跑` | 运行 `plan-experiments`，自动读当前 repo、ledger、result/quality 和 runtime context，输出三张规划表。 |
+| `批量规划50轮实验` / `给我规划50轮` | 运行 `plan-experiments --max-jobs 50`；只规划，不启动 Runner。 |
+| `规划10创新+100调参` / `跑10创新+100调参` | 解析成 mixed campaign workstreams，先出规划表，再进入 campaign gate。 |
+| `按这个计划开多agents工作流` | 解释为 `live_multi_agent_monitor`；通过 agent_runtime 和 preflight 后才能启动正式 Runner。 |
+| `按这个计划服务器冻结跑` | 解释为 `server_frozen_runner`；训练运行期不创建命名线程，走服务器 detached gate。若涉及代码/helper/template 改动，先完成代码审核门。 |
+
+代码审核不被 `server_frozen_runner` 豁免：改代码、workflow、helper、模板或训练配置生成逻辑时，必须先切专用代码审核分支，再做命名 Codex 线程预审、Claude Code 只读审核、机器验证和 `validate-ai-cross-review`。
+
 | 用户短语 | 路由 |
 |---|---|
 | `汇报`, `查状态` | 只读状态检查。除非明确要求，不写 evidence。 |
 | `读论文`, `找创新点` | 论文读取 / idea discovery。 |
 | `基于 vX 从论文开始做实验`, `论文到实验闭环` | 论文读取 -> idea_tree -> module trial 的桥接闭环；缺 `vX` 时不能开 trial。使用 `playbooks/paper_to_experiment.md`。 |
 | `调参` | 调参 Tune。使用 `playbooks/tune.md`。 |
 | `消融` | 消融 Ablation。使用 `playbooks/ablation.md`。 |
 | `复现`, `确认结果` | 复现确认 Confirmation。使用 `playbooks/confirmation.md`。 |
 | `开新模块`, `试这个想法` | 创新 / module trial。使用 `playbooks/innovation.md`。 |
 | `升版本` | 升版门 Promotion gate。使用 `playbooks/promotion.md`。 |
 | `跑10创新+100调参` | 混合实验 campaign。使用 `playbooks/mixed_campaign.md`。 |
 | `全自动研究campaign` | 全自动研究 campaign。使用 `playbooks/autonomous_campaign.md`。 |
 
 正式任务默认 agent 模式：
 
 ```yaml
 activation_mode: real_multi_agent
-agent_instance_mode: temporary_subagent
+agent_instance_mode: named_owner_thread
 lifecycle: workflow_scoped
 ```
 
 长期 agent 是文件支撑的角色身份和累积证据，不等于必须常驻的聊天窗口。
 
 `persistent_thread` 是可选活上下文，适合可见的长周期监控，但不能替代文件、日志、result、quality check 或 Warehouse artifact。
 
 正式写入或运行前，先按 `START_HERE.md` 输出启动摘要；需要正式证据时再填写完整 task card。
 
 baseline 复现状态仍然是硬门。状态比较、best 选择、复现确认、升版、tag/version 表述前，必须运行或记录：
 
 ```bash
diff --git a/docs/workflow/core/TASK_START_CARD.md b/docs/workflow/core/TASK_START_CARD.md
index 195b1cd..c126aa1 100644
--- a/docs/workflow/core/TASK_START_CARD.md
+++ b/docs/workflow/core/TASK_START_CARD.md
@@ -1,55 +1,63 @@
 # Task Start Card
 
+启动卡必须显式写 `workflow_mode`，只能是：
+- `live_multi_agent_monitor`：动态多 agents 监控工作流，要求 `activation_mode: real_multi_agent`、`agent_instance_mode: named_owner_thread`。
+- `server_frozen_runner`：本地规划、冻结计划、服务器 detached 训练工作流，要求 `activation_mode: role_only`、`formal_runtime_backend: server_detached_role_only`、`thread_creation_allowed: false`。
+
+如果 owner 只说“用工作流”，Coordinator 必须先确认是哪一种；不能默认把任务冻结到服务器跑，也不能自动创建命名线程。
+
+如果 owner 已经说“开启多agents智能体工作流”“多agents智能体工作流，开始”“跑N轮”或“做N轮实验”，启动卡必须直接写 `workflow_mode: live_multi_agent_monitor`，不得反复确认 workflow 模式或启动意图。只有模式冲突、侧边栏干净状态缺失且无法验证、硬门失败或安全边界动作，才允许再问一次。包含“开始/跑N轮/做N轮实验”的请求视为执行授权；通过 hard gate 后必须继续到 runner 计划和启动动作，而不是停在 planning gate。
+
 ## 默认真实多 Agent 策略
 
 启动卡默认应为真实实验写：
 
 ```yaml
 agents:
   activation_mode: real_multi_agent
-  agent_instance_mode: temporary_subagent
+  agent_instance_mode: named_owner_thread
   lifecycle: workflow_scoped
   formal_runner_allowed: true
   formal_evidence_allowed: true
   owner_monitor_mode: true
   owner_role: monitor
 ```
 
 原因是不同角色必须拥有独立上下文，避免规划、执行、日志解析、质量检查、结果解释和复核互相污染。
-`temporary_subagent` 在这里不是“一次性几分钟工具”，而是本轮 workflow / campaign 的活上下文。
+`named_owner_thread` 在这里不是“一次性几分钟工具”，而是本轮 workflow / campaign 的活上下文。
 `persistent_thread` 只在角色需要跨多个 workflow 连续追踪、owner 明确要求可见长期线程，或长周期 campaign 的 Coordinator/Monitor 需要跨天连续上下文时启用。
 
 只有以下场景允许 `role_only`：
 
 - 纯只读解释、状态检查或配置查看；
 - 训练前候选 triage，且不启动 Runner、不登记正式证据；
 - 不改变结论的机械账本格式整理；
 - debug/smoke，且输出明确不作为 keep、best、promotion 或 confirmation evidence。
 
 任何真实实验运行、attempt 证据登记、正式结果解释、best 选择、promotion 准备、版本判断或下一轮高成本实验决策，都必须使用 `real_multi_agent`。Runner 仍然串行；并行的是只读或复核角色。
 
 如果真实 sub-agent 工具不可用，而任务需要正式证据，启动卡必须阻断。只有 owner
 明确把目标改成非正式 debug/smoke 排障时，才允许另走 `formal_evidence: false` 路径；
 不能用 `role_only_with_independent_sequential_review` 冒充 `real_multi_agent`。
 
 正式 Runner 启动前必须有 `docs/workflow/core/AGENT_RUNTIME_HARD_GATE.md` 定义的
 `agent_runtime.yaml`，并通过：
 
 ```bash
 python workflow/gtpj_workflow.py validate-agent-runtime --path <agent_runtime.yaml>
 python workflow/gtpj_workflow.py multi-agent-preflight --path <agent_runtime.yaml>
 ```
 
-如果没有真实右侧临时 agents、没有 `temporary_subagents.instances`、没有 pre-run allow/check，
+如果没有真实左侧命名 Codex 线程、没有 `named_threads.instances`、没有 pre-run allow/check，
 Runner 必须阻断；状态机账本和服务器离线训练都不能单独算完整 workflow。
 
 Owner 是默认监控者。任何正式 Runner 启动后，Coordinator 必须持续提供 owner 可见汇报，
 不能把“服务器还在跑”当作 owner 已经看见 workflow 过程。每次汇报必须包含：
 
 ```text
 当前阶段
 哪个智能体在做什么
 run/batch 状态
 证据写入位置
 下一步动作
 ```
@@ -192,76 +200,102 @@ inputs:
   dataset:
   seed:
 
 evidence_routing:
   subject_id:
   subject_type:
   hypothesis_id:
   current_state:
   transitions_file: TRANSITIONS.jsonl
   authority_refs:
   next_allowed_transitions:
 
+experiment_planning:
+  required_before_formal_runner: true
+  plan_id:
+  auto_state_scan:
+    repo_state:
+    baseline_repro_status:
+    formal_pending_ledgers:
+    completed_result_quality_refs:
+    runtime_cache_context_only:
+  evidence_summary_table:
+  candidate_decision_table:
+  current_run_plan_table:
+  runner_start_allowed: false until plan accepted and hard gates pass
+
+workflow_mode:
+workflow_mode_reason:
+
 agents:
   activation_mode:
   agent_instance_mode:
   lifecycle:
   runner_scope:
+  formal_runtime_backend:
+  thread_creation_allowed:
   formal_runner_allowed:
   formal_evidence_allowed:
   activation_reason:
   decision_basis:
     fastest_valid_path:
       selected:
       why_fastest:
       why_still_valid:
       skipped_agents:
       parallelized_roles:
       serialized_roles:
       agent_instance_mode:
       persistent_threads:
-      temporary_subagent_reason:
+      named_thread_reason:
   required_roles:
   disabled_roles:
   required_real_agents:
   agent_instance_status:
   agent_status_refs:
   agent_output_refs:
+  role_file_plan:
+    <role_key>:
+      input_refs:
+      files_reviewed_expected:
+      output_ref:
+      not_checked_allowed: false
+      uncovered_scope_policy:
   persistent_threads:
     required:
     thread_ids:
     missing:
     reused:
-  temporary_subagents:
+  named_threads:
     allowed:
     reason:
     debug_only:
     ui_visibility:
     instances:
       runner_monitor:
       interface_checker:
       evidence_quality_checker:
       log_analyst:
       result_analyst:
   single_agent_allowed:
   owner_override:
   agent_runtime_gate:
     path:
     validated:
     validator_command:
     runner_start_allowed:
     formal_runner_allowed:
     formal_evidence_allowed:
     multi_agent_preflight:
-      required_agents_spawned:
+      required_threads_created:
       agent_instance_ids_present:
       agent_status_refs_valid:
       independent_outputs_present:
       agent_output_refs_valid:
       pre_run_allow_checks_passed:
       agent_runtime_validated:
     pre_run_required_checks:
     blocking_issues:
   owner_monitor:
     enabled:
     owner_role: monitor
     report_channel:
@@ -369,29 +403,29 @@ GitHub 结果记录能否找到 Warehouse artifact？
 
 `agents.activation_mode` 只能选择：
 
 ```text
 role_only
 real_multi_agent
 ```
 
 `agents.agent_instance_mode` 只能选择：
 
 ```text
 role_only
-temporary_subagent
+named_owner_thread
 persistent_thread
 ```
 
-正式 `real_multi_agent` 默认使用 workflow-scoped `temporary_subagent`。`persistent_thread` 是跨 workflow 活上下文，用于 owner 明确要求可见长期追踪、跨天 campaign coordinator/monitor，或某角色需要跨多个 workflow 复用连续上下文时。
+正式 `real_multi_agent` 默认使用 workflow-scoped `named_owner_thread`。`persistent_thread` 是跨 workflow 活上下文，用于 owner 明确要求可见长期追踪、跨天 campaign coordinator/monitor，或某角色需要跨多个 workflow 复用连续上下文时。
 
 `agents.lifecycle` 必须选择或描述：
 
 ```text
 role_only
 workflow_scoped
 campaign_scoped
 cross_workflow
 ```
 
 `workflow_scoped` 表示 agent 在本轮 workflow 全程存在；`campaign_scoped` 表示它在一个长周期 campaign 阶段内存在；`cross_workflow` 才要求 persistent thread 或等价长期可见线程。
 
@@ -420,24 +454,26 @@ owner 明确接受 debug/smoke 降级，必须同时写 `formal_evidence: false`
 - 准备写 `promotion_decision: promote`、创建新 `vX` 或打 version tag；
 - 任务需要同时阅读论文、源码、日志和质量证据，且这些输入可以被不同角色独立检查。
 
 允许选择 `role_only` 的情况：
 
 - 只读解释、状态检查、配置查看；
 - 不改代码、不改实验语义的窄范围 rerun / confirmation 准备；
 - 结果只作为 debug/smoke；
 - 只做账本格式整理且不改变实验结论。
 
 如果选择 `role_only`，启动卡必须写明为什么不启用真实多 agents，以及哪些角色由主 agent 代执行。
 
+真实 `real_multi_agent` 的启动卡必须列出分文件复核计划：每个角色负责哪些文件、输出到哪个 `agent_output_refs` 文件、哪些范围未覆盖。缺少 `files_reviewed`、独立输出或未覆盖范围说明时，不能把本轮记为完整多 agents 复核。
+
 `agents.decision_basis.fastest_valid_path` 必须说明本次为什么选择最快合规路径：
 
 - 简单只读、debug/smoke、训练前候选 triage、账本格式整理等任务，可以选择 `role_only`；单 Runner frozen config 如果会进入正式 evidence，仍默认 `real_multi_agent`。
 - 如果 hard gate 或 owner 要求 `real_multi_agent`，默认并行执行只读审查角色，只串行 Implementer、Runner 和 Coordinator 写账本。
 - 被跳过的角色必须写入 `skipped_agents`，并说明跳过后为什么仍然满足 hard gates。
 
 `agents.required_real_agents` 是真实 sub-agent 硬需求角色列表：
 
 - `activation_mode: real_multi_agent` 时，填写必须独立执行的角色列表；
 - `activation_mode: role_only` 时，填写 `[]`；
 - 如果按规则应使用真实多 agents 但工具不可用，填写 `[]`，并在 `tool_support.fallback_mode` 写
   `role_only_with_independent_sequential_review`，同时触发正式阻断；只有 owner 改成
@@ -525,24 +561,30 @@ forward 路径、新 loss 或评估语义，就新开 `TRIAL-002`。
 
 必须记录：
 
 - 这是 version-level confirmation，还是 trial-internal clean confirmation；
 - 要确认的 baseline tag；
 - config；
 - seed；
 - 数据 split、class order、label mapping；
 - 预期对齐的旧结果；
 - 证据等级目标：`debug_smoke`、`quick_local`、`valid_single_run`、`confirmation_grade` 或 `baseline_grade`；
 - `best_observed_H` 和 `confirmed_H` 的当前状态；
 - confirmation target、tolerance 和失败时的降级规则；
+- `repeat_type: exact_repeat`、`original_seed`、`max_attempts: 5`、`max_attempts_hard_cap: true`、`early_stop_on_best_hit: true`、
+  `restore_target_H`、`near_miss_tolerance_H`、`near_miss_not_restored`，并确认不改 seed、不改任何参数；
+- `max_attempts_hard_cap` 表示同一候选无论是否还原成功最多 5 次，5 次未达 `restore_target_H` 时收口为 not restored / near miss；
+- `near_miss_not_restored` 只能说明实验有效果、还有希望；不能写成还原，不能触发 early stop；
+- 若是 `seed_sweep`、`score_search` 或 `multi_seed_stability`，必须写
+  `not_confirmation_evidence: true`，不得登记为复现；
 - 将被锁定的 `run_commit`；
 - 这次 confirmation 是从哪个 `pre-run freeze commit` 启动。
 
 如果是 trial-internal clean confirmation，目标是确认当前 `best_attempt_id`，写入该 trial 的
 `ATTEMPTS.md` 和 `attempts/ATTEMPT-xxx/`。
 
 ### Debug / Smoke
 
 必须记录：
 
 - debug 目标；
 - 是否会产生长期证据；
@@ -558,25 +600,25 @@ forward 路径、新 loss 或评估语义，就新开 `TRIAL-002`。
 - `version_scores.<base_version>`；
 - source idea file；
 - module insertion point；
 - input/output contract；
 - shape invariants；
 - baseline-off switch；
 - trial branch 和 trial tag 计划；
 - attempt 级 `config.yaml` 和 `ATTEMPTS.md` 计划行是否已经冻结到 `pre-run freeze commit`；
 - 本次真实 run 将使用的 `run_commit`。
 - 是否触发 `innovation_code_review_protocol.md`；
 - `idea_intent_check.md`、`interface_precheck.md`、`review_round_1.md`、
   `review_round_2.md` 的计划位置；
-- 临时 agents 是否允许，哪些角色必须由真实独立 agents 执行；
+- 命名线程 是否允许，哪些角色必须由真实独立 agents 执行；
 - Review 0-3 的阻断条件和当前状态。
 
 ### Promotion
 
 必须记录：
 
 - parent version / parent tag；
 - trial code tag；
 - baseline H、trial H、delta H；
 - U/S/ZS、seed、best epoch；
 - 完整 manifest/result/quality/interface evidence；
 - `evidence_level: baseline_grade`；
@@ -589,25 +631,26 @@ forward 路径、新 loss 或评估语义，就新开 `TRIAL-002`。
 ## 5. 启动卡阻断条件
 
 遇到以下情况，先停止，不跑实验：
 
 - 工作区 dirty 且未说明哪些改动属于当前任务；
 - 启动卡没有填写 `agents.activation_mode`、`activation_reason`、`decision_basis`、`single_agent_allowed` 或 `required_real_agents`；
 - 启动卡涉及正式 evidence，却没有填写 `evidence_routing.subject_id`、`subject_type`、`current_state` 或 `authority_refs`；
 - 启动卡需要推进状态，却没有写 `agents.transition_permissions`；
 - 启动卡没有填写 `agents.agent_instance_mode`、`agents.lifecycle`、`required_roles`、`tool_support`、`persistent_threads` 或 `memory_policy`；
 - 按规则应使用 `real_multi_agent`，但启动卡写成 `role_only`；
 - owner 明确要求多 agents，但启动卡没有写 `real_multi_agent`；
 - 正式 evidence、best、promotion 或 owner 明确要求多 agents，但启动卡没有写各角色独立输入、独立输出和持久化位置；
-- 使用 `temporary_subagent` 却没有写 lifecycle、独立输出位置和本轮结束后的 agent_summary / memory / issues 写回规则；
+- 正式 evidence、best、promotion 或 owner 要求多 agents，但缺少各角色 `files_reviewed` / `input_refs` / `agent_output_refs` / 独立输出文件；
+- 使用 `named_owner_thread` 却没有写 lifecycle、独立输出位置和本轮结束后的 agent_summary / memory / issues 写回规则；
 - 工具不可用但任务硬门要求 `real_multi_agent`，却仍试图启动正式 Runner；debug/smoke 只能在 owner 改目标后另走非正式路径；
 - 正式 Runner 启动卡没有 `formal_runner_allowed: true`、`formal_evidence_allowed: true` 和通过的 `multi_agent_preflight`；
 - `agents.activation_mode` 写成了 `role_only_with_independent_sequential_review`；
 - 正式 Runner 启动卡没有 `owner_monitor.enabled: true`、`agent_activity_stream`、
   `report_channel` 或 `handoff_on_pause`；
 - 使用了 memory-derived fact，却没有说明 memory 来源和当前仓库 / artifact 验证方式；
 - 这是一个真实训练 / confirmation / tune / trial run，但工作区不是 clean；
 - 运行前新增了 attempt config、`ATTEMPTS.md`、启动卡或其他预跑账本，但还没有先提交成 `pre-run freeze commit`；
 - 预期运行 commit 不明确，或无法把本次 run 唯一映射到一个冻结后的 `run_commit`；
 - module trial 没有正式 idea；
 - idea 来源是 `unknown` 或 `unverified` 却要开 trial；
 - idea / 创新 / module trial 将改代码，但没有写明
@@ -622,49 +665,51 @@ forward 路径、新 loss 或评估语义，就新开 `TRIAL-002`。
 - raw logs、checkpoint、generated figures 会写进 GitHub；
 - Runner 需要 GPU，但 lock 状态未知；
 - promotion 只看 H 提升，没有完整证据链。
 
 阻断时写成机器可读状态，不要只写一段自然语言：
 
 ```yaml
 status: blocked
 blocked_reason: real_multi_agent_unavailable
 formal_runner_allowed: false
 formal_evidence_allowed: false
 next_action: >
-  use multi_agent_v1.spawn_agent for runner_monitor and evidence_quality_checker,
+  use codex_app.create_thread for runner_monitor and evidence_quality_checker,
   write agent_instance_status / agent_status_refs / agent_output_refs,
   then run python workflow/gtpj_workflow.py multi-agent-preflight --path <agent_runtime.yaml>
 ```
 
 ## 6. 最小开工输出
 
 每次任务启动时，Coordinator 至少输出：
 
 ```text
 任务类型：
 是否进入 idea_tree：
 GitHub 写入：
 本地写入：
 必读协议：
 启用 agents：
 agents.activation_mode：
 agents.activation_reason：
 agents.decision_basis.fastest_valid_path：
 agents.required_roles：
 agents.required_real_agents：
 agents.tool_support：
+分角色文件阅读/输出计划：
 owner_monitor.enabled：
 owner_monitor.report_channel：
 owner_monitor.agent_activity_stream：
 evidence_routing.subject_id：
 evidence_routing.current_state：
 transition_permissions：
 硬门：
 当前阻塞：
+是否需要再次确认及原因：dangerous_action | mode_ambiguous | gate_blocked | none
 pre-run freeze commit：
 run_commit：
 post-run result commit：
 sync_check：
 ```
 
 这段输出就是后续 agent 的共同入口。
diff --git a/docs/workflow/core/TASK_START_MINI.md b/docs/workflow/core/TASK_START_MINI.md
index 34c0945..c83c8e9 100644
--- a/docs/workflow/core/TASK_START_MINI.md
+++ b/docs/workflow/core/TASK_START_MINI.md
@@ -7,56 +7,61 @@ Coordinator 在后台展开；owner 日常只看这些最小字段。
 
 ```bash
 python workflow/gtpj_workflow.py start --phrase "开新模块"
 ```
 
 该命令只打印下面的字段，不写文件、不建分支、不跑训练。
 
 ## 1. Mini 启动卡
 
 ```yaml
 owner_phrase:
 task_type:
+workflow_mode:
 base_version:
 target:
 subject_id:
 evidence_state:
 writes:
 agent_mode:
 agent_instance_mode:
 runner_scope:
 formal_runner_allowed:
 formal_evidence_allowed:
 agent_runtime_gate:
 multi_agent_preflight:
 owner_monitor_mode:
 agent_activity_stream:
 gates:
 blocked_reason:
 next_action:
 ```
 
+`workflow_mode` 必填：`live_multi_agent_monitor` 表示动态多 agents 监控工作流；
+`server_frozen_runner` 表示本地规划、冻结计划、服务器 detached 训练工作流。
+owner 只说“用工作流”但没有说明哪一种时，必须先确认这一项，不能由 Coordinator 猜测。
+
 字段含义：
 
 | 字段 | 含义 |
 |---|---|
 | `owner_phrase` | owner 的原始口令，例如 `开新模块`、`复现`、`试这个：...`。 |
 | `task_type` | Coordinator 路由后的任务类型。 |
 | `base_version` | 默认当前 active baseline；只有 owner 明确指定时才改历史版本。 |
 | `target` | 本次目标，例如 baseline、参数、idea、trial 或候选列表。 |
 | `subject_id` | 本次被路由或检查的对象，例如 `TRIAL-003`、`ATTEMPT-007`、`RUN-...`、`CAMP-...`。 |
 | `evidence_state` | 当前证据成熟度；正式状态必须能由 `TRANSITIONS.jsonl` 派生。 |
 | `writes` | 本次会写哪里；只读任务写 `none`。 |
 | `agent_mode` | `role_only` 或 `real_multi_agent`，附一句为什么。 |
-| `agent_instance_mode` | `role_only`、`temporary_subagent` 或 `persistent_thread`；正式实验默认 workflow-scoped `temporary_subagent`，跨 workflow 连续追踪才启用 `persistent_thread`。 |
+| `agent_instance_mode` | `role_only`、`named_owner_thread` 或 `persistent_thread`；正式实验默认 workflow-scoped `named_owner_thread`，跨 workflow 连续追踪才启用 `persistent_thread`。 |
 | `runner_scope` | `none`、`debug_smoke` 或 `formal_runner`；只有 `formal_runner` 能产出正式实验证据。 |
 | `formal_runner_allowed` | 正式 Runner 是否允许启动；没有真实多 agent preflight 时必须是 `false`。 |
 | `formal_evidence_allowed` | 本轮输出是否允许进入 keep / best / confirmation / promotion / version 判断。 |
 | `agent_runtime_gate` | 正式 Runner 启动前的 `agent_runtime.yaml` 路径和 `validate-agent-runtime` 状态；纯只读或 debug/smoke 写 `not_required`。 |
 | `multi_agent_preflight` | 正式 Runner 启动前必须写 `pass`；缺真实 agent id、独立输出或 allow/pass 时写 `fail`。 |
 | `owner_monitor_mode` | 正式 Runner 必须写 `true`；owner 是监控者，过程必须在当前对话或明确 Monitor 线程可见。 |
 | `agent_activity_stream` | 记录哪个智能体在做什么的活动流文件；纯只读或 debug/smoke 可写 `not_required`。 |
 | `gates` | 本次真正相关的硬门，只列会影响开工的门。 |
 | `blocked_reason` | 如果不能开正式 Runner，写最小阻断原因；不能留空后继续跑正式实验。 |
 | `next_action` | 下一步最小动作；不能把完整流程丢给 owner 填。 |
 
 ## 2. 展开规则
@@ -80,118 +85,130 @@ stop_if
 
 ### 开新模块
 
 ```yaml
 owner_phrase: 开新模块
 task_type: innovation / module trial
 base_version: 当前 active baseline
 target: 下一个 selected ready idea
 subject_id: pending until trial is created
 evidence_state: hypothesis_ready
 writes: idea_tree + experiments/module_trials + Warehouse after run
 agent_mode: real_multi_agent，因为新模块代码改动需要 Review 0-3
-agent_instance_mode: temporary_subagent, lifecycle workflow_scoped
+agent_instance_mode: named_owner_thread, lifecycle workflow_scoped
 runner_scope: formal_runner
 formal_runner_allowed: false until multi_agent_preflight pass
 formal_evidence_allowed: false until formal Runner completes with evidence chain
-agent_runtime_gate: required before Runner; must record right_sidebar_temporary_agents
+agent_runtime_gate: required before Runner; must record left_sidebar_named_threads
 multi_agent_preflight: required before formal Runner
 owner_monitor_mode: true; visible reports must name active agents and actions
 agent_activity_stream: required before formal Runner
 gates: source_status, interface_contract, innovation_code_review, artifact_boundary
 blocked_reason: none after real_multi_agent gate passes; otherwise block formal run
 next_action: read active version idea view and select the highest-priority ready idea
 ```
 
 ### 复现
 
 ```yaml
 owner_phrase: 复现
 task_type: confirmation
 base_version: 当前 active baseline
 target: 当前 baseline 结果
 subject_id: confirmation subject selected after repro-status
 evidence_state: single_run_valid or confirmation target state
 writes: none until owner confirms run and evidence level
 agent_mode: 正式运行用 real_multi_agent；Runner 启动前的准备可以 role_only
-agent_instance_mode: 正式运行用 temporary_subagent；跨 workflow 追踪才用 persistent_thread
+agent_instance_mode: 正式运行用 named_owner_thread；跨 workflow 追踪才用 persistent_thread
 runner_scope: formal_runner if confirmation will enter evidence; none for read-only repro-status
 formal_runner_allowed: false until multi_agent_preflight pass
 formal_evidence_allowed: false until formal Runner and result review pass
 agent_runtime_gate: required before formal rerun; not required for read-only repro-status
 multi_agent_preflight: required before formal rerun
 owner_monitor_mode: true for formal rerun
 agent_activity_stream: required before formal Runner
 gates: baseline_repro_status, metric_semantics, evidence_level, artifact_boundary
 blocked_reason: none for read-only; missing real_multi_agent gate blocks formal rerun
 next_action: run repro-status, then decide quick_local vs formal confirmation target
+confirmation_policy:
+  repeat_type: exact_repeat
+  original_seed: must match source result
+  max_attempts: 5
+  max_attempts_hard_cap: true
+  early_stop_on_best_hit: true
+  restore_target_H: must be reached to count as reproduced
+  near_miss_tolerance_H: default 0.2, records hope only
+  near_miss_not_restored: true
+  seed_sweep_or_multi_seed_stability: not_confirmation_evidence
 ```
 
+同一候选不管是否还原成功，exact repeat 最多 5 次；命中 `restore_target_H` 可提前停止，5 次未命中则收口为 not restored / near miss。
+
 ### 试这个
 
 ```yaml
 owner_phrase: 试这个：把 <机制> 接到 <位置>
 task_type: local heuristic idea or innovation / module trial
 base_version: 当前 active baseline
 target: owner-supplied mechanism
 subject_id: pending until hypothesis/trial registration
 evidence_state: hypothesis_ready if accepted for triage
 writes: Research/idea_tree only if owner asks to register; no code until ready
 agent_mode: 纯 triage 用 role_only；变成代码或正式证据后用 real_multi_agent
-agent_instance_mode: 纯 triage 用 role_only；进入正式证据后用 temporary_subagent
+agent_instance_mode: 纯 triage 用 role_only；进入正式证据后用 named_owner_thread
 runner_scope: none for triage; formal_runner only after gate passes
 formal_runner_allowed: false until real_multi_agent gate passes
 formal_evidence_allowed: false during triage
 agent_runtime_gate: not_required until code or Runner starts
 multi_agent_preflight: not_required during triage; required before formal Runner
 gates: source_status, interface_contract
 blocked_reason: formal run blocked until real_multi_agent gate exists
 next_action: judge whether this is inbox idea, ready idea, or blocked by missing source/scope
 ```
 
 ### 全自动研究 Campaign
 
 ```yaml
 owner_phrase: 全自动研究 campaign
 task_type: autonomous research campaign
 base_version: 当前 active baseline，除非 owner 指定其它版本
 target: workflow-managed source intake, idea discovery, experiments, evidence, final result and code
 subject_id: campaign id after campaign creation
 evidence_state: hypothesis_ready for first accepted subjects
 writes: campaign ledger + idea_tree + experiments + Research + Warehouse
 agent_mode: real_multi_agent，因为 workflow 会调度多类实验并产出最终证据
-agent_instance_mode: temporary_subagent, lifecycle workflow_scoped; persistent_thread optional for cross-workflow coordinator/monitor
+agent_instance_mode: named_owner_thread, lifecycle workflow_scoped; persistent_thread optional for cross-workflow coordinator/monitor
 runner_scope: formal_runner per formal batch
 formal_runner_allowed: false until campaign/workstream/run preflight passes
 formal_evidence_allowed: false for any batch without real_multi_agent evidence chain
 agent_runtime_gate: required for every formal runner-start transition
 multi_agent_preflight: required at campaign level and before every formal Runner batch
 owner_monitor_mode: true; owner watches the campaign, agents write activity updates
 agent_activity_stream: required at campaign level and per formal Runner batch
 gates: source_status, baseline_repro_status, interface_contract, metric_semantics, artifact_boundary, quality_gate, promotion_gate
 blocked_reason: formal batches blocked when real_multi_agent support is absent
 next_action: create campaign brief from sources, evaluation standard, safety boundaries, experiment standard, budget, and deliverables
 ```
 
 ### 任意组合实验
 
 ```yaml
 owner_phrase: 跑10创新+100调参
 task_type: mixed experiment campaign
 base_version: 当前 active baseline，除非 owner 指定其它版本
 target: requested_mix innovation=10, tune=100
 subject_id: campaign id after campaign creation
 evidence_state: campaign planning, then per-task evidence_state
 writes: experiments/campaigns + each workstream's canonical experiment directory + Warehouse
 agent_mode: real_multi_agent，因为多个 workstream 需要隔离规划、运行、分析和质量检查
-agent_instance_mode: temporary_subagent, lifecycle campaign_scoped/workstream_scoped/task_scoped/run_scoped
+agent_instance_mode: named_owner_thread, lifecycle campaign_scoped/workstream_scoped/task_scoped/run_scoped
 runner_scope: formal_runner per formal batch
 formal_runner_allowed: false until campaign/workstream/run preflight passes
 formal_evidence_allowed: false for any batch without real_multi_agent evidence chain
 agent_runtime_gate: required at campaign level and before each formal runner batch
 multi_agent_preflight: required at campaign level and before each formal Runner batch
 owner_monitor_mode: true; no silent server-only run
 agent_activity_stream: required; every report names role, action, evidence, next
 gates: baseline_repro_status, source_status, interface_contract, metric_semantics, artifact_boundary, quality_gate
 blocked_reason: formal batches blocked when real_multi_agent support is absent
 next_action: parse requested_mix, create campaign manifest, build workstreams, and freeze campaign plan before Runner starts
 ```
diff --git a/docs/workflow/core/WORKFLOW_ROUTER.md b/docs/workflow/core/WORKFLOW_ROUTER.md
index 335ba80..09440ee 100644
--- a/docs/workflow/core/WORKFLOW_ROUTER.md
+++ b/docs/workflow/core/WORKFLOW_ROUTER.md
@@ -1,24 +1,24 @@
 # GTPJ Workflow Router
 
 ## 默认 agent 路由
 
 Router 默认把真实实验类任务路由到 `real_multi_agent`，并把正式角色实例路由到 workflow-scoped
-`temporary_subagent`。原因是不同角色共享同一上下文会污染证据和判断，而正式事实必须沉淀到文件和 artifact。
+`named_owner_thread`。如果目标是服务器 detached 连续训练、owner 明确不希望创建线程，允许走第二条正式路径：`role_only + formal_runtime_backend=server_detached_role_only`。无论哪条路径，正式事实都必须沉淀到文件和 artifact。
 
 默认 `real_multi_agent` 的范围包括：真实 Runner、正式 attempt/result/quality 证据、代码或配置语义变化、结果解释、best 选择、promotion、版本判断、论文实验路线或下一轮高成本实验决策。
 
-`role_only` 只允许用于纯只读状态/解释、训练前候选 triage、不改变结论的机械账本格式整理，或 debug/smoke 且结果不进入正式证据。
+`role_only` 默认只允许用于纯只读状态/解释、训练前候选 triage、不改变结论的机械账本格式整理，或 debug/smoke 且结果不进入正式证据。唯一正式例外是 `server_detached_role_only`：它要求独立 sequential role outputs、formal gate 和 detached server monitoring。
 
-`temporary_subagent` 是本轮 workflow / campaign 的活上下文默认形态。`persistent_thread` 只在角色需要跨多个 workflow 连续追踪、owner 明确要求可见长期线程，或当前 campaign 的 Coordinator/Monitor 需要跨天保留连续上下文时启用。无论使用哪种活上下文，正式证据都必须写入 repo、Research、Warehouse、result、quality 和 agent summary。
+`named_owner_thread` 是本轮 workflow / campaign 的活上下文默认形态。`persistent_thread` 只在角色需要跨多个 workflow 连续追踪、owner 明确要求可见长期线程，或当前 campaign 的 Coordinator/Monitor 需要跨天保留连续上下文时启用。若采用 `server_detached_role_only`，则不创建线程，改为 owner 当前线程 + 独立 role outputs + server status files 共同构成 formal gate。无论使用哪种形态，正式证据都必须写入 repo、Research、Warehouse、result、quality 和 agent summary。
 
 本文件是 GTPJ 的总教官。它不替代具体协议，而是在任何任务开始前先做路由判断：
 
 ```text
 用户请求 -> 任务类型 -> 是否进入 idea_tree -> 写入位置 -> 需要读取的协议 -> agents -> gates
 ```
 
 默认范围：本 Router 只服务“跑实验、做创新、复现、消融、调参、debug 和实验结果记账”。
 
 Owner 不需要说“开启动卡”或自己判断任务类型。默认先读 `START_HERE.md`；`QUICK_START.md` 只作为人话短口令备忘。
 Owner 可以只说：
 
@@ -129,24 +129,42 @@ status=owner_activated_unconfirmed -> active code 可以使用，但 baseline-gr
 | 调正式 baseline 的参数、seed、epoch、loss weight | tune | 否 | `experiments/vX/tune/` | Warehouse logs/runs | `experiment_protocol.md` | Coordinator、Runner、Log Analyst、Quality Checker |
 | 对正式 baseline 做关掉/旁路/替换已有模块看贡献 | ablation | 否 | `experiments/vX/ablation/` | Warehouse logs/runs | `experiment_protocol.md`, `code_interface_contract.md` | Implementer、Interface Checker、Runner、Quality Checker |
 | 复现 baseline 或确认某个版本级结果 | confirmation | 否 | `experiments/vX/confirmation/` | Warehouse logs/runs | `experiment_protocol.md` | Runner、Log Analyst、Quality Checker |
 | 调某个 module trial 的参数、头数、ratio、dropout、seed | innovation / module trial；subtype: trial-internal attempt | 已有 idea | `experiments/module_trials/.../TRIAL-xxx/ATTEMPTS.md` + `attempts/ATTEMPT-xxx/` | Warehouse logs/runs | `module_trial_protocol.md`, `code_interface_contract.md` | Coordinator、Runner、Log Analyst、Quality Checker、Result Analyst |
 | 对某个 module trial 做窄消融或 clean confirmation | innovation / module trial；subtype: trial-internal attempt | 已有 idea | `experiments/module_trials/.../TRIAL-xxx/ATTEMPTS.md` + `attempts/ATTEMPT-xxx/` | Warehouse logs/runs | `module_trial_protocol.md`, `code_interface_contract.md` | Coordinator、Interface Checker 视风险、Runner、Log Analyst、Quality Checker、Result Analyst |
 | debug、smoke test、环境验证 | debug / smoke | 否 | 通常不写；若结果要引用，必须转为对应实验目录并标明 `evidence_level: debug_smoke`、`formal_evidence: false` | 可写临时本地输出；长期证据进 Warehouse | `docs/workflow/protocols/experiment_protocol.md` 视情况 | 不得作为有效结果，除非补齐 manifest/result/quality 并重新按正式证据运行 |
 | 加新模块、新结构、新 forward 路径、新 loss 机制，或把 idea/创新落成代码 | innovation / module trial | 是 | `idea_tree/` + `experiments/module_trials/` | Research 长推理，Warehouse 运行证据 | `idea_tree_protocol.md`, `module_trial_protocol.md`, `code_interface_contract.md`, `innovation_code_review_protocol.md` | Reader/Planner、Implementer、Interface Checker、Runner、Quality Checker、Reviewer；强制 `real_multi_agent` 多轮审查 |
 | 结果想成为新 baseline | promotion | 通常已有 idea 或实验来源 | `config/versions/vY.yaml`、`experiments/vY/`、`experiments/VERSION_TREE.md` | Warehouse 证据引用 | `docs/workflow/protocols/promotion.md`, `docs/workflow/protocols/quality_gate.md`, `docs/workflow/protocols/versioning.md` | Coordinator、Quality Checker、Reviewer、Result Analyst |
 | 只切换创意树当前视图 | set-current-version | 使用已有 idea_tree | `idea_tree/idea_tree.json`、`idea_tree/versions/vX.md` | 不写 | `idea_tree_protocol.md` | 不切 main active code |
 | 切换 main 当前运行代码到某版本 | activate-version | 否 | `config/GTPJ_*.yaml` 等 active code/config | 不写 | `versioning.md`, `git_policy.md` | 必须 owner 明确要求 |
 | 创建或查看运行看板状态 | progress dashboard | 否 | 不写长期 GitHub 账本 | `.gtpj_runtime/` | `progress_dashboard.md` | 只读看板，不启动训练 |
 
+## 2.1 正式待跑表格
+
+当 owner 问“有哪些待跑实验”“表格中有没有”时，Coordinator 必须从正式表格回答，而不是从
+`.gtpj_runtime/` 目录数量回答。
+
+| 范围 | 正式表格 | 待跑行由什么决定 | runtime 的作用 |
+|---|---|---|---|
+| 版本级 tune | `experiments/vX/tune/INDEX.md` | `Status` 为 `planned`、`pending`、`pre_run`、`pre_run_gated` 或 `ready_to_run` 的实验行 | 只核对运行包和事件，不新增待跑事实 |
+| 版本级 ablation | `experiments/vX/ablation/INDEX.md` | 同上，且实验类型必须是 ablation | 只核对运行包和事件 |
+| 版本级 confirmation | `experiments/vX/confirmation/INDEX.md` | 同上，且目标必须是 baseline、candidate 或正式 config | 只核对运行包和事件 |
+| module trial 内部 attempt | `experiments/module_trials/.../TRIAL-xxx/ATTEMPTS.md` | attempt 行含 `ATTEMPT-xxx`、run id 或目录，状态是 `planned/pending/pre_run/...` | 只核对 run 是否已启动、完成或失败 |
+| mixed campaign | `experiments/campaigns/.../WORK_ITEMS.md` / `RESULT_INDEX.md` | 只列 work item；每个 work item 必须回指某个 version-level 或 trial-internal 正式表格行 | 只核对调度和 monitor 状态 |
+
+正式待跑的统一判定名为 `formal_pending`。如果 `.gtpj_runtime/batches/<run_id>` 存在，但上面任一正式表格都没有对应行，判为 `orphan_runtime_plan`。`orphan_runtime_plan` 只能作为历史参考、排障证据或重新登记新实验的输入，不能直接续跑，也不能进入 keep / best / confirmation / promotion。
+
+debug/smoke 不进入正式待跑表。若必须长期保留，只能写成 `evidence_level: debug_smoke`、
+`formal_evidence: false`，并放在对应实验目录的 debug 记录或 Warehouse 引用里。
+
 ## 3. 路由流程
 
 每个 GTPJ 任务先执行这 9 步：
 
 1. 用一句话复述用户请求。
 2. 从任务分类表选择一个主类型；如果请求混合多个类型，拆成多个阶段。
 3. 判断是否进入 `idea_tree/`。
 4. 判断写入位置：GitHub、Research、Warehouse 或 `.gtpj_runtime/`。
 5. 判断是否需要 Research-GitHub-Warehouse 联动更新，以及哪个目录先写、哪个目录只写引用。
 6. 读取该类型必读协议。
 7. 选择 agents 和并行/串行边界。
 8. 做 preflight：分支、dirty 状态、base version、路径、GPU lock、远端是否需要核对。
@@ -277,25 +295,25 @@ Paper intake 的细化流程见 `docs/workflow/protocols/paper_intake.md`。论
 | autonomous research campaign | Coordinator、Source Reader、Idea Planner、Runner Monitor、Log Metric Parser、Result Comparator、Evidence Quality Checker；按阶段加 Runner、Implementer、Interface Checker、Reviewer、Promotion Manager |
 | mixed experiment campaign | Workflow Coordinator、Campaign Planner、Runner Monitor、Result Comparator、Evidence Quality Checker、Warehouse Registrar；按 workstream 加 Innovation/Tune/Ablation/Confirmation roles |
 | tune | Coordinator、Reader/Planner、Runner、Log Analyst、Quality Checker、Result Analyst |
 | ablation | Coordinator、Reader/Planner、Implementer、Interface Checker、Runner、Log Analyst、Quality Checker、Result Analyst |
 | confirmation | Coordinator、Runner、Log Analyst、Quality Checker、Result Analyst |
 | innovation / module trial | Coordinator、Reader/Planner、Implementer、Interface Checker、Runner、Log Analyst、Quality Checker、Result Analyst、Reviewer |
 | promotion | Coordinator、Quality Checker、Interface Checker、Result Analyst、Reviewer |
 | debug / smoke | Coordinator；必要时 Implementer 或 Runner，但结果默认无效 |
 
 Router 选择 agents 时必须先套用“最快合规路径”：
 
 - 能用 `role_only` 且不违反 hard gates 的任务，不启用 `real_multi_agent`。
-- 必须用 `real_multi_agent` 的任务，默认启动 workflow-scoped temporary agents，并把只读审查角色并行执行，不串行排队等待。
+- 必须用 `real_multi_agent` 的任务，默认启动 workflow-scoped named threads，并把只读审查角色并行执行，不串行排队等待。
 - Runner 串行并持有 GPU lock；同一代码路径只能有一个 Implementer；Coordinator 是最终账本 writer。
 - 被跳过的 agent 必须在启动卡 `agents.decision_basis.fastest_valid_path.skipped_agents` 中说明。
 - 如果启用了 persistent thread，启动卡必须列出 thread id 或可见 label；如果未启用，必须说明状态如何写回 campaign ledger、agent_summary、memory 或 issues。
 
 Runner 串行。多个 agents 可以并行读文档、审查和分析，但同一代码路径只能有一个 writer。
 `Experiment Runner` 是实际启动训练命令的运行者；`Runner Monitor` 是服务器/GPU/队列/失败隔离监控者。小规模任务可由同一 Runner family 承担，但启动卡和 summary 必须写清楚显示名、`role_key` 和职责。
 
 ## 8. 强制阻断
 
 以下情况 Router 必须阻断继续执行：
 
 - 当前动作试图 push、发布、删除远端或改写历史，但用户未授权。
diff --git a/docs/workflow/core/WORKFLOW_VERSION.md b/docs/workflow/core/WORKFLOW_VERSION.md
index 2b82abd..a9cc08a 100644
--- a/docs/workflow/core/WORKFLOW_VERSION.md
+++ b/docs/workflow/core/WORKFLOW_VERSION.md
@@ -38,20 +38,20 @@ Runtime gate layer:
 
 ```text
 AGENT_RUNTIME_HARD_GATE.md
 agent_runtime.yaml
 validate-agent-runtime
 multi-agent-preflight
 formal_runner_allowed
 formal_evidence_allowed
 multi_agent_preflight
 agent_instance_status
 agent_status_refs
 agent_output_refs
-right_sidebar_temporary_agents
-right_sidebar_retention_policy: current_stage_active_only
-close_completed_agents_on_stage_end
+left_sidebar_named_threads
+thread_archive_policy: archive_completed_threads_on_stage_end
+archive_completed_threads_on_stage_end
 ```
 
 The evidence state machine records state changes. The agent runtime gate decides whether
 a formal Runner is allowed to start and whether the owner-visible right sidebar stays
 limited to the current active roles.
diff --git a/docs/workflow/playbooks/ablation.md b/docs/workflow/playbooks/ablation.md
index 45b90c8..b9f99bd 100644
--- a/docs/workflow/playbooks/ablation.md
+++ b/docs/workflow/playbooks/ablation.md
@@ -1,15 +1,16 @@
 # 执行卡：消融 Ablation
 
-用于移除、替换、关闭或隔离某个组件。
+用于移除、替换、关闭或隔离既有组件。普通消融不新增方法模块；如果需要新增或改写
+module、forward、loss、eval、data view 或接口语义，必须改走 innovation / module trial。
 
 ## 必读
 
 ```text
 START_HERE.md
 WORKFLOW_KERNEL.md
 docs/workflow/reference/GZSL_HARD_RULES.md
 docs/workflow/core/AGENT_RUNTIME_HARD_GATE.md
 docs/workflow/protocols/experiment_protocol.md
 docs/workflow/protocols/code_interface_contract.md
 产生 raw artifact 时读 docs/workflow/protocols/ARTIFACT_REGISTRATION.md
 ```
@@ -25,26 +26,28 @@ docs/workflow/protocols/module_trial_protocol.md
 正式默认角色：
 
 ```text
 总控 (Coordinator)
 阅读/规划 (Reader/Planner)
 接口检查 (Interface Checker)
 运行监控 (Runner Monitor)
 日志分析 (Log Analyst)
 证据质量检查 (Evidence Quality Checker)
 结果比较 (Result Comparator)
 ```
 
-只有需要改代码时才加入 `实现者 (Implementer)`。
+只有需要添加关闭开关、旁路或空路径时才加入 `实现者 (Implementer)`。如果实现者要新增或改写
+方法模块，本任务必须停止并重新路由为 innovation / module trial。
 
 正式 Runner 启动前必须写 `agent_runtime.yaml` 并通过 `validate-agent-runtime` 和
 `multi-agent-preflight`。
 Interface / Quality / Runner Monitor 没有独立 allow/pass 时，不得把消融结果作为正式证据。
 
 ## 阻断门
 
 - label mapping、seen/unseen split、class order、logits shape 或 metric semantics 不清楚。
 - 消融暗中改变了目标组件之外的东西。
+- 消融需要新增或改写模块代码、forward、loss、eval、data view 或接口语义；这种情况不是普通消融。
 - 要和 unconfirmed baseline 比较，却没有标出这个边界。
 
 ablation 只有在组件贡献证据成立时才能进入 `ablation_supported`；如果消融不支持贡献，必须记录
 `stopped_ablation_not_supported` 或 `rejected` transition。
diff --git a/docs/workflow/playbooks/confirmation.md b/docs/workflow/playbooks/confirmation.md
index 7a6b5d5..763f919 100644
--- a/docs/workflow/playbooks/confirmation.md
+++ b/docs/workflow/playbooks/confirmation.md
@@ -17,66 +17,89 @@ docs/workflow/protocols/quality_gate.md
 
 正式默认角色：
 
 ```text
 总控 (Coordinator)
 运行监控 (Runner Monitor)
 日志分析 (Log Analyst)
 证据质量检查 (Evidence Quality Checker)
 结果比较 (Result Comparator)
 ```
 
 正式 confirmation / rerun 启动 Runner 前，必须写 `agent_runtime.yaml`，记录真实
-右侧临时 agents，并通过 `validate-agent-runtime` 和 `multi-agent-preflight`。否则
+左侧命名 Codex 线程，并通过 `validate-agent-runtime` 和 `multi-agent-preflight`。否则
 confirmation 必须阻断；不能用单窗口 sequential review 生成 confirmed evidence。
 
 ## 复现 / Repeat 类型
 
 必须先声明本轮是哪一种：
 
 ```text
 exact_repeat:
-  固定原始 code commit、config、seed、data/cache、epoch schedule、batch size 和评估口径。
+  固定原始 code commit、config、original_seed、data/cache、epoch schedule、batch size 和评估口径。
+  不允许换 seed，不允许换任何参数。
+  max_attempts: 5
+  max_attempts_hard_cap: true
+  early_stop_on_best_hit: true
+  restore_target_H: 原始结果水平，必须达到才算还原。
+  near_miss_tolerance_H: 默认 0.2；只用于记录接近但未还原。
+  near_miss_not_restored: 接近只能说明实验有效果、还有希望。
   用来回答“原始结果能不能原样再跑出来”。
   只有 exact_repeat 才能叫严格复现。
 
-same_seed_min3:
-  同一个原始 seed 重跑 3 次。
+same_seed_repeat:
+  同一个 original_seed 重跑，最多 5 次，命中即停。
   用来检查非确定性、环境漂移和同配置可重复性。
 
 seed_sweep / score_search:
   主配置固定，但 seed 变化。
-  用来冲分、找 seed 敏感性或观察稳定性；不能叫严格复现，也不能单独作为 confirmed evidence。
+  用来冲分、找 seed 敏感性或观察稳定性；必须写 not_confirmation_evidence: true，不能叫严格复现，也不能单独作为 confirmed evidence。
 
 multi_seed_stability:
   预先声明多个 seed，报告 mean/min/max/range。
-  可作为稳定性证据，但必须和 exact_repeat 区分。
+  可作为稳定性证据，但必须和 exact_repeat 区分，并写 not_confirmation_evidence: true。
 ```
 
 seed 是实验配置的一部分。改变 seed 就不是“同配置严格复现”，只能是
 `seed_sweep`、`score_search` 或 `multi_seed_stability`。
 
-默认 confirmation 跑 3 次，但必须写明 repeat 类型。
+默认 confirmation 必须写明 repeat 类型。正式复现默认 `repeat_type: exact_repeat`、
+`max_attempts: 5`、`max_attempts_hard_cap: true`、`early_stop_on_best_hit: true`。一旦任一 clean run 达到 `restore_target_H`，
+立刻停止后续 pending repeat；无论是否还原成功，同一候选最多 5 次，5 次未达到则收口为 not restored。落入 `near_miss_tolerance_H` 但未达到 `restore_target_H` 时，
+只能写 `near_miss_not_restored`：说明实验有效果、还有希望，不能说还原，不能停止。
 
-如果复现通过：
+如果复现有单次命中：
 
 ```text
+best_hit = true
+best_single_H = best repeat H
+best_observed_H = best repeat H
+结论 = 命中候选 / 继续复现
+```
+
+如果稳定确认也通过：
+
+```text
+stable_confirm = true
+confirmed_H = repeat mean 或协议指定的 confirmed metric
 official single = best repeat
 reported stability = mean / min / max
 promotion_compare_metric = repeat mean / confirmed_H
 ```
 
 不能隐藏较弱 repeat。稳定性属于正式证据的一部分。
 不得只凭 best repeat 做 promotion 或 baseline claim。
 不得把 multi-seed 的最高值写成 exact-repeat confirmed。
+也不得用 mean H 掩盖单次最高命中；回答“有没有复现到”时优先报告 best single，
+回答“能不能 promotion / baseline claim”时再报告 mean/min/max/range。
 
 ## 输出
 
 版本级 confirmation：
 
 ```text
 experiments/vX/confirmation/
 ```
 
 trial 内部 confirmation：
 
 ```text
diff --git a/docs/workflow/playbooks/innovation.md b/docs/workflow/playbooks/innovation.md
index f9b925f..5f6b5ad 100644
--- a/docs/workflow/playbooks/innovation.md
+++ b/docs/workflow/playbooks/innovation.md
@@ -30,25 +30,25 @@ docs/workflow/core/AGENT_RUNTIME_HARD_GATE.md
 阅读/规划 (Reader/Planner)
 实现者 (Implementer)
 接口检查 (Interface Checker)
 运行监控 (Runner Monitor)
 日志分析 (Log Analyst)
 证据质量检查 (Evidence Quality Checker)
 结果比较 (Result Comparator)
 复核者 (Reviewer)
 ```
 
 同一个代码路径只能有一个实现者 (Implementer)。
 
-正式 Runner 启动前必须先启动右侧临时 agents，写 `agent_runtime.yaml`，并通过
+正式 Runner 启动前必须先创建或绑定左侧命名 Codex 线程，写 `agent_runtime.yaml`，并通过
 `validate-agent-runtime` 和 `multi-agent-preflight`。如果只是 Coordinator 单窗口代办
 Review 0-3，本轮不能作为正式 `real_multi_agent` 创新证据。
 
 ## 探索 / 正式分界
 
 探索性 trial 只允许做这些事：
 
 ```text
 idea triage
 接口草图
 debug_smoke
 本地 shape / script / speed probe
@@ -72,25 +72,30 @@ promotion。正式路径必须通过真实 `real_multi_agent` gate；不能把
 
 ```yaml
 upgrade_path:
   exploration_run:
     kept_as: exploration_ref
     evidence_level: debug_smoke
     formal_evidence: false
   formal_rerun_required:
     - real_multi_agent
     - agent_instance_status / agent_status_refs / agent_output_refs
     - Review 1-3
     - frozen config
-    - min3 confirmation when used for confirmed_H or promotion
+    - exact repeat confirmation when used for confirmed_H or promotion:
+      `repeat_type: exact_repeat`, `original_seed`, `max_attempts: 5`,
+      `max_attempts_hard_cap: true`,
+      `early_stop_on_best_hit: true`, `restore_target_H`, `near_miss_tolerance_H`,
+      `near_miss_not_restored`; each candidate has at most 5 exact repeats regardless of success or failure; seed_sweep /
+      multi_seed_stability must be `not_confirmation_evidence: true`
   forbidden:
     - promote exploration run in place
     - rewrite debug_smoke as valid_single_run
     - use sequential review as formal audit
 ```
 
 ## 创新拆解
 
 创新必须按下面层级管理：
 
 ```text
 Paper
@@ -163,14 +168,14 @@ idea_tree/
 experiments/module_trials/<IDEA-ID>/TRIAL-xxx/
 需要长推理时写 GTPJ_Research
 raw logs/checkpoints 写 GTPJ_Warehouse
 ```
 
 ## 阻断门
 
 - 没有有效 idea id 或 owner 接受的 local heuristic。
 - 论文创新要做实验但缺少 owner 明确指定的 base version / base code tag。
 - 没有 `module_source.md` 或没有选择 module template family。
 - interface semantics 不清楚。
 - attempt 改变了实现假设，应该新开 trial。
-- 没有真实右侧临时 agents、没有 `agent_runtime.yaml` 或 `validate-agent-runtime` 未通过。
+- 没有真实左侧命名 Codex 线程、没有 `agent_runtime.yaml` 或 `validate-agent-runtime` 未通过。
 - 正式 multi-agent 支持不可用。owner 只能把本轮改成 debug-only 排障；不能继续正式 trial。
diff --git a/docs/workflow/playbooks/mixed_campaign.md b/docs/workflow/playbooks/mixed_campaign.md
index 826a499..0b212bd 100644
--- a/docs/workflow/playbooks/mixed_campaign.md
+++ b/docs/workflow/playbooks/mixed_campaign.md
@@ -21,29 +21,39 @@ docs/workflow/core/AGENT_RUNTIME_HARD_GATE.md
 
 ## 结构
 
 ```text
 campaign
   -> workstream: innovation / tune / ablation / confirmation / debug
     -> task
       -> run
 ```
 
 不要给每个 run 创建一个永久 agent。
 
-但 campaign / workstream / task 级正式角色必须是真实右侧临时 agents，并在
+但 campaign / workstream / task 级正式角色必须是真实左侧命名 Codex 线程，并在
 `agent_runtime.yaml` 中记录实例 id。没有通过 `validate-agent-runtime` 和
 `multi-agent-preflight` 的 campaign 不能启动正式 Runner；不能用 sequential review
 替代正式 campaign evidence。
 
+生成 campaign manifest、batch 或 runner plan 前，先运行只读规划门：
+
+```bash
+python workflow/gtpj_workflow.py plan-experiments --phrase "<owner 组合口令>"
+```
+
+规划必须根据当前 repo、baseline、正式待跑 ledger 和已完成 result/quality 自动生成
+Evidence Summary、Candidate Decision、Current Run Plan 三张表；`.gtpj_runtime` 只能作
+debug context。
+
 每个 campaign task 必须有：
 
 ```text
 subject_id
 subject_type
 evidence_state
 next_allowed_transitions
 result_ref
 quality_ref
 authority: derived_index_only
 ```
 
@@ -80,30 +90,34 @@ Campaign 规划 (Campaign Planner)
 证据质量检查 (Evidence Quality Checker)
 Warehouse 登记 (Warehouse Registrar)
 ```
 
 再按对应 playbook 加入 workstream 专属角色。
 
 ## 调度规则
 
 总控 (Coordinator) 负责优先级和边界。
 
 运行监控 (Runner Monitor) 负责 GPU/服务器执行和失败隔离。
 
-结果比较 (Result Comparator) 根据 evidence 决定哪些方向需要 3-repeat confirmation。
+结果比较 (Result Comparator) 根据 evidence 决定哪些方向需要 exact-repeat confirmation：
+`repeat_type: exact_repeat`、`original_seed`、`max_attempts: 5`、
+`max_attempts_hard_cap: true`、`early_stop_on_best_hit: true`、`restore_target_H`、`near_miss_tolerance_H`、
+`near_miss_not_restored`。接近但未达到目标只能说明有效果、还有希望，不能说还原；同一候选无论是否还原成功都最多 5 次，5 次未还原不能继续加跑复现。换 seed 的
+`seed_sweep` / `multi_seed_stability` 必须写 `not_confirmation_evidence: true`。
 
 调度按 evidence state machine，不按 run 数硬排：
 
 ```text
-hypothesis_ready -> interface_precheck_passed -> smoke_passed -> single_run_valid -> tune_promising -> ablation_supported -> min3_confirmed
+hypothesis_ready -> interface_precheck_passed -> smoke_passed -> single_run_valid -> tune_promising -> ablation_supported -> exact_repeat_best_hit -> stable_confirmed
 ```
 
 ## 必要 Campaign 汇报
 
 ```text
 请求组合 requested mix
 实际规划 runs
 completed/running/pending/failed
 最佳单次 best single
 进入复现的 top candidates
 confirmed/rejected directions
 下一轮 10-50 run 计划
diff --git a/docs/workflow/playbooks/paper_to_experiment.md b/docs/workflow/playbooks/paper_to_experiment.md
index 3de4820..2637073 100644
--- a/docs/workflow/playbooks/paper_to_experiment.md
+++ b/docs/workflow/playbooks/paper_to_experiment.md
@@ -77,25 +77,25 @@ Paper intake 本身不启动训练，也不直接创建 module trial。
 只有通过正式 IDEA 门、进入 selected queue，并由 owner 批准实验后，才允许走 formal Runner。
 如果 owner 没有明确说“基于 vX 代码开始”，本闭环停在候选创新和版本适配评分，不得默认当前 active version。
 
 ## 阻断门
 
 - 没有 verified source，且 owner 未接受 local heuristic。
 - 没有明确 `source_ref`，或官方代码声明无法反查到本地 clone/失败记录。
 - 缺少 `hypothesis`、`implementation_scope`、`risk` 或当前版本评分。
 - 缺少 owner 明确指定的 `base_version` / `base_code_tag`。
 - idea 未进入 selected queue。
 - 未选择 module template family，或缺少 `module_source.md`。
 - Interface Checker 不能判断接口影响。
-- 正式实验前缺少真实右侧 temporary agents、`agent_runtime.yaml`、preflight 或 cleanup plan。
-- 阶段结束时没有汇报 keep / close / unknown agents，或 completed agents 未关闭并记录 `close_result`。
+- 正式实验前缺少真实左侧命名 Codex 线程、`agent_runtime.yaml`、preflight 或 cleanup plan。
+- 阶段结束时没有汇报 keep / archive / unknown agents，或 completed threads 未归档并记录 `archive_result`。
 
 ## 启动口径
 
 Owner 只说“从论文开始”时，默认先做只读 intake 和候选排序：
 
 ```text
 能不能开工：能做论文读取和候选提取；不能直接训练。
 任务类型：paper -> idea -> module trial closed loop。
 当前最小动作：读取 PAPERS_INDEX/_inbox，列出候选来源和缺口。
 正式实验条件：selected IDEA + owner approval + agent_runtime + preflight + cleanup plan。
 ```
diff --git a/docs/workflow/playbooks/tune.md b/docs/workflow/playbooks/tune.md
index ba46283..03ae821 100644
--- a/docs/workflow/playbooks/tune.md
+++ b/docs/workflow/playbooks/tune.md
@@ -23,25 +23,25 @@ docs/workflow/protocols/module_trial_protocol.md
 
 正式 tune 默认使用 `real_multi_agent`：
 
 ```text
 总控 (Coordinator)
 调参规划 (Tune Planner)
 运行监控 (Runner Monitor)
 日志分析 (Log Analyst)
 证据质量检查 (Evidence Quality Checker)
 结果比较 (Result Comparator)
 ```
 
-正式 Runner 启动前必须写 `agent_runtime.yaml`，记录右侧临时 agents 的真实
+正式 Runner 启动前必须写 `agent_runtime.yaml`，记录左侧命名 Codex 线程的真实
 `agent_instance_id`，并通过 `validate-agent-runtime` 和 `multi-agent-preflight`。
 否则正式 tune 必须阻断。只有 owner 明确把目标改成非正式 `debug_smoke` 排障时，
 才允许继续；该结果不能进入 keep / best / confirmation / promotion。
 
 ## 输出
 
 版本级 tune：
 
 ```text
 experiments/vX/tune/
 ```
 
@@ -49,23 +49,27 @@ trial 内部 tune：
 
 ```text
 experiments/module_trials/.../TRIAL-xxx/ATTEMPTS.md
 experiments/module_trials/.../TRIAL-xxx/attempts/ATTEMPT-xxx/
 ```
 
 raw logs 和 checkpoints 留在 Warehouse。
 
 ## 决策规则
 
 只调参数带来的提升不能开新的 `vX`。
 
-重要 tuned config 必须 3 次 confirmation 后，才能作为正式数据表述。
+重要 tuned config 必须经过 `repeat_type: exact_repeat` 后，才能作为正式数据表述：
+锁定 `original_seed` 和原始配置，`max_attempts: 5`、`max_attempts_hard_cap: true`、`early_stop_on_best_hit: true`，
+并声明 `restore_target_H`、`near_miss_tolerance_H` 和 `near_miss_not_restored`。接近但未达到目标
+只能说明有效果、还有希望，不能说还原；同一候选无论是否还原成功都最多 5 次，5 次未还原不能继续加跑复现。换 seed 的 `seed_sweep` / `multi_seed_stability`
+必须写 `not_confirmation_evidence: true`，只能作为搜索或稳定性诊断。
 
 tune transition 默认只能进入：
 
 ```text
 single_run_valid
 tune_promising
 rerun_required
 rejected
 stopped_no_gain
 ```
diff --git a/docs/workflow/protocols/agent_cleanup_protocol.md b/docs/workflow/protocols/agent_cleanup_protocol.md
index 265ecf1..04dd22a 100644
--- a/docs/workflow/protocols/agent_cleanup_protocol.md
+++ b/docs/workflow/protocols/agent_cleanup_protocol.md
@@ -1,120 +1,144 @@
 # Agent Cleanup Protocol
 
-本协议只解决一个问题：每轮 workflow 或阶段结束后，右侧栏不能堆历史 agent。
+本协议只解决一个问题：每轮 workflow 或阶段结束后，左侧命名 Codex 线程不能变成历史堆积。旧 UI 临时 agent 已不再作为正式范式使用。
 
 ## 1. 目标
 
-右侧栏只显示当前阶段仍在工作的 active agents。历史结论必须回到文件和 artifact，不能靠旧窗口保存。
+左侧栏只保留当前阶段仍在工作的 active 线程。历史结论必须回到文件和 artifact，不能靠旧对话窗口保存。
+
+创建新的 formal named threads 前，Coordinator 必须先问 owner 是否允许，并确认当前左侧栏不会被旧线程混淆。如果 owner 看到历史线程太多，正式 `real_multi_agent` 必须暂停，先整理账本和归档计划。
 
 阶段结束时，Coordinator 必须执行：
 
 ```text
 1. 列出保留名单。
-2. 列出关闭名单。
-3. 确认关闭名单的输出已经写入 agent_summary / AGENT_ACTIVITY / result / quality / issues / memory。
-4. 调用 close_agent 关闭已完成的 temporary agents。
-5. 把关闭结果写回 AGENT_ACTIVITY.md 或 closeout summary。
+2. 列出归档名单。
+3. 确认归档名单的输出已经写入 agent_summary / AGENT_ACTIVITY / result / quality / issues / memory。
+4. 使用线程归档能力归档已完成的 named_owner_thread。
+5. 把归档结果写回 AGENT_ACTIVITY.md 或 closeout summary。
 ```
 
 ## 2. 必须记录的字段
 
-`agent_runtime.yaml` 中每个 temporary agent 至少要能追踪：
+`agent_runtime.yaml` 中每个命名线程至少要能追踪：
 
 ```yaml
-temporary_subagent_ids:
+named_thread_ids:
   runner_monitor: 019...
 
-temporary_subagent_display_names:
+named_thread_titles:
   runner_monitor: "ATTEMPT-005 | Runner Monitor"
 
 agent_instance_status:
   runner_monitor: completed
 
 agent_output_refs:
   runner_monitor: agent_outputs/runner_monitor.md
 
 agent_cleanup:
-  retention_policy: current_stage_active_only
-  close_completed_agents_on_stage_end: true
-  close_command: multi_agent_v1.close_agent
-  close_results_record: AGENT_ACTIVITY.md
+  thread_archive_policy: archive_completed_threads_on_stage_end
+  archive_completed_threads_on_stage_end: true
+  archive_command: codex_app.set_thread_archived
+  archive_results_record: AGENT_ACTIVITY.md
 ```
 
-如果工具返回 `not found`，不能伪造为已关闭，必须记录为：
+如果工具返回 `not_found`，不能伪造为已归档，必须记录为：
 
 ```text
-close_result: not_found
-meaning: repo ledger id is no longer reachable by the current agent tool
+archive_result: not_found
+meaning: repo ledger thread id is no longer reachable by the current thread tool
 ```
 
-## 3. 关闭判定
+## 3. 归档判定
 
 ```text
 running / active / spawned -> 保留
-completed / complete / closed -> 关闭
-missing / failed / unknown / not_found -> 不盲关，先汇报
+completed / complete / closed -> 归档
+missing / failed / unknown / not_found -> 不盲目归档，先汇报
 ```
 
-重复 agent id 不能代表独立角色。一个 agent id 如果同时承担多个正式角色，必须标记为历史限制或降级，不能作为完整 `real_multi_agent` 证据。
+重复 thread id 不能代表独立角色。一个 thread id 如果同时承担多个正式角色，必须标记为历史限制或降级，不能作为完整 `real_multi_agent` 证据。
 
 ## 4. 命名判定
 
-右侧栏临时 agent 显示名不能随便取英文名。正式 runtime 必须使用：
+正式 runtime 必须使用：
 
 ```text
 <subject_id> | <Role Label>
 ```
 
-其中 `subject_id` 是本次 attempt / confirmation / campaign / review pack 的机器可读任务 id，
-`Role Label` 是清晰角色名，例如 `Runner Monitor`、`Interface Checker`、
-`Evidence Quality Checker`、`Result Analyst`。
-
-合法示例：
-
-```text
-ATTEMPT-007 | Runner Monitor
-CONFIRM-20260703-strict-template-rebuild-v5 | Evidence Quality Checker
-DR035-EXACT-REPEAT | Result Comparator
-```
+其中 `subject_id` 是本次 attempt / confirmation / campaign / review pack 的机器可读任务 id，`Role Label` 是清晰角色名，例如 `Runner Monitor`、`Interface Checker`、`Evidence Quality Checker`、`Result Analyst`。
 
 非法示例：
 
 ```text
 Herschel
 Galileo
 Feynman
 Runner
 Quality
 ```
 
 非法原因：看不出属于哪个任务、哪个证据对象，也无法和 `agent_runtime.yaml` 稳定对应。
 
 ## 5. 只读计划命令
 
 阶段结束前先运行：
 
 ```bash
 python workflow/gtpj_workflow.py agent-cleanup-plan --path <agent_runtime.yaml>
 ```
 
-它只输出保留/关闭/未知名单，不会关闭 agent。
+它只输出保留/归档/未知名单，不会归档线程。
 
 ## 6. Owner 可见汇报格式
 
 ```text
 role: Coordinator
 action: agent cleanup
 evidence: agent_runtime.yaml + AGENT_ACTIVITY.md + agent_outputs/
 keep: ...
-close: ...
+archive: ...
 unknown: ...
-next: close completed agents, then write close_result
+next: archive completed threads, then write archive_result
+```
+
+如果 owner 说左侧栏数量和 cleanup plan 不一致，Coordinator 必须说明：
+
+```text
+repo 账本只能识别已记录的 runtime threads；
+当前工具若没有完整 list_threads API，无法权威枚举 UI 中所有历史线程；
+未知 UI thread 需要按标题人工对照后再归档。
 ```
 
-如果 owner 说右侧栏数量和 cleanup plan 不一致，Coordinator 必须说明：
+在这种不一致被解决前，禁止创建新的 formal named threads。否则每次新开正式角色时，旧窗口会继续堆积。
+
+## 7. 旧 UI agent 污染退出规则
+
+如果同时满足下面条件：
 
 ```text
-repo 账本只能识别已记录的 runtime agents；
-当前工具若没有 list_agents API，无法权威枚举 UI 中所有历史窗口；
-未知 UI agent 需要按显示名人工对照后再关闭。
+1. owner 可见 UI 仍有历史临时 agent 或未知命名线程；
+2. UI 没有关闭 / 归档按钮；
+3. 已记录 id 不能被当前工具关闭；
+4. 当前环境没有 list_agents 或按 UI nickname 关闭的工具；
+```
+
+则当前线程必须标记为：
+
+```yaml
+owner_window_status: polluted_by_unknown_ui_agents
+formal_real_multi_agent_allowed: false
+runner_start_allowed: false
+allowed_actions:
+  - read_only_status
+  - repo_ledger_cleanup
+  - handoff_to_new_clean_owner_thread
+blocked_actions:
+  - spawn_agent
+  - formal_runner
+  - confirmation_evidence_start
+  - promotion
 ```
+
+正确处理不是继续尝试在当前线程补 gate，而是开一个干净 owner 线程；新线程仍然必须遵守命名线程 gate，不能重新启用旧 `create_thread` 范式。
diff --git a/docs/workflow/protocols/agent_orchestration.md b/docs/workflow/protocols/agent_orchestration.md
index fde7255..96be431 100644
--- a/docs/workflow/protocols/agent_orchestration.md
+++ b/docs/workflow/protocols/age
```

> focused diff 已截断；需要追查完整上下文时再读取 `02_diff.patch`。

## Untracked Text Snippets


## 未跟踪文件：docs/workflow/reference/GENERAL_GZSL_EXPERIMENT_PROTOCOL.md

```text
# 通用 GZSL 实验规范

本文用于在新电脑或新环境中搭建、运行、评估和记录广义零样本学习实验。结论先行：正式 GZSL 实验必须固定 seen/unseen 类划分、固定类别顺序、训练只使用 seen 图像监督、评估在 seen+unseen 全类别空间竞争，并同时报告 `GZSL-U`、`GZSL-S`、`GZSL-H` 和 `ZSL`。

## 1. 适用范围

本规范适用于 CUB、AWA2、SUN 等标准 GZSL 数据集，也适用于自建数据集。只要任务包含“训练类”和“未见类”，并需要在测试时让 seen 类和 unseen 类共同竞争，就应使用本规范。

术语约定：

- `seen class`：训练阶段有图像和类别标签监督的类别。
- `unseen class`：训练阶段没有图像标签监督的类别。
- `semantic prototype`：属性向量、类别文本、CLIP 文本特征、GPT/VDT 描述等类别语义表示。
- `global label`：数据集原始全局类别编号，评估必须回到这个编号体系。
- `local seen label`：训练 CE loss 可用的 seen 类局部编号，只能用于训练内部，不能替代评估标签。

## 2. 新电脑环境基线

新电脑先做环境记录，再跑实验。每次正式 run 必须保存环境快照。

最小检查项：

```text
操作系统和版本
GPU 型号
NVIDIA driver 版本
CUDA runtime 版本
Python 版本
PyTorch / torchvision / timm / transformers 等关键包版本
当前 Git commit
当前配置文件路径
数据集路径
随机种子
```

Windows PowerShell 可记录：

```powershell
python --version
python -c "import torch; print('torch=', torch.__version__); print('cuda=', torch.version.cuda); print('available=', torch.cuda.is_available()); print('gpu=', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'cpu')"
nvidia-smi
git rev-parse HEAD
git status --short
pip freeze > env_pip_freeze.txt
```

Linux Bash 可记录：

```bash
python --version
python - <<'PY'
import torch
print("torch=", torch.__version__)
print("cuda=", torch.version.cuda)
print("available=", torch.cuda.is_available())
print("gpu=", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu")
PY
nvidia-smi
git rev-parse HEAD
git status --short
pip freeze > env_pip_freeze.txt
```

建议目录：

```text
project_root/
  data/
    xlsa17/data/CUB/
    xlsa17/data/AWA2/
    xlsa17/data/SUN/
    cache/
  configs/
  runs/
    <dataset>/<method>/<run_id>/
      config.yaml
      env.txt
      train.log
      eval.log
      metrics.json
      predictions.csv
      rule_checks.yaml
      checkpoints/
```

数据集、特征缓存、checkpoint、大型日志不进 Git。Git 中只保留轻量摘要、配置、脚本、规则检查和结果索引。

## 3. 数据和标注规范

### 3.1 标准 split

标准数据集优先使用公开固定 split，例如 xlsa17 的 `att_splits.mat`。至少要记录：

```text
allclasses_names: 全部类别名，顺序必须固定
seenclasses: seen 类全局编号
unseenclasses: unseen 类全局编号
trainval_loc: seen 训练样本索引
test_seen_loc: seen 测试样本索引
test_unseen_loc: unseen 测试样本索引
labels: 每张图像的全局类别标签
att 或 text_features: 类别语义原型
```

如果自建 split，必须额外保存：

```text
split_name
split_version
class_order
seen_class_ids
unseen_class_ids
sample_id -> global_label
sample_id -> split
生成 split 的脚本和随机种子
```

### 3.2 标签映射

训练时可以把 seen 类映射到局部编号 `[0, N_seen-1]`，但必须保存双向映射：

```text
global_to_seen_local: global_label -> local_seen_label
seen_local_to_global: local_seen_label -> global_label
eval_class_order: [全部 global_label，顺序固定]
```

评估输出的预测标签必须是全局标签。禁止用局部 seen 标签直接计算 GZSL 指标。

### 3.3 禁止信息泄漏

以下情况视为无效实验：

- unseen 测试图像参与训练、特征训练、缓存拟合或数据增强统计拟合。
- unseen 图像标签参与 loss、采样权重、校准参数搜索或 early stopping。
- 重新排序类别后没有同步修正语义原型和标签。
- 用 test_unseen 的结果反复调超参，却把该结果当作正式测试结果。

允许使用 unseen 类的语义原型，但必须说明来源和使用方式。例如属性向量、类别名文本、CLIP 文本编码、人工描述、GPT 生成描述等。若 unseen 语义原型经过训练模块 forward，必须记录是否进入 loss、是否产生梯度、是否影响训练参数。

## 4. 模型和训练规范

训练阶段默认只从 seen 图像样本构造监督 loss。训练 logits 可是 `[B（图片/样本数量）, N_seen（seen 类别数量）]`，也可以是 `[B（图片/样本数量）, N_total（全部类别数量）]` 后只取 seen 部分算 loss，但必须明确记录。

每个新增模块必须记录：

```text
输入张量形状、dtype、device
输出张量形状、dtype、device
训练阶段行为
评估阶段行为
梯度路径
是否触碰 unseen semantic prototype
是否触碰 unseen image feature
关闭该模块时是否等价回到 baseline
预期影响的指标
```

训练 run 必须固定并记录：

```text
dataset
split_source
backbone
semantic_source
feature_cache_path
config_path
seed
epochs
batch_size
optimizer
learning_rate
weight_decay
augmentation
train_command
eval_command
```

正式对比时，baseline 和新方法必须使用同一 split、同一类别顺序、同一特征缓存或同一 backbone 设置、同一语义来源，除非实验目的就是比较这些因素。

## 5. 评估规范

### 5.1 GZSL 评估

GZSL 评估时，候选类别必须是 seen+unseen 全类别。模型输出应能映射到：

```text
logits: [B（图片/样本数量）, C_total（全部候选类别数量）]
class_axis: 固定的 eval_class_order
prediction: argmax(logits, dim=1) 后映射为 global_label
```

在 `test_unseen` 上计算 unseen 类平均准确率：

```text
acc_c = correct_samples_of_class_c / total_samples_of_class_c
GZSL-U = mean(acc_c for c in unseenclasses)
```

在 `test_seen` 上计算 seen 类平均准确率：

```text
acc_c = correct_samples_of_class_c / total_samples_of_class_c
GZSL-S = mean(acc_c for c in seenclasses)
```

调和平均：

```text
GZSL-H = 2 * GZSL-U * GZSL-S / (GZSL-U + GZSL-S)
```

如果 `GZSL-U + GZSL-S = 0`，则 `GZSL-H = 0`。

默认使用 per-class macro accuracy，不使用按样本数加权的 micro accuracy 作为主指标。结果统一报告百分比，例如 `73.93%`。

### 5.2 ZSL 评估

ZSL 只在 unseen 测试样本上评估，候选类别只允许 unseen 类：

```text
ZSL = mean per-class accuracy on test_unseen with candidate labels = unseenclasses
```

注意：`ZSL` 不等于 `GZSL-U`。`GZSL-U` 是 unseen 样本在 seen+unseen 全类别竞争下的准确率，通常更难。

### 5.3 checkpoint 选择

默认以 `GZSL-H` 选择 best checkpoint。禁止只看 `GZSL-U` 或只看 `GZSL-S` 宣称主结果，除非实验目标明确是偏置分析。

正式报告至少包含：

```text
best_epoch
GZSL-U
GZSL-S
GZSL-H
ZSL
U/S gap = GZSL-S - GZSL-U
checkpoint_path
eval_log_path
```

## 6. 评估产物标注

每次评估建议输出 `predictions.csv`：

```text
sample_id
image_path
split: test_seen 或 test_unseen
true_global_label
true_class_name
pred_global_label_gzsl
pred_class_name_gzsl
pred_is_seen_gzsl
pred_score_gzsl
correct_gzsl
pred_global_label_zsl
pred_class_name_zsl
correct_zsl
```

其中 `pred_global_label_zsl`、`pred_class_name_zsl`、`correct_zsl` 只对 unseen 测试样本有意义；seen 测试样本可为空。

`metrics.json` 建议字段：

```json
{
  "dataset": "CUB",
  "split_source": "xlsa17/att_splits.mat",
  "method": "method_name",
  "run_id": "RUN-YYYYMMDD-CUB-method-seed1-attempt001",
  "seed": 1,
  "commit": "<git_commit>",
  "config_path": "configs/xxx.yaml",
  "class_order_hash": "<hash>",
  "seen_class_count": 150,
  "unseen_class_count": 50,
  "metric_semantics": "standard GZSL U/S/H/ZS, per-class macro accuracy",
  "best_epoch": 26,
  "GZSL-U": 71.43,
  "GZSL-S": 76.36,
  "GZSL-H": 73.81,
  "ZSL": 81.25,
  "checkpoint_path": "runs/.../checkpoints/best_h.pt"
}
```

`rule_checks.yaml` 建议字段：

```yaml
rule_checks:
  - rule_id: seen_unseen_split_unchanged
    verdict: pass
    checked_by: script
    authority_ref: xlsa17/att_splits.mat
  - rule_id: class_order_unchanged
    verdict: pass
    checked_by: script
    authority_ref: class_order_hash
  - rule_id: label_mapping_unchanged
    verdict: pass
    checked_by: script
    authority_ref: eval_class_order
  - rule_id: metric_semantics_standard
    verdict: pass
    checked_by: evaluator
    authority_ref: standard GZSL U/S/H/ZS
  - rule_id: unseen_label_leakage_forbidden
    verdict: pass
    checked_by: code_review
    authority_ref: train_dataset_and_loss_trace
```

任何 hard rule 不清楚时，该 run 只能标为 `blocked`、`rerun` 或 `reject`，不能标为 `best`、`confirmed` 或 `promote`。

## 7. 新电脑首轮验证流程

在长时间训练前，先跑小验证：

1. 环境检查：确认 `torch.cuda.is_available()`、GPU 名称、driver、CUDA 和 PyTorch 版本。
2. 数据检查：打印 seen/unseen 类数量、训练样本数、test_seen 样本数、test_unseen 样本数。
3. 标签检查：随机抽 5 个样本，打印 `sample_id`、`image_path`、`global_label`、`class_name`、`split`。
4. 类别顺序检查：保存 `eval_class_order` 和 hash，确认语义原型行数等于全部类别数。
5. one batch 检查：跑一个 batch，确认输入、输出和 loss 都不是 NaN。
6. tiny run：用少量 batch 跑 1 个 epoch，确认 train log、eval log、checkpoint、metrics.json 都能生成。
7. resume 检查：从 checkpoint 恢复一次，确认 epoch 和 optimizer 状态能延续。
8. dry eval 检查：固定 checkpoint 重跑 eval，确认指标可复现。

这些检查通过后，再跑正式完整实验。

## 8. 结果记录和结论分级

每个 run 结论按以下等级标注：

```text
explore: 探索 run，可用于找方向，不能支撑论文 claim
best_single: 单次最优结果，只能说 best single
repeat_pending: 已有单次结果，等待多 seed 或 confirmation
confirmed_repeat: 多 seed 或重复 run 结果稳定
rejected: 指标差、规则失败或证据不足
blocked: 关键规则、路径、数据或评估语义不清楚
promote_candidate: 可进入下一轮主线或论文表格候选
```

正式 promotion 至少需要：

```text
hard rules 全部 pass
baseline 与新方法同 split、同评估语义
至少 3 个 seed 或 3 次独立确认 run
报告 mean ± std
同时检查 best single 和 confirmed repeat mean
GZSL-H 提升不是由 GZSL-U 或 GZSL-S 单边崩塌换来的
保留训练日志、评估日志、checkpoint 路径和 metrics.json
```

结论表达模板：

```text
best single:
  RUN-xxx epoch=xx U=xx.xx S=xx.xx H=xx.xx ZS=xx.xx

confirmed repeat:
  seeds=[1,2,3]
  H mean=xx.xx std=xx.xx
  U mean=xx.xx std=xx.xx
  S mean=xx.xx std=xx.xx
  ZS mean=xx.xx std=xx.xx

promotion judgment:
  promote / hold / reject / rerun

main risk:
  U/S gap、数据泄漏风险、class order 风险、超参调优风险、复现风险
```

## 9. 常见无效结果

以下结果不能进入正式表格：

- 只输出整体 accuracy，没有拆分 `GZSL-U` 和 `GZSL-S`。
- `GZSL-U` 用 unseen-only candidate labels 计算，混成了 `ZSL`。
- 训练时类别顺序和评估时类别顺序不一致。
- 训练 CE 用局部 seen label，评估时没有映射回 global label。
- 用 test_unseen 反复调校准参数，然后宣称无偏测试结果。
- 新模块关闭后不能回到 baseline，导致无法判断收益来自哪里。
- 只保存截图或聊天结论，没有日志、配置、commit 和指标 JSON。

## 10. 最小交付包

一次可审计的正式 GZSL run 至少交付：

```text
config.yaml
env.txt 或 env_pip_freeze.txt
train.log
eval.log
metrics.json
predictions.csv
rule_checks.yaml
checkpoint 路径
运行命令
Git commit
结论摘要
```

如果这些文件不完整，结论最多是探索结果，不应写成论文级 claim。
```
