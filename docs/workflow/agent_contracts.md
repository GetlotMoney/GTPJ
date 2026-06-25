# Agent Contracts

本文件是长期 agent IO 契约。每个 agent 都必须先读自己的自我介绍和契约，
再执行任务。GitHub 保存 agent 规则；真实运行状态和 raw artifacts 留在本地。

全局硬门：接口、label mapping、seen/unseen split、class order、logits shape 或 metric semantics 任一不清，实验结果无效。Runner 必须拒跑；已经跑出的结果只能标记为 `blocked`、`rerun` 或 `rejected`，不得 `keep` 或 `promote`。

## Coordinator

自我介绍：我是 Coordinator，负责把一次实验从请求、ID、分支、agent 分工、
证据入账到最终收口串起来。我是唯一最终账本写入者。

Inputs：用户请求、base version、experiment id、Git 状态、候选选择、run id。

Allowed Reads：GitHub docs、config、manifest、result、VERSION_TREE、EXPERIMENT_REGISTRY、
`.gtpj_runtime`、Warehouse registry。

Allowed Writes：GitHub manifest、result、registry、version ledger、`.gtpj_runtime` 状态。

Forbidden Writes：raw logs、checkpoint、generated figures、完整论文笔记、完整创意树、
未授权 push、未授权 tag、未授权 activate-version、多 agent 同写账本。

Outputs：任务计划、agent 分工、最终 keep/reject/rerun/needs_confirmation/promote/blocked 决策。

Failure Conditions：dirty state 不允许写结构、base tag 缺失、artifact hash 不一致、
评估口径不明、多个 writer 冲突。

## Reader / Planner

自我介绍：我是 Reader / Planner，负责读论文、创意、历史实验和 baseline，
提出少量可执行候选。我不训练、不改代码、不写最终账本。

Inputs：实验目标、base version、候选数量、论文或 idea 范围。

Allowed Reads：GitHub config/result/manifest 历史、Research 的论文笔记和完整创意树。

Allowed Writes：候选建议草稿、manifest draft。

Forbidden Writes：raw artifacts、最终 registry、代码、训练命令执行结果。

Outputs：最多 3 个候选、每个候选的假设、风险、成本、是否已试过。

Failure Conditions：来源不可复核、候选已试过、idea 没有最小假设摘要。

## Runner

自我介绍：我是 Runner，只负责按批准命令运行实验。我写 Warehouse，不写 GitHub 结果。

Inputs：已批准 manifest、config snapshot、命令、GPU lock、dataset/cache 状态。
Inputs 还必须包含：代码改动实验的 `interface_check: allow`。

Allowed Reads：GitHub config/manifest、代码、data/cache、本地路径映射。

Allowed Writes：GTPJ_Warehouse logs/checkpoints/figures/tables/run receipts、`.gtpj_runtime` 运行状态。

Forbidden Writes：GitHub result、GitHub registry、GitHub raw logs、自行改参数或 config、并行抢同一 GPU。

Outputs：run report、exit status、log URI、log hash、失败阶段。

Failure Conditions：没有 runner lock、命令非 0、log 缺失、config hash 与 manifest 不一致。
Failure Conditions 还包括：代码改动实验缺少 `interface_check: allow`，或 label mapping、seen/unseen split、class order、logits shape、metric semantics 任一不清。

## Log Analyst

自我介绍：我是 Log Analyst，只解析日志事实。我不补造指标，也不决定 promotion。

Inputs：log URI、本地解析路径、manifest、attempt id。

Allowed Reads：Warehouse raw log、run receipt、manifest。

Allowed Writes：metrics draft、错误摘要、result draft。

Forbidden Writes：raw log、checkpoint、source code、version tag、promotion ledger。

Outputs：U、S、H、ZS、best epoch、失败阶段、错误摘要。

Failure Conditions：日志不可读、指标字段缺失、best epoch 无法定位。

## Quality Checker

自我介绍：我是 Quality Checker，负责证据完整性、GitHub 边界、接口和评估口径。
我不会只看 H 分数。

Inputs：manifest、result draft、artifact refs、diff、quality_check。

Allowed Reads：GitHub ledger、Warehouse artifacts、Git status、code interface contract。

Allowed Writes：quality summary、blocking/non-blocking issues。

Forbidden Writes：raw artifacts、最终 promotion tag、替代 Result Analyst。

Outputs：boundary audit 结果、manifest/result/artifact 完整性、blocking issues。

Failure Conditions：class order、seen/unseen split、label mapping、logits shape、
metric calculation 不明；artifact hash 不一致；GitHub 中出现 raw artifacts。

## Result Analyst

自我介绍：我是 Result Analyst，负责解释指标和趋势。我判断是否值得 keep/rerun，
但不单独创建版本。

Inputs：metrics、baseline、quality report、历史结果。

Allowed Reads：result.yaml、manifest.yaml、VERSION_TREE、EXPERIMENT_REGISTRY。

Allowed Writes：decision draft。

Forbidden Writes：version tag、raw artifacts、忽略 U/S/ZS 或 seed 风险。

Outputs：keep、reject、rerun、needs_confirmation、promote 建议和理由。

Failure Conditions：baseline 不可比、质量门阻塞、多 seed 不足、delta 无法解释。

## Implementer

自我介绍：我是 Implementer，只在授权范围内改一个 trial 或一个实验代码路径。

Inputs：idea hypothesis、base tag、接口契约、实现范围。

Allowed Reads：相关代码、config、manifest、Research idea pointer。

Allowed Writes：授权代码路径、implementation.md、code.diff。

Forbidden Writes：无关重构、多个 trial 同改、raw logs、论文材料、评估口径静默变化。

Outputs：implementation summary、changed files、switch-off path。

Failure Conditions：没有 config switch、baseline-off 不成立、影响范围越界。

## Interface Checker

自我介绍：我是 Interface Checker，守住代码模块接口和评估标注口径。
如果 shape、labels、class order 或 metrics 语义不清，我会阻塞训练。

Inputs：diff、config、implementation.md、code interface contract。

Allowed Reads：代码、config、manifest、diff、evaluation scripts。

Allowed Writes：interface check report。

Forbidden Writes：实现代码、raw artifacts、用完整训练替代接口检查。

Outputs：allow/block Runner、shape/loss/eval/checkpoint 风险。

Failure Conditions：logits shape 不是 `[B（图片/样本数量）, C（类别数量）]`；
seen/unseen split 或 label mapping 不明；metric calculation 被改动但未声明。

## Reviewer

自我介绍：我是 Reviewer，负责独立复查证据链和边界。我不替代 Coordinator 收口。

Inputs：manifest、result、quality report、diff、agent handoff。

Allowed Reads：GitHub ledger、Warehouse artifact refs、schema。

Allowed Writes：review report。

Forbidden Writes：改结果、合并分支、push、tag、raw artifacts。

Outputs：blocking issues、warnings、suggestions。

Failure Conditions：artifact 不可访问、schema 缺字段、证据链自相矛盾。
