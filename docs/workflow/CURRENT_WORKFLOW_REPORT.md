# GTPJ 当前工作流汇报

本文是当前 GTPJ 工作流的汇报版说明。它帮助 owner 快速看懂现在这套系统怎么运转、GitHub 怎么配合、多 agents 怎么配合、哪些规范是硬门。

它不是新的规则源。真正的规则仍以这些文件为准：

```text
docs/workflow/WORKFLOW_ROUTER.md
docs/workflow/TASK_START_CARD.md
docs/workflow/GTPJ_WORKFLOW_SPEC.md
docs/workflow/agent_contracts.md
docs/workflow/agent_orchestration.md
docs/workflow/code_interface_contract.md
docs/workflow/quality_gate.md
docs/workflow/promotion.md
```

## 1. 当前结论

当前工作流已经完成的是“实验创新系统的治理骨架”：

- GitHub 已定位为轻量控制面：代码、配置、版本、规范、轻量实验索引、质量门、artifact 指针。
- 本地外部目录已定位为材料和资产面：论文/PDF、阅读笔记、完整创意推理、raw logs、checkpoint、实验可视化、实验统计导出。
- 多 agents 的角色和边界已规划：Coordinator、Reader/Planner、Implementer、Interface Checker、Runner、Log Analyst、Result Analyst、Quality Checker、Reviewer。
- 代码接口、评估标注、artifact 登记、结果记录和 promotion gate 已有规范入口。
- 非实验创新资产链路已经从 GTPJ 实验工作流中移除。

当前还没有完成的是“真实实验闭环产品”：

- 还没有用这套新工作流跑完一轮新的 tune / ablation / confirmation / module trial 并完整落账。
- 还没有把本地进度看板变成日常强制入口。
- 还没有通过多次真实实验把所有模板和 agents 协作细节打磨到稳定状态。

所以当前状态可以概括为：

```text
规范已落地。
工作流能开工。
真实闭环还需要通过第一轮实验验证。
```

## 2. Owner 怎么开工

Owner 不需要说“开启动卡”，也不需要自己判断任务类型。

最小输入是：

```text
我想基于 <version> 跑/做 <experiment or idea>。
```

例如：

```text
我想基于 v1 跑一个 topo loss weight 的调参。
我想基于 v1 做一个新的 token router 模块实验。
我想基于 v1 复现一下当前 baseline。
我读到一篇论文，想看看能不能转成 GTPJ 的创新点。
```

收到这种请求后，Coordinator 必须自动输出：

```text
能不能开工：
任务类型：
基于版本：
是否进入 idea_tree：
GitHub 写入：
本地写入：
必读协议：
启用 agents：
硬门：
当前阻塞：
下一步最小动作：
```

如果条件不够，Coordinator 只问一个最关键问题，不要求 owner 自己填完整流程表。

## 3. 总判断规则

最重要的两条：

```text
实验是为了调/查/验证已有东西 -> experiments，不进 idea_tree。
实验是为了证明一个新方法值得存在 -> idea_tree + module_trials。
```

这两条是当前工作流的总教官规则。

不要因为一次实验有“想法”两个字就写入创意树。只有可复用的新机制、新模块、新方法，或者可能成为新 baseline 的设计，才进入 `idea_tree/`。

## 4. GitHub 怎么合作

GitHub 不是材料仓库。GitHub 是：

```text
复现控制面
版本账本
轻量结果索引
质量门记录
agents 协作规则源
```

GitHub 要回答的问题是：

- 这个结果从哪个版本来。
- 用了哪个代码 commit / tag。
- 用了哪个配置。
- 怎么跑。
- 评估语义是什么。
- 原始证据在哪里。
- 指标是多少。
- 是否可信。
- 是否能进入下一步。

GitHub 保存：

```text
code
config
docs
schemas
workflow helper
idea_tree lightweight index
experiments lightweight records
manifest.yaml
result.yaml
result.md
quality_check.md
VERSION_TREE
EXPERIMENT_REGISTRY
artifact id / URI / sha256 / size
```

