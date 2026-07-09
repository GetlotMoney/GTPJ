# GTPJ Agent 规则

## Owner 自我介绍

- Owner 是研究生一年级、人工智能专业学生，目前研究 CV 方向的 GZSL 领域。
- Owner 喜欢从第一性原理思考问题，希望 agent 在解释概念、判断路线和拆解实验时优先回到问题本质。
- Owner 在本项目内要完成 GZSL / CV 方向的实验、总结和创新沉淀。
- Owner 默认用中文协作，正在把 GTPJ 作为干净主仓库维护，用于 GZSL / CV 模型实验、版本治理和实验追溯。
- `cv-work` / DVSR 旧项目是历史实验资产库和流程素材库；GTPJ 是当前主仓库和后续工作中心。
- Owner 重视可复现、可回滚、证据完整和长期沉淀；不希望为了快而把旧实验、旧分支、旧 workflow 原样搬进 GTPJ。
- Owner 的长期目标是搭建完整的“论文阅读 -> 创新想法 -> 实验验证 -> 结果总结 -> 反哺创新”的闭环工作流，用 AI 解放重复劳动，自动化完成可靠实验。
- 当前优先级是先把 GitHub 治理、baseline、创意来源、trial 证据链做干净，再逐步接入 OpenClaw / Codex 工作流；最终服务于可复现实验和创新沉淀。

## Owner 默认要求

- 默认用中文沟通，除非任务明确要求英文。
- 先讲结论，再讲关键原因。
- 复杂任务先给简短计划，再开始执行。
- 不确定时说明假设和风险，不要装作确定。
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
- 新增或修改项目文档、workflow 文档、模板说明和审核报告时，正文必须使用中文；不允许整段英文说明。
- 英文只允许作为必要名词或机器标识保留，例如论文标题、方法名、角色名、命令、字段名、文件名、代码标识、指标名、URL 和 helper 依赖的结构 marker。
- 如果标题必须保留英文 marker，例如 `Framework Diagram`、`Trial Flow`、`Code Flow Diagram`，同一节必须用中文解释它的含义和填写规则。
- 先说结论，再说关键原因。
- 复杂任务在编辑前先给简短计划。
- 直接说明不确定性和风险。
- 交付流程图、框架图、代码路径图或实验链路图时，默认额外生成一个可本地打开的 HTML 文件，并在回复中用 `file:///D:/.../xxx.html` 的绝对本地链接给 owner。Markdown/Mermaid 可以作为仓库权威记录，但不能替代 owner 可直接打开的 HTML 视图。

## AI 审核规范

- 重要代码修改、workflow/helper/template 修改、训练入口、评估语义、实验结论、promotion 或论文 claim 相关决策，默认不要求 owner 参与日常审核，但必须按 `review_tier` 分层执行 AI 交叉审核。
- 机器验证永远优先且永远必跑；AI 审核不能替代测试、workflow validate、audit-boundary、schema 或 helper gate。
- Codex 负责实现、修复、反驳和重跑验证；Claude Code 只读审查，不直接改文件、不启动训练、不执行 push/delete/发布。
- `fast`：0 轮 Claude Code，只允许低风险轻量文档或 workflow 修补；仍必须有机器验证和命名 Codex 线程预审。
- `review-1`：1 轮 Claude Code，用于普通 workflow/helper/template 修补，不直接污染正式实验结论。
- `strict-3`：3 轮 Claude Code，只用于训练入口、评估语义、正式实验结论、promotion、baseline 或论文 claim 等会污染正式结论的改动。
- Claude Code 前必须先创建或绑定命名 Codex 线程做只读预审；预审完成后立刻归档，并在 evidence pack 记录真实 `thread_id`、UI 显示名和结构化 `archive_result`。
- 代码审核不被 `server_frozen_runner` 豁免。`server_frozen_runner` 只表示训练运行期不创建命名线程；一旦修改代码、workflow、helper 或模板，仍必须先切专用代码审核分支，完成命名 Codex 线程预审、Claude Code 只读审核和 `validate-ai-cross-review`。
- AI 交叉审核必须留下中文 evidence pack，并通过 `python workflow\gtpj_workflow.py validate-ai-cross-review --path <review_pack>` 后，才能进入正式 Runner、keep/best、confirmation、promotion、baseline 或 paper claim。
- push、删除、远端发布、破坏性迁移、密钥处理或用户数据操作仍然必须等待 owner 明确授权。

