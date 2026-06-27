# GTPJ Workflow Router

本文件是 GTPJ 的总教官。它不替代具体协议，而是在任何任务开始前先做路由判断：

```text
用户请求 -> 任务类型 -> 是否进入 idea_tree -> 写入位置 -> 需要读取的协议 -> agents -> gates
```

默认范围：本 Router 只服务“跑实验、做创新、复现、消融、调参、debug 和实验结果记账”。

Owner 不需要说“开启动卡”或自己判断任务类型。Owner 只需要说：

```text
我想基于 <version> 跑/做 <experiment or idea>。
```

Router 和 Coordinator 必须自动判断这是什么任务、能不能开工、缺什么、下一步最小动作是什么。

如果其它文档分散描述了某条规则，先用本文件判断任务归类，再进入对应协议细节。

## 0. 优先级

发生冲突时按下面顺序处理：

1. 用户本轮明确要求。
2. 安全边界：不 push、不发布、不删远端、不重写历史，除非用户明确要求。
3. 硬门：`code_interface_contract.md`、`quality_gate.md`、`promotion.md`。
4. 本文件的路由判断。
5. 具体协议：`idea_tree_protocol.md`、`experiment_protocol.md`、`module_trial_protocol.md` 等。
6. `IMPLEMENTATION_STATUS.md` 的已落地/按需创建状态。

Router 只负责决定走哪条路；证据是否有效，由接口硬门、质量门和 promotion gate 决定。

## 1. 总判断规则

最重要的两条：

```text
实验是为了调/查/验证已有正式 baseline -> experiments/vX，不进 idea_tree。
实验是为了调/查/确认某个 module trial 内部模块 -> experiments/module_trials/.../attempts/ATTEMPT-xxx，不另进 idea_tree。
实验是为了证明一个新方法值得存在 -> idea_tree + module_trials。
```

不要因为一次实验有“想法”两个字就写入创意树。只有可复用的新机制、新模块、新方法，或者可能成为新 baseline 的设计，才进入 `idea_tree/`。

## 2. 任务分类表

| 用户请求 | 任务类型 | 是否进 `idea_tree/` | GitHub 写入 | 本地外部写入 | 必读协议 | 必需 agents/gates |
|---|---|---:|---|---|---|---|
| 读一篇论文，找创新点 | paper intake / idea discovery | 候选成熟后才进 | `idea_tree/sources/`、必要时 `idea_tree/inbox.md` 或 `idea_tree/ideas/` | `GTPJ_Research/papers/`、`notes/`、`source_reviews/`、`ideas/` | `paper_intake.md`, `idea_tree_protocol.md` | Reader/Planner，source review |
| 自己想到一个新机制 | local heuristic idea | 是，但先写来源和假设 | `idea_tree/inbox.md` 或 `idea_tree/ideas/IDEA-xxxx/` | `GTPJ_Research/ideas/` | `idea_tree_protocol.md` | Reader/Planner，Interface Checker 预审 |
| 调正式 baseline 的参数、seed、epoch、loss weight | tune | 否 | `experiments/vX/tune/` | Warehouse logs/runs | `experiment_protocol.md` | Coordinator、Runner、Log Analyst、Quality Checker |
| 对正式 baseline 做关掉/旁路/替换已有模块看贡献 | ablation | 否 | `experiments/vX/ablation/` | Warehouse logs/runs | `experiment_protocol.md`, `code_interface_contract.md` | Implementer、Interface Checker、Runner、Quality Checker |
| 复现 baseline 或确认某个版本级结果 | confirmation | 否 | `experiments/vX/confirmation/` | Warehouse logs/runs | `experiment_protocol.md` | Runner、Log Analyst、Quality Checker |
| 调某个 module trial 的参数、头数、ratio、dropout、seed | innovation / module trial；subtype: trial-internal attempt | 已有 idea | `experiments/module_trials/.../TRIAL-xxx/ATTEMPTS.md` + `attempts/ATTEMPT-xxx/` | Warehouse logs/runs | `module_trial_protocol.md`, `code_interface_contract.md` | Coordinator、Runner、Log Analyst、Quality Checker、Result Analyst |
| 对某个 module trial 做窄消融或 clean confirmation | innovation / module trial；subtype: trial-internal attempt | 已有 idea | `experiments/module_trials/.../TRIAL-xxx/ATTEMPTS.md` + `attempts/ATTEMPT-xxx/` | Warehouse logs/runs | `module_trial_protocol.md`, `code_interface_contract.md` | Coordinator、Interface Checker 视风险、Runner、Log Analyst、Quality Checker、Result Analyst |
| debug、smoke test、环境验证 | debug / smoke | 否 | 通常不写；若结果要引用，转为对应实验目录 | 可写临时本地输出；长期证据进 Warehouse | `experiment_protocol.md` 视情况 | 不得作为有效结果，除非补齐 manifest/result/quality |
| 加新模块、新结构、新 forward 路径、新 loss 机制 | innovation / module trial | 是 | `idea_tree/` + `experiments/module_trials/` | Research 长推理，Warehouse 运行证据 | `idea_tree_protocol.md`, `module_trial_protocol.md`, `code_interface_contract.md` | Reader/Planner、Implementer、Interface Checker、Runner、Quality Checker、Reviewer |
| 结果想成为新 baseline | promotion | 通常已有 idea 或实验来源 | `config/versions/vY.yaml`、`experiments/vY/`、`VERSION_TREE.md` | Warehouse 证据引用 | `promotion.md`, `quality_gate.md`, `versioning.md` | Coordinator、Quality Checker、Reviewer、Result Analyst |
| 只切换创意树当前视图 | set-current-version | 使用已有 idea_tree | `idea_tree/idea_tree.json`、`idea_tree/versions/vX.md` | 不写 | `idea_tree_protocol.md` | 不切 main active code |
| 切换 main 当前运行代码到某版本 | activate-version | 否 | `config/GTPJ_*.yaml` 等 active code/config | 不写 | `versioning.md`, `git_policy.md` | 必须 owner 明确要求 |
| 创建或查看运行看板状态 | progress dashboard | 否 | 不写长期 GitHub 账本 | `.gtpj_runtime/` | `progress_dashboard.md` | 只读看板，不启动训练 |

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
9. 执行或给出执行计划。
10. 用对应 gate 收口：interface、quality、promotion、source review 或 sync check。