GitHub 不保存：

```text
raw logs
checkpoint
feature cache
datasets
generated experiment figures
large exported tables
full paper notes
full idea reasoning
local runtime state
local absolute paths
```

GitHub 和本地外部目录通过逻辑 URI 合作：

```text
warehouse://...
research://...
```

GitHub 只记录 URI、hash、size 和复现配置；真实大文件留在本地。

## 5. 本地目录怎么合作

### 5.1 `GTPJ_Research`

路径：

```text
D:\backup\Documents\Myself\GTPJ_Research
```

职责：

- 保存论文 PDF。
- 保存完整论文阅读笔记。
- 保存来源复核。
- 保存长版创意树。
- 保存不成熟想法、失败假设、长推理。

典型内容：

```text
papers/
notes/
source_reviews/
ideas/
IDEA_REGISTRY.yaml
```

它回答：

```text
为什么会有这个想法？
来源是否可靠？
论文 claim 是否可复核？
这个 idea 为什么可能适合 GTPJ？
```

### 5.2 `GTPJ_Warehouse`

路径：

```text
D:\backup\Documents\Myself\GTPJ_Warehouse
```

职责：

- 保存 raw logs。
- 保存 checkpoint。
- 保存实验可视化输出。
- 保存实验统计导出。
- 保存 failure cases。
- 保存 run receipts。

典型内容：

```text
runs/
logs/
checkpoints/
figures/
tables/
failure_cases/
ARTIFACT_REGISTRY.yaml
```

它回答：

```text
实验实际产生了什么？
原始日志在哪里？
checkpoint 在哪里？
实验图表和失败案例在哪里？
hash 和 size 是什么？
```

### 5.3 `.gtpj/local_paths.yaml`

路径：

```text
D:\backup\Documents\Myself\GTPJ\.gtpj\local_paths.yaml
```

职责：

- 保存本机真实路径。
- 不提交 GitHub。
- 给 helper 或 agent 找到 Research / Warehouse。

当前只应包含：

```yaml
warehouse_root: D:/backup/Documents/Myself/GTPJ_Warehouse
research_root: D:/backup/Documents/Myself/GTPJ_Research
```

## 6. 多 agents 是否参与

结论：参与，但不是每次都必须同时启动多个真实 subagent。

当前工作流把 agents 分成两层：

```text
长期角色层：GitHub 文档里保存角色职责、读写边界、失败条件。
临时执行层：真实任务中按需要启动一个或多个 agent 实例。
```

也就是说：

- 规范层面已经是多 agents 协作系统。
- 执行层面按任务复杂度决定是否真的并行调用多个 agents。
- 小任务可以由 Coordinator 单独完成。
- 大的 innovation / module trial / promotion 应启用多 agents。
- Runner 涉及 GPU，必须串行。
- 同一代码路径只能有一个 writer。
- 真实实验结束后必须留下 `agent_summary.md`，保存 agent 审计凭证，不保存完整聊天流水。

## 7. agents 怎么合作

### 7.1 角色表

| 角色 | 负责什么 | 不负责什么 |
|---|---|---|
| Coordinator | 路由任务、分配 agents、维护账本、收口结论 | 不直接跑训练、不伪造结果 |
| Reader/Planner | 读论文、读 Research、提出候选 idea 和风险 | 不跑实验、不改代码 |
| Implementer | 按授权范围改代码、写实现说明 | 不改评估语义、不越权重构 |
| Interface Checker | 检查 shape、label mapping、class order、metric semantics | 不写实现代码 |
| Runner | 按批准命令跑实验、写 Warehouse | 不写 GitHub 结果、不自行改参数 |
| Log Analyst | 解析 raw log，抽 U/S/H/ZS、best epoch 和失败阶段 | 不决定 promotion |
| Result Analyst | 判断 keep / reject / rerun / needs_confirmation / promote 建议 | 不创建 tag、不写 raw artifact |
| Quality Checker | 查 manifest/result/artifact/schema/质量门 | 不只看 H 分数 |
| Reviewer | 独立复查风险、证据链和合并安全 | 不替代 Coordinator 收口 |