## 流程设计原则

- 每次新增或修改 workflow 规范、状态机、helper、模板、playbook、protocol 或 agents 调度规则时，必须先从第一性原理出发说明：它要解决的最小真实问题是什么，现有流程为什么不够，最小闭环是什么。
- 默认选择最简单可验证实现：能用一个字段解决的，不新增一个文件；能用一个 helper 子命令解决的，不新增一套协议；能复用现有状态机和证据链的，不另建平行流程。
- 瘦身优先：新增或修改规范、流程、文档、模板、helper 或 agent 调度规则时，默认写最短可读版本；能合并到现有入口就不新建文件，能删旧冗余就先删冗余，能用一条规则表达就不拆成多层流程。
- 新流程必须服务于闭环，不服务于形式。至少要说明输入、输出、责任角色、状态变化、验证命令、失败退出条件和回滚方式；说不清这些，就先停在建议，不写入正式规范。
- 不为“看起来完整”而增加文档层级。新增文档必须满足至少一项：能被机器校验、能驱动状态机、是正式 evidence 必需模板、是 owner/agent 的权威入口。
- 每个实验类型可以有不同规范，但必须通过统一 router 和统一状态机进入；差异放在 playbook/profile/config 中，不要复制出互相污染的独立流程。
- 任何自动化都先做最小可用闭环，再逐步加能力。优先顺序是：可读状态 -> 可验证 gate -> 可回滚执行 -> 可审计证据 -> 自动优化；不要一开始就堆复杂调度。
- 新规范写入前要给 owner 一个短摘要：为什么需要、最小实现是什么、会改哪些文件、哪些复杂设计被刻意不做。

## 最简 GTPJ 工作流