如果第 2 步无法归类，先不要动代码和文件，向 owner 提出一个最关键问题。

## 3.1 对话先行规则

正式开工前，Coordinator 先给 owner 一个简短判断：

```text
能不能开工：
任务类型：
基于版本：
为什么这样归类：
当前缺口：
下一步最小动作：
```

然后再决定是否进入启动卡、分支、目录、代码或运行。

没有下面任一信号时，不要改代码、跑实验、创建实验目录或登记结果：

- owner 明确说“开始”“跑”“你来操作”“按这个做”；
- owner 本轮请求本身已经明确授权实际操作；
- 当前动作只是只读检查、解释或建议。

如果存在阻断，先说阻断原因和最小补齐动作，不要让 owner 自己填完整流程表。

## 4. Idea Tree 准入

进入 `idea_tree/` 的必要条件：

- 这是新模块、新机制、新方法，或可能成为新 baseline 的设计。
- 有明确 `source_type`：`paper`、`user`、`observation`、`cross_domain` 或 `hybrid`。
- 有明确 `source_status`：正式 trial 前必须是 `verified` 或 `local_heuristic`。
- 有针对 base version 的 `version_scores.<vX>`。
- 写清楚 hypothesis、implementation_scope、risk。
- 接口影响能被 Interface Checker 检查。

不进入 `idea_tree/` 的情况：

- 版本级 tune 参数搜索。
- 版本级 ablation 问题本身。
- 版本级 confirmation 复现实验。
- 已有 module trial 内部的 param_tune、窄 ablation、confirmation/rerun。
- debug/smoke test。
- 只为了排查环境、日志、cache 或数据路径。

版本级调参或消融中如果发现了可复用新机制，先把原 version-level 实验记入 `experiments/vX/...`，再单独创建新的 idea。不要把一次普通实验硬改成 module trial。
module trial 内部 attempt 如果超出原实现假设，形成新的 forward 路径、新 loss 机制或新接口语义，则新开 `TRIAL-002`，不要继续写入原 `TRIAL-001`。

## 5. 来源不是论文时怎么写

不是所有 idea 都需要论文来源。

用户自己的想法：

```yaml
source_type: user
source_status: local_heuristic
source_ref: owner:YYYY-MM-DD:<short reason>
```

来自实验观察：

```yaml
source_type: observation
source_status: local_heuristic
source_ref: observation:<experiment_id>:<short observation>
```

混合来源：

```yaml
source_type: hybrid
source_status: verified
source_ref: paper:<paper_id> + observation:<experiment_id>
```

`local_heuristic` 必须写明可复核观察、owner 接受理由和日期；否则只能留在 `inbox`，不能开 trial。

## 6. 写入边界