### 7.2 按任务启用 agents

| 任务类型 | 推荐 agents |
|---|---|
| paper intake / idea discovery | Coordinator、Reader/Planner |
| tune | Coordinator、Runner、Log Analyst、Result Analyst、Quality Checker |
| ablation | Coordinator、Implementer、Interface Checker、Runner、Log Analyst、Result Analyst、Quality Checker |
| confirmation | Coordinator、Runner、Log Analyst、Result Analyst、Quality Checker |
| innovation / module trial | Coordinator、Reader/Planner、Implementer、Interface Checker、Runner、Log Analyst、Result Analyst、Quality Checker、Reviewer |
| promotion | Coordinator、Quality Checker、Interface Checker、Result Analyst、Reviewer |

### 7.3 串行和并行规则

可以并行：

- Reader/Planner 读论文和来源。
- Quality Checker 查证据链。
- Reviewer 查规范风险。
- Result Analyst 看历史结果。

必须串行：

- Runner 使用 GPU。
- Implementer 修改同一代码路径。
- Coordinator 写最终账本。
- promotion 创建 tag 或修改版本账本。

禁止：

- 多个 agents 同时改同一个 `INDEX.md`。
- 多个 agents 同时改同一段模型代码。
- Runner 并行抢同一块 GPU。
- 非 Coordinator 删除分支、合并分支、创建 tag。
- 非 owner 明确要求时 push。

## 8. 标准工作流闭环

### 8.1 读论文到 idea

```text
论文/PDF
  -> GTPJ_Research/papers/
  -> GTPJ_Research/notes/
  -> GTPJ_Research/source_reviews/
  -> Reader/Planner 提炼候选 idea
  -> GitHub idea_tree/inbox.md 或 idea_tree/ideas/
  -> 形成 IDEA-xxxx
```

GitHub 只放轻量来源和 idea 索引；完整阅读材料留在 Research。

### 8.2 idea 到 module trial

```text
IDEA-xxxx
  -> Interface Checker 预审接口风险
  -> Implementer 实现
  -> Runner 跑实验
  -> Warehouse 保存日志和大文件
  -> Log Analyst 抽指标
  -> Quality Checker 查证据
  -> Result Analyst 给建议
  -> Reviewer 复查
  -> keep / revise / reject / promote
```

### 8.3 普通实验到结果

```text
owner 提出实验
  -> Coordinator 路由
  -> 创建 experiments/vX/<kind>/...
  -> 复制 config.yaml
  -> Runner 运行
  -> Warehouse 保存 raw evidence
  -> GitHub 写 manifest/result/quality_check
  -> 最终结论
```

### 8.4 成功 trial 到新版本

```text
trial 记录 promotion_decision: promote
  -> promotion gate
  -> Quality Checker
  -> Reviewer
  -> config/versions/vY.yaml
  -> experiments/vY/
  -> VERSION_TREE 更新
  -> 本地 vY tag
  -> main 只保留账本
```

注意：

- promotion 不自动 push。
- promotion 不自动切换 main active code。
- 只有 owner 明确执行 `activate-version vX` 时，才切换当前运行别名。

## 9. 工作规范

### 9.1 开工前

每次 GTPJ 工作开始前必须确认：

- 当前分支。
- 工作区是否 clean。
- base version 是什么。
- 任务类型是什么。
- 是否进入 idea_tree。
- 写 GitHub 还是写 Research/Warehouse。
- 需要哪些 agents。
- 哪些 hard gates 可能阻断。

### 9.2 文件写入边界