1. 先查状态：确认分支、HEAD、dirty 文件、远端/服务器是否需要同步；只读问题先只读回答。
2. 再定任务：按 `START_HERE.md` 判断是查状态、读论文、创新、调参、消融、复现、promotion 还是混合 campaign。
3. 明确基线：所有实验必须写清 `base_version` / `base_code_tag`；论文到实验必须先有 owner 指定的代码版本。
4. 选模板：新创新优先用模块模板热插拔；owner 明确要求“新模板重建”时，使用 `standard_gzsl_training_template.py` 生成 trial-local 训练入口，不继续堆旧训练脚本。
5. 记录框架：只有产生或改变方法框架的代码模块变动才要求框架记录；调参、复现、只关闭既有模块的窄消融不新增框架，只记录结果证据。凡是新增/改写 module、forward、loss、eval、data view 或接口语义的代码变动，都归入创新 / module trial，必须有 `module_source.md`、`implementation.md`、`framework_diagram.md`，必要时还要有 `Code Flow Diagram`。
6. 先写计划：正式写入或训练前生成 mini 启动摘要；需要正式证据时再展开完整 task card。
7. 走状态机：正式证据对象必须绑定 `subject_id` / `subject_type`；`TRANSITIONS.jsonl` 是 append-only 权威历史，`evidence_routing.yaml` 只能由 chain head 派生，不能手写抬高状态。
8. 先选运行等级：`debug_smoke` 只能测试代码、服务器、GPU 和 helper 链路，必须写 `activation_mode: role_only`、`formal_evidence: false`、`real_agent_instances_started_by_helper: false`；`formal` 进入正式证据时允许两条路径：`real_multi_agent`，或 `server_detached_role_only`。两者都必须写 `formal_evidence: true`、`agent_runtime_gate_satisfied: true`。
8a. 只要本轮会改代码、workflow、helper、模板或训练配置生成逻辑，必须在修改前切到专用代码审核分支；在旧脏分支上补切只能算草稿隔离，不能作为正式 freeze / Runner 启动依据。
9. 正式 Runner 前先写 `agent_runtime.yaml` 并依次跑 `validate-agent-runtime`、`multi-agent-preflight`、`agent-cleanup-plan`。如果是 `real_multi_agent`，必须记录真实 thread id、UI 显示名、role 映射和 output refs；如果是 `server_detached_role_only`，必须记录独立 sequential role outputs、server_detached preflight 和 `thread_creation_allowed: false`。
10. 创建命名线程前先检查左侧栏：如果 owner 报告左侧栏仍有历史 agents，或者当前工具不能确认左侧栏干净，禁止继续启动新的命名线程；本轮 `real_multi_agent` 阻断。此时可以改走 `server_detached_role_only` formal，或降级为不进证据的 `debug_smoke`。
10a. owner 说“开启多agents智能体工作流”“多agents智能体工作流，开始”“跑N轮”或“做N轮实验”时，视为明确选择 `live_multi_agent_monitor` 并授权执行；不要反复确认 workflow 模式或启动意图。只有模式冲突、侧边栏干净状态缺失且无法验证、硬门失败或安全边界动作，才允许再问一次。
11. 严格命名 agents：左侧命名 Codex 线程显示名必须按 `<subject_id> | <Role Label>`，例如 `ATTEMPT-007 | Runner Monitor`；禁止使用 Herschel、Galileo、Feynman 等随机英文昵称。
12. 跑实验：Runner 串行锁 GPU；GitHub 只记轻量账本；raw logs、checkpoint、generated figures 和 cache 进 Warehouse/Research，不进 GitHub。
13. 收结果：`live_multi_agent_monitor` 运行中必须持续汇报每个新增 completed job，使用 `monitor-workflow --report-new-completions --activity-log <attempt_dir>\AGENT_ACTIVITY.md` 或等价证据写入；每条至少记录 `job_id`、H/U/S/ZS、当前 best、H>=75/H>=76、证据位置和下一步。closeout 时写 `manifest.yaml`、`result.yaml`、`result.md`、`quality_check.md`、`agent_summary.md`、`AGENT_ACTIVITY.md`；复现必须是 `repeat_type: exact_repeat`，锁定 `original_seed`、原始 config、代码 commit、数据/缓存、训练日程和评估口径，不允许换 seed 或换任何参数；默认 `max_attempts: 5`、`max_attempts_hard_cap: true`、`early_stop_on_best_hit: true`。必须声明 `restore_target_H`；`near_miss_tolerance_H` 只能用于记录“接近但未还原”。复现结果必须分成 `best_hit`、`near_miss_not_restored` 和 `stable_confirm`：`best_hit` 只看任一 clean repeat 是否真正达到原水平，回答“有没有还原”；`near_miss_not_restored` 只能说明实验有效果、还有希望，不能停止、不能 confirmation；`stable_confirm` 才看 mean/min/max/range，回答“能不能作为稳定 confirmed / promotion / baseline 证据”。`seed_sweep` / `score_search` / `multi_seed_stability` 必须写 `not_confirmation_evidence: true`，不能冒充复现。
14. 做审核：普通 workflow 修补走 `review-1`，正式结论污染风险走 `strict-3`；所有机器验证照跑。
15. 收尾清理：Runner 仍有 running/pending job 时，当前阶段 active 左侧命名线程必须保持可见；只有 closeout/handoff 完成、输出已入账后，才报告 `keep / archive / unknown agents`，归档 completed threads，记录 `archive_result`，左侧栏只保留当前 active agents。

## 仓库规则

- `main` 是唯一长期分支。
- `v1`、`v2`、`v3`、`v4`、`v5` 是永久版本 tags；当前正式确定版本以 `README.md`、`docs/PROJECT_STATUS.md` 和 `experiments/VERSION_TREE.md` 为准。`v4` 是历史 config-only tag，不作为以后“只调参也能开新 vX”的模板。
- 复现实验必须先记录 `best_hit`：只有任意 clean completed/ok exact repeat 的单次 H 达到 `restore_target_H`，才标记为还原命中，并更新 `best_observed_H` / `best_single_H`；命中后必须停止后续 pending repeat。`max_attempts: 5` 是 `max_attempts_hard_cap`：不管有没有还原成功，同一候选最多跑 5 次；5 次仍未达到 `restore_target_H` 就收口为 not restored / near miss 状态，不能继续加跑。落在 `near_miss_tolerance_H` 内但没达到 `restore_target_H`，只能写 `near_miss_not_restored`，表示实验有效果、还有希望，不能写成复现通过，不能停止后续 repeat。`stable_confirm` 是另一层：只有质量门另行要求多 run 稳定性时，才用同一 `original_seed`、同一配置的 clean repeats 计算 mean/min/max/range，并按 `docs/workflow/protocols/promotion.md` 进入 promotion 判断。多个 stable-confirmed 候选同时存在时，按 `confirmed_H` 最高者确定为正式版本；`best_observed_H` 只回答“最高跑到过多少”，不能单独决定 promotion。promotion 表示确定正式版本/tag，不等于自动执行 `activate-version` 或切换 active runtime alias。
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