| 内容 | 写入位置 |
|---|---|
| 完整论文、长笔记、长推理、完整创意树 | `GTPJ_Research` |
| GitHub 轻量 idea id、评分、状态、linked trials | `idea_tree/` |
| 版本级普通实验配置、manifest、result、quality_check | `experiments/vX/...` |
| 模块 trial 根证据 | `experiments/module_trials/.../TRIAL-xxx/` |
| 模块 trial 内部调参、窄消融、confirmation/rerun | `experiments/module_trials/.../TRIAL-xxx/ATTEMPTS.md` + `attempts/ATTEMPT-xxx/` |
| raw logs、checkpoint、generated figures、failure cases | `GTPJ_Warehouse` |
| 运行中状态 | `.gtpj_runtime/`，不进 Git |
| 本机真实路径 | `.gtpj/local_paths.yaml`，不提交 |

## 6.1 联动更新规则

GitHub 和本地不是机械“每次同时写”，而是按任务类型成对更新：

| 触发场景 | 先写 | 后写 | 收尾检查 |
|---|---|---|---|
| 读论文、提取创新点 | `GTPJ_Research/papers/`、`source_reviews/`、`ideas/` | GitHub `idea_tree/sources/`、`idea_tree/ideas/` 轻量索引 | GitHub 有 `research://` 或本地路径指针 |
| 用户提出新机制 | `GTPJ_Research/ideas/` 长版动机/机制/风险 | GitHub `idea_tree/inbox.md` 或正式 `IDEA.md` | `source_status` 和 owner 接受理由可追溯 |
| module trial 运行 | Warehouse raw artifacts | GitHub `manifest/result/quality/ATTEMPTS` | GitHub artifact URI/hash/size 可反查 Warehouse |
| trial 改变 idea 结论 | Research `decision_history.md`、`experiment_plan.md` | GitHub `idea_tree.json`、`IDEA.md`、版本视图 | 人类版和机器版状态一致 |
| version-level tune/ablation/confirmation | Warehouse + GitHub `experiments/vX/...` | 通常不写 Research | 若产生新机制，再另走 idea discovery |

如果某个结论影响后续实验选择、promotion、版本适配分或论文叙述，不能只留在聊天里。
Coordinator 收尾时必须说明：

```text
GitHub 写了什么：
Research 写了什么：
Warehouse 写了什么：
哪些内容没有联动，为什么：
```

Paper intake 的细化流程见 `docs/workflow/paper_intake.md`。论文是否读过、读到哪一步，以
`GTPJ_Research/papers/PAPERS_INDEX.md` 为准，不以 PDF 是否存在为准。

## 7. Agent 路由

| 任务类型 | 默认 agents |
|---|---|
| paper intake / idea discovery | Coordinator、Reader/Planner |
| tune | Coordinator、Reader/Planner、Runner、Log Analyst、Quality Checker、Result Analyst |
| ablation | Coordinator、Reader/Planner、Implementer、Interface Checker、Runner、Log Analyst、Quality Checker、Result Analyst |
| confirmation | Coordinator、Runner、Log Analyst、Quality Checker、Result Analyst |
| innovation / module trial | Coordinator、Reader/Planner、Implementer、Interface Checker、Runner、Log Analyst、Quality Checker、Result Analyst、Reviewer |
| promotion | Coordinator、Quality Checker、Interface Checker、Result Analyst、Reviewer |
| debug / smoke | Coordinator；必要时 Implementer 或 Runner，但结果默认无效 |

Runner 串行。多个 agents 可以并行读文档、审查和分析，但同一代码路径只能有一个 writer。

## 8. 强制阻断

以下情况 Router 必须阻断继续执行：

- 用户没有明确要求 push、发布、删除远端或改写历史。
- 当前任务会写 raw logs、checkpoint 或 generated figures 到 GitHub。
- 任务需要有效实验结果，但缺少 split、label mapping、class order、logits shape 或 metric semantics。
- module trial 没有 idea_id。
- idea 的 `source_status` 是 `unknown` 或 `unverified`，却要开 trial。
- promotion 只凭一次 H 提升，没有完整 manifest/result/quality/interface 证据。
- 真实实验要启动，但 GPU lock 或运行目录状态不清楚。

阻断时输出：阻断原因、需要补什么、下一步最小动作。

## 9. 每次回答的最小格式

GTPJ 工作流类任务开始时，先给出：

```text
能不能开工：
任务类型：
基于版本：
是否进入 idea_tree：
GitHub 写入：
本地写入：
联动更新：
必读协议：
启用 agents：
硬门：
当前阻塞：
下一步最小动作：
```

这个摘要是给 owner 和后续 agent 的共同入口。