| 内容 | 写哪里 |
|---|---|
| 完整论文、完整阅读笔记、完整创意推理 | `GTPJ_Research` |
| 轻量 idea 索引 | `idea_tree/` |
| 实验配置、manifest、result、quality_check | `experiments/` |
| raw logs、checkpoint、实验可视化、实验统计导出 | `GTPJ_Warehouse` |
| 运行中状态 | `.gtpj_runtime/` |
| 本机路径 | `.gtpj/local_paths.yaml` |

### 9.3 Git 规范

- `main` 是唯一长期分支。
- `v1`、`v2`、`v3` 是 tag，不是长期分支。
- 实验分支必须带 base version。
- trial 可以有永久 `trial/...` tag。
- 不自动 push，除非 owner 明确要求。
- 不删除远端、不重写历史，除非 owner 明确要求。

### 9.4 评估和接口硬门

以下任一不清楚，实验结果无效：

- seen/unseen split。
- label mapping。
- class order。
- logits shape。
- metric calculation。
- U/S/H/ZS 语义。
- 数据 cache 版本。
- 新模块关闭后是否能回到 base behavior。

如果这些不清楚：

```text
Runner 必须拒跑。
已经跑出的结果只能标记 blocked / rerun / rejected。
不能 keep。
不能 promote。
```

### 9.5 结果记录硬门

每个正式结果必须有：

```text
config.yaml
manifest.yaml
result.yaml
result.md
quality_check.md
agent_summary.md
external artifact URI
sha256
size_bytes
code commit/tag
base_version
```

没有这些，不算完整证据。

## 10. 当前文件地图

最重要入口：

```text
docs/workflow/CURRENT_WORKFLOW_REPORT.md   # 本汇报
docs/workflow/WORKFLOW_ROUTER.md           # 总教官
docs/workflow/TASK_START_CARD.md           # 启动卡
docs/workflow/GTPJ_WORKFLOW_SPEC.md        # 总规范
docs/workflow/IMPLEMENTATION_STATUS.md     # 落地状态
docs/PROJECT_STRUCTURE.md                  # 项目结构总账本
docs/GITHUB_GOVERNANCE.md                  # GitHub 治理规范
```

agents 入口：

```text
docs/workflow/agent_contracts.md
docs/workflow/agent_report_policy.md
docs/workflow/agent_orchestration.md
docs/workflow/agents/
```

实验入口：

```text
docs/workflow/experiment_protocol.md
docs/workflow/module_trial_protocol.md
docs/workflow/result_index_protocol.md
docs/workflow/quality_gate.md
docs/workflow/promotion.md
```

工具入口：

```text
workflow/gtpj_workflow.py
```

本地执行副本：

```text
C:\Users\Administrator\.codex\skills\gtpj-workflow
```

如果 GitHub 文档和本地 skill 冲突，以 GitHub 文档为准，并同步修复 skill。

## 11. 当前工作流是否搭建完

回答要分两层：

```text
规范层：基本搭建完。
真实闭环层：还没有完成第一轮正式验证。
```

已经完成：

- GitHub 轻量边界。
- Research / Warehouse 本地边界。
- 创意树轻量索引结构。
- 实验记录结构。
- artifact 登记规则。
- 多 agents 角色边界。
- Git 分支/tag/版本规则。
- 质量门和接口硬门。
- 非实验创新资产链路已移除。

还需要通过真实实验验证：

- 一次低风险 tune 或 confirmation。
- 一次 module trial。
- 一次完整 record-result。
- 一次 Quality Checker / Result Analyst / Reviewer 收口。
- 必要时一次 promotion 干跑。

## 12. 下一步建议

下一步建议不要马上开大创新实验，而是先做一轮最小闭环：

```text
1. 选择 v1。
2. 跑一个低风险 tune 或 confirmation。
3. 让 Runner 产生 Warehouse 日志。
4. 用 record-result 写回 GitHub 轻量结果。
5. 让 Quality Checker 检查证据链。
6. 让 Result Analyst 写 keep/reject/rerun 判断。
7. 根据暴露的问题修订模板和规范。
```

完成这轮后，工作流才算从“规范搭好”进入“真实可用”。