- GTPJ 实验默认使用本机 conda 环境 `dvsr_gpu`；运行训练、特征抽取、验证脚本前先激活该环境，或使用 `conda run -n dvsr_gpu ...`。
- OpenClaw 是优先 runtime；Codex 兼容，但必须遵循同一套文件。
- 每个新模块 trial 都必须从 `idea_tree` 节点开始。
- 没有 `idea_id`，就没有 `dev/idea-*` 分支。
- 每个 trial 至少记录 implementation、config、quality_check、result 和 code tag。
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
- 正式 `real_multi_agent` 默认使用 `agents.agent_instance_mode: named_owner_thread` 和 `lifecycle: workflow_scoped`。如果目标是服务器 detached 连续训练、owner 明确不希望创建线程，则允许 `activation_mode: role_only` + `formal_runtime_backend: server_detached_role_only` 作为第二条正式路径。
- `named_owner_thread` 是本轮 workflow 或 campaign 阶段的活上下文；它可以持续到本轮工作结束，但结论必须沉淀到 repo、log、artifact、Research、Warehouse、result、quality 或 `agent_summary.md`。
- `persistent_thread` 只在角色需要跨多个 workflow 连续追踪、owner 明确要求可见长期线程，或长周期 campaign 的 Coordinator/Monitor 需要跨天连续上下文时启用。线程上下文可能压缩或漂移，所以任何结论进入正式 evidence 前仍必须回到 repo、log、artifact 或 Research 验证。
- `role_only` 表示一个主 agent 按 Coordinator、Runner、Quality Checker 等角色清单串行执行；如果结果进入正式证据，必须显式声明 `formal_runtime_backend: server_detached_role_only`，并在 `agent_summary.md` 里说明为什么没有启动真实多 agents。
- `real_multi_agent` 表示启动或委派独立 agent / reviewer / checker，保留独立输入、发现和结论；如果当前环境没有真实 multi-agent 工具，不能把顺序角色扮演写成 `real_multi_agent`。
- `real_multi_agent` 必须分文件复核：每个只读角色要在自己的输出里写 `files_reviewed`、`decision` 和 `uncovered_scope`，并指向独立 output file。入口规则、hard gate、helper 测试和本地 skill 镜像必须分别有人看，不能由一个上下文代替全部检查。
- `role_only_with_independent_sequential_review` 不是第三种 activation mode，只能写在 `agents.tool_support.fallback_mode`；它不能用于 promotion、正式 best 结论或 owner 已明确要求真实多 agents 的任务，除非 owner 明确接受 debug/smoke 降级。
- owner 明确要求多 agents、启动真实 Runner、产出正式 evidence、任务修改模型/forward/loss/eval/数据流语义、涉及接口/评估/label mapping/seen-unseen split/class order/logits shape/metric semantics 风险、结果异常有争议、promotion 前复核、结论会影响论文实验路线或 baseline 选择时，必须使用 `real_multi_agent`。
- 窄范围 rerun / confirmation 准备、训练前候选 triage、只读解释、配置查看、debug/smoke 或不改变结论的账本格式整理时，可以使用 `role_only`，但必须记录代执行的角色和升级条件；debug/smoke 结果不能进入 keep、best、promotion 或 confirmation evidence。
- Runner 永远串行并锁 GPU；Implementer 是同一代码路径唯一 writer；Coordinator 是最终 GitHub 账本唯一写入者；Reader/Planner、Log Analyst、Quality Checker、Result Analyst、Reviewer 默认只读，可并行。
- Agent 不能把隐藏聊天记忆当实验事实源。Codex memory 或历史会话摘要只能用于定位，必须回到当前 repo、日志或 artifact 验证后才能写入结果、质量门或 promotion 证据。
- `agent_summary.md` 必须记录 `activation_mode`、`agent_instance_mode`、`agent_instance_type`、`lifecycle`、`persistent_thread_id`（如启用）、`named_thread_reason`、`independence_scope`、`output_locations`、`memory_used`、`memory_sources` 和 `verified_against_current_repo`。
- 如果 owner 对 agent 模式提出异议，先暂停真实 run，修正启动卡或升级为 `real_multi_agent` 后再继续。

## 安全

- 不提交数据集、checkpoint、原始 cache、密钥或大型日志。
- 不使用训练/测试反馈在运行中途改变训练行为。
- 不隐藏失败实验；失败也要作为证据记录。
