# GTPJ V6 精简前工作流完整归档

```yaml
status: historical
command_authority: none
snapshot_date: 2026-08-13
source_commit: 60e81c4a0086f38865dfab4b148302f6d49f55cb
archived_files:
  - AGENTS.md
  - docs/workflow/START_HERE.md
  - docs/workflow/WORKFLOW_KERNEL.md
  - docs/workflow/playbooks/tune.md
  - docs/workflow/playbooks/ablation.md
  - docs/workflow/playbooks/confirmation.md
  - docs/workflow/playbooks/innovation.md
  - docs/workflow/playbooks/promotion.md
  - docs/workflow/playbooks/mixed_campaign.md
  - docs/workflow/playbooks/autonomous_campaign.md
  - docs/workflow/playbooks/paper_intake.md
  - docs/workflow/playbooks/paper_to_experiment.md
  - docs/workflow/README.md
  - docs/workflow/core/QUICK_START.md
  - docs/workflow/core/WORKFLOW_ROUTER.md
  - docs/workflow/core/TASK_START_MINI.md
  - docs/workflow/core/TASK_START_CARD.md
  - docs/workflow/core/AGENT_RUNTIME_HARD_GATE.md
  - docs/workflow/core/WORKFLOW_VERSION.md
  - docs/workflow/protocols/parameter_matrix_protocol.md
  - workflow/README.md
```

本文件集中保存 V6 精简前的三份核心工作流、九张活动执行卡、七份旧 README/core 导航、旧参数矩阵协议和旧 helper README 原文，只用于解释历史实验和审计历史，不得用于启动新任务。当前业务只读取仓库根目录 `AGENTS.md`、`docs/workflow/START_HERE.md`、`docs/workflow/WORKFLOW_KERNEL.md` 和任务所需的 V6 执行卡或协议。

---

# 归档六：docs/workflow/protocols/parameter_matrix_protocol.md（V6 替换前）

# 参数矩阵规范

```text
policy_status: active
policy_version: DATA-FRAMEWORK-LEDGER-V1
effective_date: 2026-08-05
scope: 所有框架的 tune、ablation、innovation、confirmation；旧 module trial attempt 只作兼容
```

## 这条规则解决什么问题

一轮 50 或 100 个任务属于一个具体实验项，但里面有很多个实际运行。以后每一个实际运行都必须有自己的一行 `RUN-xxx`，避免只留下 `ATTEMPT` 批次摘要，导致后来不知道某个参数是否已经试过。

不保存原始日志和模型到 GitHub：它们仍留在 Warehouse。本规范只保存轻量、可查、可复现的参数和结果索引。

## 固定文件

每个新实验目录必须有：

```text
PARAMETER_MATRIX.csv   # 机器校验、查重和结果回填的唯一来源
PARAMETER_MATRIX.md    # 由 CSV 生成，给人直接阅读
```

CSV 一行对应一个真实任务，不是一行对应整个 50/100 任务批次。Markdown 只是同一数据的阅读版，禁止分别手工维护两份内容。

旧 `ATTEMPT / DR` 写入 `run_id`、`work_item_id` 或 `legacy_ref`。无法可靠恢复逐任务参数时，
只允许写 `legacy_summary_only`，并明确它是历史摘要，不得把一条摘要冒充 50 个运行。

如果手工修改了 CSV，必须立刻重新生成阅读版；校验和正式入账都会检查两份内容是否一致：

```powershell
python workflow\gtpj_workflow.py refresh-parameter-matrix-view --path <PARAMETER_MATRIX.csv>
python workflow\gtpj_workflow.py validate-parameter-matrix --path <PARAMETER_MATRIX.csv> --require-ready
```

## 每行必须回答的事

```text
job_id                 这一个具体任务的编号
job_kind               调参 / 消融 / 对照 / 原样复跑
status                 草稿、已冻结、运行中、完成、失败、跳过、取消或历史仅摘要
base_version           基于哪个版本
base_config_sha256     基线配置的指纹
code_ref               使用的代码标签或提交
config_snapshot_ref    这一行实际训练所用配置快照的位置
changed_parameters     相对基线只改了什么，使用 JSON 对象
config_fingerprint     完整配置的指纹，用于查重
repeat_of              若是原样复跑，明确写复跑哪一行
seed                   随机种子
run_start_receipt_sha256 启动收据的固定哈希
run_command_sha256      实际训练命令的固定哈希
run_log_sha256          helper 封口后的完整训练日志哈希
run_exit_code           helper 真实子进程的退出码
U/S/H/ZS、best_epoch   实际结果；未跑时为空
decision               保留、放弃、继续确认等决定
artifact_ref           Warehouse 中结果摘要的位置
artifact_manifest_sha256 该任务证据清单的固定哈希；首次回填后不可更换
```

表中只写“这次改了什么”；完整配置仍由每个任务的配置快照保存。不要把数百个没有变化的字段重复塞进表格。基线中存在、但本次配置明确删除的字段写成 `"<removed>"`，避免把换框架误写成只改了一个新增参数。参数值按 JSON 保留真实类型，例如布尔值 `false` 与字符串 `"false"` 必须能区分；日期要显式加引号，`NaN` 和无穷值不允许进入参数表。配置既可直接写值，也可用只含 `value` 的单键包装；同一字典同时写 `value` 和其他键会被拒绝，避免把普通字典误认成包装后漏记变化。

## 开跑前的硬步骤

```text
1. 生成参数矩阵。
2. 逐行看清任务数、参数变化和复跑对象。
3. 查重：同一个 config_fingerprint 已经存在时，必须改参数，或明确写 repeat_of。
4. 把参数矩阵和计划一起提交为 pre-run freeze commit；训练与结果入账都引用这个提交。
5. 通过 `prepare-run-start-receipt` 一次完成“生成启动收据 + 直接拉起训练进程 + 收集输出”，不能再手工把训练命令拆出去运行。
6. 通过参数矩阵校验后，才能生成正式 Runner 批次。
```

版本级 tune、ablation、confirmation 的训练入口目前由外部训练脚本执行。因此 `new-experiment`
只会先建立一行 `draft` 草稿；在运行训练脚本前必须填完 CSV，并用下面命令把实际 `config.yaml`
的完整指纹写入该行，再校验并提交冻结。

```powershell
python workflow\gtpj_workflow.py freeze-parameter-matrix `
  --path experiments/vX/tune/TUNE-xxx/PARAMETER_MATRIX.csv `
  --config experiments/vX/tune/TUNE-xxx/config.yaml --job-id TUNE-xxx-001
python workflow\gtpj_workflow.py validate-parameter-matrix `
  --path experiments/vX/tune/TUNE-xxx/PARAMETER_MATRIX.csv --require-ready
```

这一步只能把一行从 `draft`（草稿）变成 `frozen`（已冻结），不能再次冻结或修改已冻结、运行中或完成的行，并会重新生成阅读版。若每一行有不同配置快照，就每行分别执行一次。随后冻结的
`config_snapshot_ref`、种子和完整配置指纹会在正式入账时再次核对。
单独冻结一行不会要求同批其余草稿已经填完；全部行都冻结后，再执行一次
`validate-parameter-matrix --require-ready` 作为整批放行检查。

冻结提交完成后，用下面这个唯一入口生成启动收据并直接启动训练：

```powershell
python workflow\gtpj_workflow.py prepare-run-start-receipt `
  --path <PARAMETER_MATRIX.csv> --config <实际训练配置> --job-id <JOB-ID> `
  --run-id <RUN-ID> --pre-run-freeze-commit <commit> `
  --command "<实际训练命令>" --receipt <run_start_receipt.json> --log <train.log>
```

正常启动时，这个命令拒绝只存在收据或只存在日志的半套文件，只能在训练前成对创建。若收据和日志已经同时存在，且都能证明来自同一行、同一 Run、同一冻结提交和同一训练命令，重复执行同一条命令只会恢复或复核结束封存，不会再次训练。首次创建时必须正好位于指定的冻结提交，且工作树没有未提交变化；命令只能直接调用 Python，或使用 `conda run ... python`，不能套 `cmd /c echo`、PowerShell 输出命令或多个 shell 命令。`--config` 的实际参数必须精确等于这一行冻结的配置，`--conf`、`--con` 等缩写一律拒绝；训练入口本身也关闭 argparse 的参数缩写。训练入口脚本必须在仓库内、存在于冻结提交且内容没有变化。启动收据会记录训练入口相对路径及其冻结内容哈希。

helper 会先准备临时收据和临时日志，再把该行从 `frozen` 改成 `running`，写入唯一的 Run 编号、收据路径、收据 SHA-256 和命令 SHA-256，最后发布收据和日志首行；其中任何一步失败，参数表会恢复到原来的 `frozen` 状态并清理本次临时文件。随后 helper 自己用无 shell 的子进程直接执行 `--command`，把进程号、开始时间、退出码和完整标准输出/错误输出追加到同一日志。进程结束后、等待参数表锁之前，helper 会额外创建一次性的 `*.finish.json` 结束收据，先固定原始日志哈希、退出码、进程号和起止时间。子进程无法启动时，该行恢复为 `frozen` 并清理收据和日志；子进程已经启动但非零退出时，该行明确写成 `failed`，保留收据、退出码和日志供排障，不能一直停在 `running`。

进程结束标记必须独占日志最后一行；即使训练程序最后一段输出没有换行，helper 也会先补换行再写结束标记。helper 随后把整份日志的 SHA-256 和退出码写回参数表，相当于给日志“封口”；正式入账只解析开始标记和结束标记之间的真实进程输出，并同时核对日志哈希、退出码和标记顺序。任何在结束标记后补写指标、改写中间输出或手工伪造成功退出码的日志都会被拒绝。

同一张参数表的所有改写动作共用同一把锁，不只是领取启动收据。冻结配置、刷新阅读版、登记普通结果、准备动态批次和回填动态结果都会在锁内重新读取并检查当前表，再一起写回 CSV 与 Markdown，避免两个进程各自拿旧表覆盖对方。训练进程已经结束时，封存步骤会等待最多 30 秒让短暂占锁的写入完成；若仍未封存，释放占锁后原样重跑 `prepare-run-start-receipt`，helper 会用一次性结束收据核对原始日志哈希、结束标记、退出码和进程身份后补齐参数表，不会重复训练，也不会接受超时窗口中被改写的日志。

即使有人绕过这一步单独运行训练，`record-result` 也会拒绝把结果写成正式账本。它只会把指标回填到已冻结的对应行。旧模块 Attempt 仍可由 `record-module-attempt` 做历史兼容核验，但它不能创建新的正式实验。两个结果命令都必须显式传入 `--pre-run-freeze-commit <commit>` 和 `--run-start-receipt <run_start_receipt.json>`；helper 会核对启动收据与结束收据、真实文件哈希、训练入口路径与冻结哈希、日志首行、进程标记、日志封口哈希和文件先后关系。正式账本中的代码提交固定写训练前的冻结提交，不会被训练后推进的当前 `HEAD` 偷换；helper 自己产生的参数表运行状态、两份收据和日志也不会被误判成训练代码变脏。

`record-result` 在写正式框架账本前先取得整张参数表的锁；历史兼容命令 `record-module-attempt` 在补旧证据前也会锁表并检查旧 `ATTEMPTS.md`。两者用途不同：前者是今后的正式入口，后者只修补历史证据。

下面的 `init-parameter-matrix` + 旧 Attempt 路径只用于修复规范生效前已经存在的历史任务，不得用于发起新实验：

```powershell
python workflow\gtpj_workflow.py init-parameter-matrix `
  --directory experiments/v5/ablation/ABLATION-001_local_branch_effect `
  --job-id RUN-001 --job-kind ablation --base-version v5 `
  --base-config experiments/v5/config.yaml `
  --config experiments/v5/ablation/ABLATION-001_local_branch_effect/config.yaml --seed 5
```

`SYS-WORKFLOW-V5` 启用后，旧动态路由 Trial/Attempt 入口只作历史回查。不得再创建新的旧式动态路由参数表，
也不得用旧正式 batch planner 启动训练。新动态路由想法必须先成为所属正式框架的 innovation 实验，
再使用该实验目录自己的 `PARAMETER_MATRIX.csv`、`freeze-parameter-matrix` 和
`prepare-run-start-receipt`。旧 planner 只允许 `--debug-smoke`，产物不能进入正式证据。

标准实验的检查入口是：

```powershell
python workflow\gtpj_workflow.py validate-parameter-matrix `
  --path experiments/v5/innovation/INNOVATION-xxx_slug/PARAMETER_MATRIX.csv `
  --expected-jobs <任务数> --require-ready
```

每行 `code_ref` 必须等于 `EXPERIMENT.yaml` 绑定的母版 Tag，`run_id` 必须等于本次正式运行编号。
为 `RUN-A` 冻结的表不能拿去回填 `RUN-B`，结果回填也不能覆盖既有结果。

## 跑完后

下面的同步命令只用于收回规范启用前已经实际运行的旧动态路由结果，不得用它创建新批次：

```powershell
python workflow\gtpj_workflow.py sync-dynamic-routing-matrix --run-dir .gtpj_runtime/batches/<RUN_ID>
```

回填后再次校验，再写 `result.yaml`、`result.md` 和质量检查。每一行的 `artifact_ref`
必须指向该任务在 Warehouse 的目录，不得只指向 `.gtpj_runtime` 运行缓存。参数列属于运行前冻结内容；
跑完后只能补状态、指标、决策、Warehouse 引用和证据清单哈希，不能暗中改参数。首次回填后，
`artifact_manifest_sha256` 会固定在这一个任务行里；后续再次同步必须与它完全相同，不能替换
manifest 后再用新的哈希冒充同一次结果。
回填还必须核对逐任务 Warehouse 目录、`artifact_manifest.json`、manifest 哈希和其中的
`job_id/run_id/attempt_id`，不能只凭一个非空路径入账。服务器 Runner 会把每个真实 manifest 复制到运行目录的 `artifact_manifests/<JOB-ID>.json`；取回运行摘要时必须把这个目录一起取回。本地同步缺少真实文件、文件哈希不符或身份不符时一律拒绝，不能用 summary.csv 里自报的一串哈希代替真实文件。

对于“按前序排名复跑”的动态任务，开跑前可暂写 `top_rank:n`；回填时 helper 必须读取完整的
前序探索结果，按 H 从高到低、任务号从小到大处理同分情况，重新算出第 n 名，再核对服务器给出的
`resolved_from_job_id`。只有来源任务存在还不够；来源不是实际第 n 名、探索摘要不完整或 H 不是数字时，
回填都会拒绝。

服务器 Runner 为每个 Run/Attempt/任务使用一个全新 Warehouse 目录。目录只要已经存在，即使为空，
Runner 也会拒绝复用，避免重跑或串线覆盖旧日志、配置、模型和 manifest。`summary.csv.attempt_id`、
manifest 内的 `attempt_id` 与 `warehouse_attempt_id` 还必须同时等于冻结计划里的 Attempt 编号。

## 正式实验放在哪里

```text
版本级调参：experiments/vX/tune/TUNE-xxx/PARAMETER_MATRIX.*
版本级消融：experiments/vX/ablation/ABLATION-xxx/PARAMETER_MATRIX.*
版本级确认：experiments/vX/confirmation/CONFIRM-xxx/PARAMETER_MATRIX.*
创新实验：experiments/vX/innovation/INNOVATION-xxx/PARAMETER_MATRIX.*
旧模块目录：只读兼容；通过 legacy_ref 映射回上述四类正式账本
```

版本文件只说明“版本为什么变化”；参数矩阵负责完整记录“每一个候选怎么试、结果如何、为什么留下或停止”。

## 历史记录迁移

历史 Attempt 和 v3/v4 不能补造数据。迁移时只允许从 Warehouse 的 `plan.json`、`summary.csv`、每任务配置和日志登记中恢复；恢复不了的行可以标成 `legacy_summary_only`，但这种行不能开跑、不能写成 keep/best，也不能进入 promotion。旧目录确实没有矩阵时，结果迁移必须显式使用 `--legacy-summary-only --legacy-source-commit <旧提交>` 和非提升决定。helper 会核对该目录在旧提交中真实存在、当时没有参数矩阵，而且参数矩阵规范尚未生效；刚新建目录后删表无法冒充历史。写入后 `legacy_summary_only` 身份永久保留，普通重写和 `--overwrite-ledger` 都不能清除。后续 `sync-trial-summary` 也会继续拒绝把它改写成 keep、best 或 promote。

参数矩阵硬门在项目采纳本规范后由 helper 和 Git 历史共同固定。删除本规范文件或把 `policy_status` 改成 `inactive` 只会让正式命令直接失败，不会退回旧流程；尚未采纳过本规范的旧仓库仍可先完成迁移再启用。

跨历史矩阵复跑时，`repeat_of` 使用 `matrix:<历史 PARAMETER_MATRIX.csv 路径>#<job_id>`；同一张表内则直接写原 `job_id`。helper 会确认来源任务存在，且版本、代码引用和完整配置指纹完全相同；不同参数不能借用一个旧任务号绕过查重。

---

# 归档七：workflow/README.md（V6 替换前）

# GTPJ Workflow Helper

> 2026-08-08 起，默认实验入口改为 `SYS-WORKFLOW-V6` 五步短流程。本文后续的 `agent_runtime.yaml`、`prepare-run-start-receipt`、多层审核和旧动态批次命令只作历史兼容或按需工具，不再是普通实验与论文实验的默认门槛。新实验优先使用：唯一实验提交、配置与参数表、一次 clean/data/GPU 检查、直接训练到独立 RUN 目录、结果回填。

`workflow/gtpj_workflow.py` 是 GTPJ 的结构辅助入口。它不训练模型、不 push、不改远端、不自动发布；它只负责创建标准目录、写轻量账本、检查 GitHub 边界和验证基础治理状态。

当前主规范：

```text
docs/GITHUB_GOVERNANCE.md
docs/PROJECT_STRUCTURE.md
docs/PROJECT_STATUS.md
docs/workflow/FRAMEWORK_EXPERIMENT_STANDARD.md
docs/workflow/reference/artifact_policy.md
docs/workflow/reference/result_index_protocol.md
docs/workflow/protocols/quality_gate.md
docs/workflow/reference/agent_contracts.md
```

当前 active mainline code 是 `GTPJ-v5 / tag v5`。`best_observed_H=74.54`，
`confirmed_H=74.44`，仍需和更强 confirmed reference `v3/CONFIRM-001 local-v3-054 confirmed_H=74.47` 区分表述。当前 IDEA-0003/TRIAL-001 的研究最高单次为 `H=75.11`，但 exact repeat 未还原，不能写成 confirmed 或 promoted 结果。
`validate` 会检查本地 baseline tag 是否能读到对应记录；`validate-remote`
用于核对远端 `main` 和 baseline tags 是否与本地治理事实对齐。

任何状态检查、结果比较、promotion 或 tag 前，先用只读命令判断复现状态：

```bash
python workflow/gtpj_workflow.py repro-status --version v5
```

如果输出 `verdict: needs_confirmation`，该版本只能作为 active code / unconfirmed reference，
不能表述为 confirmed baseline。

## Owner Phrases

owner 日常可以直接说人话口令，Coordinator 负责映射到下面的结构命令和协议：

| 口令 | 默认动作 |
|---|---|
| `查状态` | 运行只读状态检查和必要的结构检查。 |
| `复现` | 走当前 active baseline 的 confirmation 准备；未要求正式证据时优先最快合规路径。 |
| `调参` | 先用 `tune-suggest` 生成最多 3 个候选，不自动训练。 |
| `消融` | 先确定目标框架和要关闭的因素，再在该框架的 ablation 账本建计划。 |
| `开新模块` | 从当前 active baseline 的 selected ready idea 队列自动选择一个 module trial。 |
| `试这个：...` | 先判断是一句 local heuristic idea、idea inbox，还是可进入 trial 的候选。 |
| `继续上一个` | 找到上一个正式框架实验；旧 Trial/Attempt 只作为追溯链接。 |
| `升版本` | 检查 promotion gate。 |
| `切版本` | 区分 set-current-version 和 activate-version；后者必须 owner 明确授权。 |

这些口令的正式定义见 `docs/workflow/core/QUICK_START.md` 和 `docs/workflow/core/TASK_START_MINI.md`。

## Commands

```bash
# status / validation
python workflow/gtpj_workflow.py start --phrase "开新模块"
python workflow/gtpj_workflow.py status
python workflow/gtpj_workflow.py todo-status
python workflow/gtpj_workflow.py refresh-todo
python workflow/gtpj_workflow.py repro-status --version v5
python workflow/gtpj_workflow.py validate
python workflow/gtpj_workflow.py validate-remote
python workflow/gtpj_workflow.py audit-boundary

# tune suggestion
python workflow/gtpj_workflow.py tune-suggest --version v5

# framework tune example
python workflow/gtpj_workflow.py validate-framework-templates
git switch -c exp/v1/tune/tune-001-topo008 <TEMPLATE_TAG>
python workflow/gtpj_workflow.py new-experiment --version v1 --kind tune --exp-id TUNE-001 --slug topo008
# 填写 experiments/v1/tune/TUNE-001_topo008/PARAMETER_MATRIX.csv 的真实参数、seed 和目的后：
python workflow/gtpj_workflow.py freeze-parameter-matrix --path experiments/v1/tune/TUNE-001_topo008/PARAMETER_MATRIX.csv --config experiments/v1/tune/TUNE-001_topo008/config.yaml --job-id RUN-001
python workflow/gtpj_workflow.py validate-parameter-matrix --path experiments/v1/tune/TUNE-001_topo008/PARAMETER_MATRIX.csv --require-ready
# 提交上述冻结表后，才运行训练。
python workflow/gtpj_workflow.py runner-lock --run-id RUN-20260625-001 --experiment-id TUNE-001
python workflow/gtpj_workflow.py prepare-run-start-receipt --path experiments/v1/tune/TUNE-001_topo008/PARAMETER_MATRIX.csv --config experiments/v1/tune/TUNE-001_topo008/config.yaml --job-id RUN-001 --run-id RUN-001 --pre-run-freeze-commit <FREEZE_COMMIT> --command "python train_GTPJ_CUB.py --config experiments/v1/tune/TUNE-001_topo008/config.yaml" --receipt train_log/tune.run_start.json --log train_log/CUB/<log>.txt
python workflow/gtpj_workflow.py record-result --version v1 --kind tune --exp-id TUNE-001 --slug topo008 --matrix-job-id RUN-001 --parameter conditional_text_ratio --old-value 0.008 --new-value 0.006 --seed 5 --log train_log/CUB/<log>.txt --pre-run-freeze-commit <FREEZE_COMMIT> --run-start-receipt train_log/tune.run_start.json --command "python train_GTPJ_CUB.py --config experiments/v1/tune/TUNE-001_topo008/config.yaml" --decision keep
python workflow/gtpj_workflow.py runner-unlock --run-id RUN-20260625-001

# idea and version view
python workflow/gtpj_workflow.py new-idea --idea-id IDEA-XXXX --slug short_name --title "short name" --source-type paper --source-ref "<source>" --source-status verified --base-version v1 --global-score 50 --version-score 50 --applicability direct
python workflow/gtpj_workflow.py set-current-version --version v1

# framework innovation example
python workflow/gtpj_workflow.py validate-framework-templates
git switch -c exp/v1/innovation/innovation-001-short-name <TEMPLATE_TAG>
python workflow/gtpj_workflow.py new-experiment --version v1 --kind innovation --exp-id INNOVATION-001 --slug short_name
# 填写 innovation 实验的 PARAMETER_MATRIX.csv；确认晋级后再注册新的同级正式框架和 Tag。
```

## Boundary Rules

- `new-experiment` 只在干净且命名准确的 `exp/vX/<type>/...` 分支运行；分支 `HEAD` 必须正好等于 `TEMPLATE.yaml` 登记的母版 commit，并生成 `EXPERIMENT.yaml`。
- `start --phrase "..."` is read-only: it prints the owner-facing mini start card and never creates branches, files, or runs.
- `new-trial`、`record-module-attempt` 和 `sync-trial-summary` 仅用于维护迁移前的旧 Trial/Attempt 证据，不是新实验入口。
- `record-result` parses an external log, computes `sha256` and `size`, writes `manifest.yaml`, `result.yaml`, `result.md`, README, and indexes, but never copies the raw log into GitHub.
- 兼容命令 `record-module-attempt` 仍可维护旧目录，但任何新运行必须登记到所属正式框架的正式实验和参数表。
- `closeout-check` is read-only: it verifies attempt evidence, trial root files, module-trial index, idea-tree evidence, and Warehouse artifacts are connected.
- `audit-boundary` blocks raw logs, checkpoints, generated images, feature caches, and copied-log evidence from entering GitHub.
- Historical `GTPJ-v1` baseline raw log has been migrated to `GTPJ_Warehouse`; GitHub keeps only artifact id, URI, hash, size, config, result, and quality records.

## Interface And Evaluation Rules

Experiments that change code, data flow, scoring, loss, or evaluation must satisfy `docs/workflow/protocols/code_interface_contract.md`.

If interface, label mapping, seen/unseen split, class order, logits shape, or metric semantics are unclear, the experiment is invalid evidence. Runner must refuse to run it; already produced results must be marked `blocked`, `rerun`, or `rejected`, not `keep` or `promote`.

## Runtime Notes

`runner-lock` and `runner-unlock` use `.gtpj_runtime/gpu_runner.lock` as a local file lock. This lock is not tracked by Git and does not replace checking actual GPU state.

The current OpenClaw/Codex runtime entrypoints, and any future runtime integration, must use the same repository docs, templates, schemas, and CLI checks.

## 参数矩阵入口（2026-08-04 起）

新的正式实验必须先有逐任务参数表，不能只保留批次总结果。先填写 `PARAMETER_MATRIX.csv`，再用 `freeze-parameter-matrix` 把实际配置快照、种子和完整指纹冻结并生成阅读版；通过 `validate-parameter-matrix --require-ready` 后提交 pre-run freeze commit。随后运行 `prepare-run-start-receipt`：它不再只写一张收据，而是由 helper 亲自拉起冻结命令并把进程开始、退出和完整输出写进同一个日志；`--conf` 等配置参数缩写会被拒绝。所有参数表改写动作共用同一把锁。结果登记时必须同时提供 `--pre-run-freeze-commit` 与 `--run-start-receipt`。`record-result` 和历史补录命令会拒绝未准备好、阅读版过期或和实际配置、种子、训练入口、进程标记不一致的表，并把指标回填到对应行。`SYS-WORKFLOW-V5` 下旧动态路由矩阵创建和正式 batch planner 已停用；`sync-dynamic-routing-matrix` 只允许收回规范启用前已经运行的历史结果。完整命令和规则见 `docs/workflow/protocols/parameter_matrix_protocol.md`。

---

# 归档一：AGENTS.md

# GTPJ Agent 规则

## 2026-08-08 实验短流程（最高优先级）

本节覆盖本文件后面仍保留的旧复杂条款。旧的多层 `agent_runtime.yaml`、命名线程、三轮审核、Git bundle、多层收据、永久 claim、专用控制器和二次冻结，只用于回查已经发生的历史实验，今后不再作为普通实验或论文实验的整套默认流程。但凡真正启动正式 Runner，仍必须使用本文件后面规定的当前最小版 `agent_runtime.yaml`，并通过对应的运行前检查；本句不豁免正式训练安全门。

普通问答、Git 状态查询、分支比较、概念解释，以及不改变 workflow 门槛、schema、解析/生成逻辑、训练/评估含义的纯文字修正，不属于实验启动流程：直接完成必要的只读检查或最小修改，不生成实验计划、启动卡或状态机。这个豁免只去掉与当前动作无关的实验启动仪式，不豁免代码/规则审核；凡是会改变开跑条件、数据或评估含义、结果认定方式的规则修改，仍按代码修改处理。只有真的要创建实验、改训练/评估含义、冻结运行、启动训练、记录正式结果或晋级版本时，才进入后面的实验步骤。需要计划时只写到能开工为止：简单任务不单列计划，中等任务最多 3 步。

一次新实验默认只走五步：

1. 写清实验问题、基线、唯一代码提交、配置和参数表。
2. 做一次开跑检查：代码工作区干净、数据身份一致、GPU 可见、输出目录不存在。
3. 用现有训练入口直接运行；多张 GPU 只做简单任务分配，不为每个实验新写控制器。
4. 每个 `RUN-xxx` 只保存一个独立目录，至少包含 `training.log`、最终指标和需要保留的最佳模型；禁止覆盖旧目录。
5. 训练后把全部结果回填同一张参数表，并写一份结论说明。

固定保留的科学边界只有：准确 Git commit、配置快照、数据/划分身份、种子、评估口径、完整 U/S/H/ZS 和不覆盖历史结果。其余机制按真实风险选择，不得为了“更正式”自动叠加。

审核使用下面的最小固定规则：

- 普通说明文档、账本值，或已审核代码明确支持的普通超参数/seed 修改，只要不改 schema、解析/生成逻辑、数据/划分、评估语义、工作流门槛，也不打开未审核代码路径，就只做机器检查。其他配置、模板和工作流规则修改按代码修改处理。
- 任何代码修改，包括模型、训练、数据、评估、workflow、helper、模板和训练配置生成逻辑，目标测试通过后必须完成 2 轮对抗式只读审核。
- 两轮必须由两个不同的子 Agent 依次完成，不能由主助手自审代替，也不能让同一个子 Agent 重复充当两轮。
- 第 1 轮主动寻找实现、接口、shape、梯度、数据与评估错误；实现者修复、重跑测试并由第 1 轮 Reviewer 复核通过后，才能启动第 2 轮。
- 第 2 轮必须检查同一份最终代码，并从反方立场寻找反例、隐藏耦合、回归和测试盲区。若第 2 轮导致被审核代码再次修改，原两轮结论失效，仍由这两个 Reviewer 按第 1 轮 → 第 2 轮重新检查，不增加第三个 Reviewer。
- 两轮都绑定同一个 `reviewed_code_id`（准确 commit；尚未提交时使用包含 staged/unstaged tracked diff 的 SHA-256），并绑定相同的 `reviewed_extra_files`（范围内 untracked 或仓库外文件的排序后路径与 SHA-256）；两轮都明确通过、阻断问题为 0 且机器测试通过，代码才算完成并允许进入正式训练。
- 正式 Runner 最终只能使用已冻结的 `commit:<sha>`。若两轮先审核的是 diff，freeze 后由 Coordinator 只读确认提交内容与已审核 diff/额外文件完全一致，并记录 `freeze_equivalence: pass`；不一致就重新审核，不能拿旧结论开跑。

时间上限：纯参数实验从计划到开始训练不超过 10 分钟；涉及代码或评估改动不超过 30 分钟。超过上限时停止增加流程，只汇报并处理唯一真实阻断。正式论文实验也使用这套短流程；论文严谨性来自完整实验设计和结果，不来自更多文件层级。

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
- 论文英文写作优先复用 owner 指定的本地参考论文中已经出现的句型、术语和连接方式；在项目事实一致的前提下改写或组合，不擅自换成参考论文未使用的陌生表达。
- 论文摘要默认贴近指定参考论文的篇幅，只说明核心问题、主要方法和有证据的结论；删除重复解释与次要模块，不为显得完整而扩写。
- 交付流程图、框架图、代码路径图或实验链路图时，默认额外生成一个可本地打开的 HTML 文件，并在回复中用 `file:///D:/.../xxx.html` 的绝对本地链接给 owner。Markdown/Mermaid 可以作为仓库权威记录，但不能替代 owner 可直接打开的 HTML 视图。

## AI 审核规范

- 机器验证永远先跑；两轮审核不能替代测试、schema、边界检查或真实最小样例。
- Implementer 是唯一代码 writer；两个 Reviewer 都只读，不改文件、不启动正式训练。
- 每轮最少记录：`round`、`reviewer_id`、`reviewed_code_id`、`reviewed_extra_files`、`files_reviewed`、`machine_test_ref`、发现、`unresolved_blockers`、`decision` 和 `uncovered_scope`；第 2 轮另写 `previous_round_ref`。
- 正式训练开始前，Coordinator 必须确认两轮来自不同子 Agent、顺序正确、绑定同一份最终代码、`decision: pass` 且 `unresolved_blockers: 0`。缺一项就停止，不拿旧审核结论顶替。
- 默认复用当前任务输出或现有实验质量记录，不创建命名审核线程、完整审核包或额外审核层。旧的 `review-1`、`strict-3`、Claude Code 审核包只用于回查历史，除非 owner 当前明确要求特殊审计。
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
14. 做审核：代码修改在机器验证后依次完成两轮不同子 Agent 的对抗式只读审核；两轮绑定同一份最终代码，全部通过后才允许正式训练。
15. 收尾清理：Runner 仍有 running/pending job 时，当前阶段 active 左侧命名线程必须保持可见；只有 closeout/handoff 完成、输出已入账后，才报告 `keep / archive / unknown agents`，归档 completed threads，记录 `archive_result`，左侧栏只保留当前 active agents。

## 仓库规则

- 开始涉及新旧仓库对照的任务前读取根目录 `REPOSITORY_INDEX.json`。允许读取索引中的新版模板与新版实例文件，但默认不得跨仓库写入、自动同步或迁移账本；跨仓库写入必须由 owner 明确授权。

- `main` 是总管理长期分支。历史 `framework/v1`、`framework/v2`、`framework/v3`、`framework/v5` 与 `vX` Tag 只负责回查正式框架来源；正式新实验必须读取 `TEMPLATE.yaml`，从 `framework/vX-template-vN` 和 `model/vX-template-vN` 锁定的准确母版提交独立分叉。`v4` 是历史 config-only 标签，不创建 `framework/v4`。
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

- 框架与实验唯一正式结构见 `docs/workflow/FRAMEWORK_EXPERIMENT_STANDARD.md`：所有正式框架平级；每个 `FRAMEWORK-VX` 固定拥有 tune、ablation、innovation、confirmation 四类实验；创新通过确认和接纳后才注册为新的同级正式框架并获得 Tag。
- 人看的实验编号使用 `VX-TUNE-xxx`、`VX-ABLATION-xxx`、`VX-INNOVATION-xxx`、`VX-CONFIRM-xxx`；`TRIAL / ATTEMPT / DR` 只作历史或 Runner 内部追踪号。
- 每个实验项必须拥有一张 `PARAMETER_MATRIX.csv/.md`，每个真实训练任务对应一行 `RUN-xxx`；旧记录不能可靠恢复逐任务参数时写 `legacy_summary_only`，不得猜值。
- GTPJ 实验默认使用本机 conda 环境 `dvsr_gpu`；运行训练、特征抽取、验证脚本前先激活该环境，或使用 `conda run -n dvsr_gpu ...`。
- OpenClaw 是优先 runtime；Codex 兼容，但必须遵循同一套文件。
- 每个新创新实验必须从 `idea_tree` 节点开始，并登记到所属正式框架的 `innovation/INDEX.md`。
- 没有 `idea_id`，就不创建正式 `INNOVATION-xxx`。
- 每个创新实验至少记录 implementation、config、quality_check、result 和代码来源。
- tune、ablation、innovation、confirmation 四类实验都写入目标正式框架目录，例如 `experiments/v5/`。
- 旧 `TRIAL / ATTEMPT` 目录只继续保存和追溯历史证据；新的调参、窄消融和确认必须写进所属正式框架对应类型的参数表，并用 `legacy_ref` 回指旧目录。
- 创新通过确认和接纳后注册新的同级正式框架并创建 Tag；未通过时留在所属正式框架的创新实验内，不能提前占用框架编号、长期框架分支或 Tag。
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
- `real_multi_agent` 必须分文件复核：每个只读角色要在自己的输出里写 `files_reviewed`、`decision` 和 `uncovered_scope`，并指向独立 output file。入口规则、hard gate 和 helper 测试必须分别有人看；本机 Skill 只核对入口路径，不再镜像整套规则。
- `role_only_with_independent_sequential_review` 不是第三种 activation mode，只能写在 `agents.tool_support.fallback_mode`；它不能用于 promotion、正式 best 结论或 owner 已明确要求真实多 agents 的任务，除非 owner 明确接受 debug/smoke 降级。
- owner 明确要求多 agents、启动真实 Runner、产出正式 evidence、任务修改模型/forward/loss/eval/数据流语义、涉及接口/评估/label mapping/seen-unseen split/class order/logits shape/metric semantics 风险、结果异常有争议、promotion 前复核、结论会影响论文实验路线或 baseline 选择时，必须使用 `real_multi_agent`。
- 窄范围 rerun / confirmation 准备、训练前候选 triage、只读解释、配置查看、debug/smoke 或不改变结论的账本格式整理时，可以使用 `role_only`，但必须记录代执行的角色和升级条件；debug/smoke 结果不能进入 keep、best、promotion 或 confirmation evidence。
- Runner 永远串行并锁 GPU；Implementer 是同一代码路径唯一 writer；Coordinator 是最终 GitHub 账本唯一写入者；Reader/Planner、Log Analyst、Quality Checker、Result Analyst、Reviewer 默认只读，可并行，但代码审核第 2 轮必须等待第 1 轮问题修复、重测和复核通过后再开始。
- Agent 不能把隐藏聊天记忆当实验事实源。Codex memory 或历史会话摘要只能用于定位，必须回到当前 repo、日志或 artifact 验证后才能写入结果、质量门或 promotion 证据。
- `agent_summary.md` 必须记录 `activation_mode`、`agent_instance_mode`、`agent_instance_type`、`lifecycle`、`persistent_thread_id`（如启用）、`named_thread_reason`、`independence_scope`、`output_locations`、`memory_used`、`memory_sources` 和 `verified_against_current_repo`。
- 如果 owner 对 agent 模式提出异议，先暂停真实 run，修正启动卡或升级为 `real_multi_agent` 后再继续。

## 安全

- 不提交数据集、checkpoint、原始 cache、密钥或大型日志。
- 不使用训练/测试反馈在运行中途改变训练行为。
- 不隐藏失败实验；失败也要作为证据记录。

---

# 归档二：docs/workflow/START_HERE.md

# GTPJ 工作流入口

这是每个 GTPJ 任务的精简入口，用来取代“每次都读完整 workflow 目录”的旧习惯。

## 当前唯一默认入口：五步短流程

自 2026-08-08 起，实验执行采用 `SYS-WORKFLOW-V6`。下文仍出现的多 agents、`agent_runtime.yaml`、三轮审核、Git bundle、多层收据、永久 claim、专用控制器和二次冻结，都是历史兼容能力，不再是普通实验或论文实验的默认必经步骤。

```text
实验问题与基线
-> 唯一 experiment commit + 配置 + PARAMETER_MATRIX
-> 一次开跑检查（clean/data/GPU/输出不覆盖）
-> 直接训练
-> training.log + 指标 + 最佳模型 + 参数表回填
```

默认执行规则：

- 只有 1 个运行前 Git 提交；不再额外制造 candidate commit 和 final freeze commit。训练结果另做结果提交。
- 服务器能 `git fetch` 到准确提交时不用 Git bundle；只有服务器无法访问仓库时才临时使用 bundle。
- 不为单个实验写专用控制器。复用训练入口和最小启动脚本即可。
- 两张 GPU 只做简单分配；只有真实并发冲突时才使用一把 GPU 锁，不固定三波调度。
- 不做启动收据、结束收据、永久 claim 的多层套娃。一个不可覆盖的 `RUN-xxx` 目录和一份运行记录即可。
- 只固定代码、配置、数据/划分、种子、评估口径和完整结果；制品哈希只用于需要长期保留的最终模型或关键日志，不逐文件堆哈希。
- 普通说明文档、账本值，或已审核代码明确支持的普通超参数/seed 修改，只要不改 schema、解析/生成逻辑、数据/划分、评估语义、工作流门槛，也不打开未审核代码路径，就只做机器检查。其他修改按代码修改处理：机器测试后，由两个不同的只读子 Agent 依次完成 2 轮对抗式审核；两轮绑定同一个最终代码身份并全部通过后才允许正式训练。

准备耗时上限：参数实验 10 分钟；代码或评估实验 30 分钟。超过上限时不得继续新增门槛，只处理唯一真实阻断并向 owner 说明。

下面旧章节只用于解释历史文件和旧 helper，不得覆盖本节。

## 先认清实验放在哪里

正式结构以 `docs/workflow/FRAMEWORK_EXPERIMENT_STANDARD.md` 为准：

- 先确定 `FRAMEWORK-VX`，再进入它的 tune、ablation、innovation、confirmation 四类同级实验。
- `framework.yaml` 说明“这个框架是什么”；`TEMPLATE.yaml` 登记不可修改的代码母版 `MODEL-VX-TEMPLATE-VN`；`EXPERIMENT.yaml` 记录某项实验实际复制了哪份母版代码。
- 人看编号是 `VX-TUNE-xxx / VX-ABLATION-xxx / VX-INNOVATION-xxx / VX-CONFIRM-xxx`。
- 每个实验只有一张参数矩阵；一行 `RUN-xxx` 对应一个真实任务。
- `TRIAL / ATTEMPT / DR` 只作旧记录和 Runner 内部映射。
- 创新确认并接纳后才注册新的同级正式框架并获得 Tag；纯调参、消融、确认和未晋级候选不会生成正式框架。

## 0. Owner 简单入口

owner 不需要背 `workflow_mode`、`agent_runtime.yaml` 或线程字段。下面三句就是正式入口：

| owner 口令 | Coordinator 必须解释成 | 允许动作 |
|---|---|---|
| `本地正式，干净` | `workflow_mode=live_multi_agent_monitor` | 先确认侧边栏干净；允许创建本轮左侧命名 Codex 线程；不启动服务器 runner。 |
| `开启多agents智能体工作流，开始` / `开启多agents智能体工作流，跑N轮` / `开启多agents智能体工作流，做N轮实验` | `workflow_mode=live_multi_agent_monitor` | owner 已明确选择动态多 agents 工作流；不得反复确认 workflow 模式或启动意图；通过硬门后继续创建角色、生成计划并启动对应 runner。 |
| `服务器冻结，开始` | `workflow_mode=server_frozen_runner` | 不创建命名线程；走本地规划、gate、冻结计划和服务器 detached runner。 |
| `只做本地规划` | `activation_mode=role_only` | 只做状态检查、账本整理、计划和 debug/smoke；不进入正式证据。 |

硬规则：只有 `本地正式，干净` 这句同时表达“侧边栏干净”和“允许创建本轮命名线程”。如果 owner 只说“本地正式”但没有说“干净”，Coordinator 只问一句：`侧边栏干净吗？回复：干净。`

明确入口硬规则：owner 已经说出 `开启多agents智能体工作流`、`多agents智能体工作流，开始`、`跑N轮` 或 `做N轮实验` 时，Coordinator 必须把它当作执行授权，而不是只做规划。只有四类情况允许再问一次：运行模式仍然不明、侧边栏干净状态从未确认且工具无法验证、硬门失败、或动作涉及 push / 删除 / 覆盖数据 / 密钥等安全边界。除此之外，不得反复确认规范、不得把“开始/跑N轮”降级成 `pre_run_planned` 后停止。

代码审核硬规则：代码审核不被 `server_frozen_runner` 豁免。凡是修改代码、workflow、helper、模板或训练配置生成逻辑，都要先跑机器验证，再由两个不同的只读子 Agent 按第 1 轮 → 修复与重测 → 第 2 轮的顺序做对抗式审核。两轮必须检查同一份最终代码；正式 Runner 只能使用 freeze 后与已审核内容完全一致的 commit，缺任一轮通过结论或 `freeze_equivalence: pass` 时都不能开跑。

通用话规划入口：

| owner 说 | Coordinator 必须解释成 | 允许动作 |
|---|---|---|
| `规划下一轮实验` / `下一轮怎么跑` | `experiment_planning` | 只读自动生成 Evidence Summary、Candidate Decision、Current Run Plan；不启动 Runner。 |
| `批量规划50轮实验` / `给我规划50轮` | `experiment_planning` with budget 50 | 只读规划批量候选、预算、阻塞和 ledger_target；不创建 batch。 |
| `规划10创新+100调参` / `跑10创新+100调参` | `mixed_experiment_campaign` planning | 拆成 workstreams；先过 planning gate，再进入 campaign gate。 |
| `按这个计划开多agents工作流` | `live_multi_agent_monitor` | 需要真实左侧命名线程、`agent_runtime.yaml` 和 preflight；通过后才能启动正式 Runner。 |
| `按这个计划服务器冻结跑` | `server_frozen_runner` | 训练运行期不创建命名线程；若计划涉及代码/helper/template 改动，先完成代码审核门；通过 server-detached gate 后才能启动 detached Runner。 |

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
agent_instance_mode: named_owner_thread
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

```text
哪个智能体在做什么
当前 run/batch 状态
证据写到哪里
下一步动作
如果主对话暂停，去哪里接着看
```

正式 Runner 启动还必须通过：

```text
docs/workflow/core/AGENT_RUNTIME_HARD_GATE.md
agent_runtime.yaml
python workflow/gtpj_workflow.py validate-agent-runtime --path <agent_runtime.yaml>
```

创建命名线程 前必须先确认左侧栏干净。若 owner 报告左侧栏已有历史 agents，
或者当前工具只能关闭本轮已知 id、不能枚举 UI 中全部旧 agent，则不能继续开新的
`real_multi_agent`。正确动作是先 cleanup；无法 cleanup 的旧 UI agent 必须记为
`unknown_ui_agent`，正式 Runner 阻断。只有 owner 明确接受非正式排障时，才可走
`debug_smoke`，且结果不能进入 keep / best / confirmation / promotion。

没有左侧命名 Codex 线程、没有真实 agent id、没有 pre-run allow/check，就不能启动正式 Runner。
这种情况必须阻断正式工作；只有 owner 明确接受非正式排障时，才可以另开 `debug_smoke`
路径，且结果不能进入 keep / best / confirmation / promotion / version 判断。

统一调度入口必须显式区分两种运行等级，不能默认猜：

```text
debug_smoke：测试代码、服务器、GPU 和 helper 链路；activation_mode=role_only；formal_evidence=false。
formal：正式证据实验；允许 `activation_mode=real_multi_agent`，或 `activation_mode=role_only + formal_runtime_backend=server_detached_role_only`；两者都必须先通过 agent_runtime gate。
```

旧 `run-workflow` 是专门给 Trial/Attempt 动态路由批次写的，不能把一个合法实验目录当通行证后继续跑另一套旧代码。
在 `SYS-WORKFLOW-V5` 下，它只保留 `debug_smoke` 链路探针；正式实验使用本实验自己的参数表：

```bash
python workflow/gtpj_workflow.py run-workflow ... --workflow-mode live_multi_agent_monitor --debug-smoke
python workflow/gtpj_workflow.py freeze-parameter-matrix --path <experiments/vX/type/ID_slug/PARAMETER_MATRIX.csv> --config <同目录配置> --job-id RUN-001
python workflow/gtpj_workflow.py prepare-run-start-receipt --path <同一参数表> --config <同一配置> --job-id RUN-001 ...
```

这两个正式入口都会先校验 `EXPERIMENT.yaml` 的母版绑定；旧 `module_trials/.../ATTEMPT-xxx` 只能回查，不能新冻结或新启动。
即使给旧入口传入 `run-workflow --formal --experiment-dir ...`，V5 helper 也会明确拒绝，因为
`--experiment-dir` 不能证明旧动态路由器实际采用的 Trial、版本和代码 Tag 与它相同。

正式实验必须显式选择 `workflow_mode`，不能由 Coordinator 默认猜测：

| `workflow_mode` | 中文含义 | 适用场景 | gate 要求 |
|---|---|---|---|
| `live_multi_agent_monitor` | 动态多 agents 监控工作流 | owner 要求边跑边监控、质量检查、结果解释、best/promotion 判断，且接受命名 Codex 线程参与 | `activation_mode=real_multi_agent`，`agent_instance_mode=named_owner_thread` |
| `server_frozen_runner` | 本地规划 + 服务器冻结训练工作流 | owner 要求本地只做规划/gate/账本/frozen plan，训练在 `lab4090` detached 跑，本地可以关机 | `activation_mode=role_only`，`formal_runtime_backend=server_detached_role_only`，`thread_creation_allowed=false` |

owner 只说“用工作流”但没有指定模式时，Coordinator 必须先确认：

```text
这次用 workflow_mode=live_multi_agent_monitor，还是 workflow_mode=server_frozen_runner？
```

如果 owner 已经明确说“多agents智能体工作流”，它不属于“只说用工作流”的模糊入口，直接解释为 `live_multi_agent_monitor`。

历史 `server_frozen_runner` 曾使用动态路由 batch planner、文件传输和后台进程；这套 Trial/Attempt 正式入口在
`SYS-WORKFLOW-V5` 下已停用，不能冒充新的 `live_multi_agent_monitor`，也不能把后者降级成服务器离线训练。

没有 `--formal` 和通过的 `agent_runtime.yaml`，即使服务器真的跑了训练，也只能算 runner/debug 事实，不能算正式工作流证据。

## 1.1 文档语言边界

项目文档、workflow 文档、模板说明和审核报告的正文必须使用中文，不允许整段英文说明。

英文只保留为必要名词或机器标识，例如论文标题、方法名、角色名、命令、字段名、文件名、代码标识、指标名、URL 和 helper 依赖的结构 marker。

如果必须保留 `Framework Diagram`、`Trial Flow`、`Code Flow Diagram` 这类英文结构 marker，同一节必须用中文说明它是什么、为什么需要、应该填写什么。新模板不得只给英文标题和英文正文。

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

不要默认深读所有旧协议。

如果只是确认文档层级，不要人工扫完整目录，使用：

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
| `消融` | 消融 Ablation；只允许关闭/旁路/替换既有因素，不新增方法模块 | `playbooks/ablation.md` |
| `复现`, `确认这个结果` | 复现确认 Confirmation | `playbooks/confirmation.md` |
| `开新模块`, `试这个想法` | 创新 / module trial | `playbooks/innovation.md` |
| `升版本` | 升版 Promotion | `playbooks/promotion.md` |
| `跑10创新+100调参` 或任意数量组合 | 混合实验 campaign | `playbooks/mixed_campaign.md` |
| `全自动研究campaign`, `从论文到最终结果都接管` | 全自动研究 campaign | `playbooks/autonomous_campaign.md` |

helper 会自动解析 `跑2创新+8调参` 这类组合短语：

```bash
python workflow/gtpj_workflow.py start --phrase "跑2创新+8调参"
```

## 4. 启动摘要

在改文件、跑实验、记录结果或选择 best 前，先汇报：

```text
能不能开工：
任务类型：
基于版本/分支：
baseline_repro_status：
comparison_reference：
是否进入 idea_tree：
GitHub 写入：
Research/Warehouse 写入：
agents 模式：
runner_scope：
formal_runner_allowed：
formal_evidence_allowed：
必须读的 playbook：
硬门：
agent_runtime_gate：
multi_agent_preflight：
owner_monitor_mode：
agent_activity_stream：
当前阻塞：
下一步最小动作：
```

如果只是状态汇报，保持简短即可。

## 5. 最小闭环

不要把简单任务做成大工程。正式实验只要求这条闭环：

```text
人话路由 -> campaign/attempt 计划 -> agent_runtime -> preflight -> runner
-> manifest/result/quality/agent_summary -> cleanup -> sync/closeout
```

中间的证据成熟度由状态机管理：

```text
subject_id + subject_type -> TRANSITIONS.jsonl -> evidence_state -> evidence_routing.yaml
```

`TRANSITIONS.jsonl` 是只追加的权威历史；`evidence_routing.yaml` 只是当前状态视图，必须能由
chain head 推导出来。聊天结论、服务器状态和 `agent_summary.md` 都不能手写覆盖状态机。

从论文获得创新时，多一段前置闭环，但仍然只接入同一个实验闭环：

```text
paper_inbox -> source_review -> idea_candidate -> formal_IDEA -> selected_queue
-> trial_preflight -> runner_evidence -> idea_feedback
```

进入 `trial_preflight` 前必须由 owner 明确指定 `base_version` / `base_code_tag`，例如
`基于 v5 从论文开始做实验`。不能默认使用当前 active version。

混合实验目录只做调度索引；正式结果必须写回所属框架的 tune / ablation / innovation / confirmation 账本。旧 attempt / trial 只保留兼容证据。

框架记录只跟“方法框架变动”绑定，不跟每个代码文件绑定：

```text
调参 / 复现 / 只关闭既有组件的窄消融 -> 不新增 framework_diagram，只记录结果证据。
新增或改写 module / forward / loss / eval / data view / 接口语义 -> 创新 / module trial，必须记录框架和模块来源。
```

## 6. 证据优先

不要让聊天记忆变成正式证据。

正式证据只来自：

```text
manifest.yaml
result.yaml
result.md
quality_check.md
agent_summary.md
ATTEMPTS.md
batch_status.json
Warehouse logs/checkpoints/receipts
必要时的 Research source notes
```

如果某个结论会影响 keep/drop/best/repeat/promotion/versioning 或下一轮高成本实验，就必须能追溯到文件或 artifact。

debug/smoke 结果必须显式锁定为：

```yaml
evidence_level: debug_smoke
formal_evidence: false
eligible_for_keep_best_promotion_confirmation: false
```

## 6.0 参数矩阵入口（2026-08-04 起）

从今天起，任何新实验都不能只写“这一批跑了 50/100 个”。必须为每个具体任务建立 `PARAMETER_MATRIX.csv` 和阅读版 `PARAMETER_MATRIX.md`：一行对应一套参数、一个种子和一次结果。先生成参数矩阵、查重、提交 pre-run freeze commit，再用 `prepare-run-start-receipt` 一次完成“生成启动收据 + helper 直接拉起训练 + 收集进程输出”，不能在收据生成后另开一条手工训练命令；训练结束后由 helper 记录退出码和整份日志哈希，结束标记后不得再补写指标。训练完成后把每个任务的结果回填原表。所有改表动作共用同一把锁。版本级的 `record-result` 和模块内的 `record-module-attempt` 会拒绝草稿、过期阅读版、缺少启动收据、缺少真实进程标记、日志未封口或找不到对应行的表。正式动态批次还要求矩阵中的 `run_id` 与计划完全相同。详见 `docs/workflow/protocols/parameter_matrix_protocol.md`。

## 6.1 正式待跑实验入口

Owner 问“现在有哪些待跑实验”时，只读正式 ledger，不从 `.gtpj_runtime/` 反推。正式待跑实验必须能在对应类型的正式表格里看到：

| 实验类型 | 正式待跑表格 | 说明 |
|---|---|---|
| 版本级 tune | `experiments/vX/tune/INDEX.md` | 只记录正式 baseline 的调参计划和结果。 |
| 版本级 ablation | `experiments/vX/ablation/INDEX.md` | 只记录正式 baseline 的消融计划和结果。 |
| 版本级 confirmation | `experiments/vX/confirmation/INDEX.md` | 只记录正式 baseline 或版本级 candidate 的确认计划和结果。 |
| 历史 module trial / attempt | `experiments/module_trials/...` | 只读兼容和证据回查；新实验不得在此登记，必须回到所属框架四类账本。 |
| mixed campaign | `experiments/campaigns/.../WORK_ITEMS.md` / `RESULT_INDEX.md` | 只做 derived index；每个 work item 仍要回指上面某个正式表格。 |

待跑实验的判定规则：

```text
formal_pending = 正式表格中有 subject 行
              + subject 有明确实验类型、run_id 或计划目录
              + 状态为 planned / pending / pre_run / pre_run_gated / ready_to_run
              + 不是 debug_smoke，或已明确标注 formal_evidence: true
```

`.gtpj_runtime/batches/<run_id>` 只是 runner 执行缓存；它可以证明运行包存在、事件是否发生、summary 是否产出，但不能单独决定“待跑实验”。如果 runtime 目录存在而正式表格没有对应行，统一标为 `orphan_runtime_plan`，只能作为历史参考或排障线索，不能自动续跑、不能进入 keep / best / confirmation / promotion。

## 7. 两轮对抗式代码审核

代码修改不需要 owner 参加日常审核，也不再按 `fast`、`review-1`、`strict-3` 分档。固定流程只有两轮：

```text
机器验证
-> 子 Agent A 第 1 轮：找实现、接口、shape、梯度、数据与评估错误
-> 实现者修复、重测，A 复核通过
-> 不同的子 Agent B 第 2 轮：找反例、隐藏耦合、回归和测试盲区
-> 两轮绑定同一 reviewed_code_id，均 pass，unresolved_blockers: 0
```

若第 2 轮促成被审核代码修改，原结论失效，仍用 A、B 按顺序重新检查最终代码。其他只读工作可以并行，唯独第 2 轮不能抢在第 1 轮收口前开始。详细字段见 `docs/workflow/protocols/ai_cross_review_protocol.md`；旧审核包和 `validate-ai-cross-review` 只用于历史回查，不是新代码的当前入口。

## 8. 命名线程

正式 `real_multi_agent` 不能使用随机英文昵称。左侧栏命名 Codex 线程必须按任务命名：

```text
<subject_id> | <Role Label>
```

示例：

```text
ATTEMPT-007 | Runner Monitor
ATTEMPT-007 | Interface Checker
ATTEMPT-007 | Evidence Quality Checker
```

命名必须写入 `agent_runtime.yaml` 的 `named_thread_titles`，并由
`validate-agent-runtime` 校验。随机昵称或只写 `Runner` / `Quality` 这种泛名，不能启动正式 Runner。

创建线程前还必须满足：

```text
left_sidebar_named_threads_ready: true
owner_visible_sidebar_count: 0 或只包含本阶段 active threads
unknown_ui_agents: none
```

## 9. Live Monitor 逐实验汇报

`live_multi_agent_monitor` 不是“启动服务器后结束”。在 Runner 仍处于 running/pending 时，本轮左侧命名 Codex 线程必须保持可见，尤其是 Runner Monitor、Log Analyst、Result Analyst、Quality Checker 和 Interface Checker；只有 closeout/handoff 完成、输出写回账本后，才归档这些线程。

监控每个新增 completed job 时使用统一入口：

```powershell
python workflow\gtpj_workflow.py monitor-workflow --run-dir <run_dir> --report-new-completions --activity-log <attempt_dir>\AGENT_ACTIVITY.md
```

每次报告至少写清 `job_id`、H/U/S/ZS、当前 best、是否出现 H>=75/H>=76、证据位置和下一步。`monitor_seen_completed_jobs.json` 只用于去重，不是正式结果源。

如果 owner 看到的左侧栏数量与 `agent-cleanup-plan` 不一致，以 owner 可见 UI 为准；
Coordinator 不得再开新的命名线程来“补 gate”。

---

# 归档三：docs/workflow/WORKFLOW_KERNEL.md

# GTPJ 工作流内核

本文件是精简后的硬规则层，应该保持短而稳定。

## 当前执行内核：SYS-WORKFLOW-V6

正式实验和论文实验统一使用下面这条最短闭环：

```text
唯一实验提交 + 配置/参数表 + 一次开跑检查
-> 直接训练到独立 RUN 目录
-> 回填全部指标和结论
```

必须保留：准确 commit、clean checkout、配置快照、数据/划分身份、seed、评估口径、逐 RUN 的 U/S/H/ZS、日志和不覆盖历史结果。

默认不要求：专用控制器、双层 GPU 锁、固定波次调度、Git bundle、永久 claim、多层收据、逐文件制品哈希、三路审核、命名线程、`agent_runtime.yaml`、状态迁移链或第二个 final freeze commit。它们只有在当前实验确实出现对应风险时才允许按需使用，并要说明解决了什么真实问题。

审核规则：机器测试优先。普通说明文档、账本值，或已审核代码明确支持的普通超参数/seed 修改，只要不改 schema、解析/生成逻辑、数据/划分、评估语义、工作流门槛，也不打开未审核代码路径，就默认 0 次独立审核；其他配置、模板和工作流规则修改按代码修改处理。任何代码修改，包括模型、训练、数据、评估、workflow、helper、模板和训练配置生成逻辑，都固定执行下面 2 轮对抗式只读审核：

1. 第 1 轮由子 Agent A 检查需求对应、实现正确性、接口、shape、梯度、数据与评估边界，并主动尝试证明代码有错。实现者修复并重跑机器测试后，由 A 复核到通过。
2. 第 2 轮由不同的子 Agent B 检查与第 1 轮相同的最终代码，重点寻找反例、隐藏耦合、回归、测试盲区和结论污染。

同一个子 Agent 不能计算为两轮，主助手自审不能替代子 Agent。其他只读角色可以并行，但第 2 轮必须等待第 1 轮问题修复、重测和 A 复核通过后再启动。若第 2 轮导致被审核代码改变，两轮都要针对最终代码重新执行；仍使用 A、B，不增加第三个 Reviewer。

两轮必须绑定同一个 `reviewed_code_id`：有冻结提交时写准确 commit；尚未提交时写包含 staged/unstaged tracked diff 的 SHA-256，并用 `reviewed_extra_files` 记录范围内 untracked 或仓库外文件的排序后路径与 SHA-256。每轮至少记录 `round`、`reviewer_id`、`reviewed_code_id`、`reviewed_extra_files`、`files_reviewed`、`machine_test_ref`、发现、`unresolved_blockers`、`decision` 和 `uncovered_scope`；第 2 轮另写 `previous_round_ref`。两轮都为 `decision: pass`、`unresolved_blockers: 0` 后，代码才允许正式训练。记录复用当前任务输出或现有实验质量记录，默认不新建审核包。

正式 Runner 最终只能绑定已冻结的 `commit:<sha>`。若两轮先审核 diff，freeze 后由 Coordinator 只读确认该 commit 的审核范围内容与已审核 diff、`reviewed_extra_files` 完全一致，并记录 `frozen_run_commit` 和 `freeze_equivalence: pass`；staging/commit 漏文件、夹带代码或内容变化都会使旧审核失效。影响运行的额外文件必须进入 commit 或已有的数据/配置冻结身份，否则阻断。

时间规则：参数实验准备不超过 10 分钟；代码或评估实验准备不超过 30 分钟。达到上限仍不能训练时，停止扩建流程，报告唯一阻断和最小修复。

旧的 V5 多 agents、receipt、`review-1`、`strict-3` 和 Claude Code 审核包只用于历史回查，不再作为新代码入口。

## 0. 框架与实验对象

- 唯一结构规范：`docs/workflow/FRAMEWORK_EXPERIMENT_STANDARD.md`。
- `main` 管治理；每个正式框架用 `TEMPLATE.yaml` 登记只读母版 `MODEL-VX-TEMPLATE-VN`，每项实验用 `EXPERIMENT.yaml` 登记准确起点。
- 四类实验都从准确母版提交独立分叉，分支名为 `exp/vX/<type>/...`；实验代码不得并回母版，也不得从另一项实验继续叠加。
- `legacy_frozen 不能启动新实验`：它只解释旧结果；必须先完成新的干净母版并冻结为 `frozen`。
- 每个正式框架固定有 tune、ablation、innovation、confirmation 四类实验。
- `experiments/vX/EXPERIMENTS.md` 由四个 INDEX 生成，禁止手工维护第二份结果。
- 每个实验的 `PARAMETER_MATRIX.csv` 是逐运行事实源；旧 `ATTEMPT` 只能成为 `legacy_ref`。

## 1. 权威来源

- GitHub 是可复现控制面、治理账本和轻量结果索引。
- `GTPJ_Research` 保存长推理、论文/来源笔记和完整 idea 历史。
- `GTPJ_Warehouse` 保存 raw logs、checkpoints、生成图、运行 receipt 和大型 artifact。
- 聊天上下文、命名线程 上下文、persistent thread 上下文和 Codex memory 只能辅助定位，不能作为正式证据。

## 1.1 文档语言硬规则

- 项目文档、workflow 文档、模板说明和审核报告的正文必须使用中文。
- 不允许新增或改出整段英文说明；英文只能作为必要名词或机器标识保留。
- 允许保留的英文包括：论文标题、方法名、角色名、命令、字段名、文件名、代码标识、指标名、URL，以及 helper 当前依赖的结构 marker。
- 如果标题保留英文 marker，例如 `Framework Diagram`、`Trial Flow`、`Code Flow Diagram`，同一节必须用中文解释含义、用途、填写要求和阻断条件。
- 新增模板必须先通过文档语言检查；历史 archive 可以保持原样，但不能作为新文档的写法模板。

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
状态机记录和服务器 runner 都不能替代真实左侧命名 Codex 线程；没有 `agent_runtime.yaml`
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

统一调度入口必须强制选择运行等级：

```yaml
debug_smoke:
  activation_mode: role_only
  formal_evidence: false
  real_agent_instances_started_by_helper: false

formal:
  activation_mode: real_multi_agent
  formal_evidence: true
  agent_runtime_gate_satisfied: true
```

`run-workflow` 还必须显式选择 `workflow_mode`，禁止 Coordinator 猜测：
```yaml
workflow_mode:
  required: true
  allowed:
    - live_multi_agent_monitor
    - server_frozen_runner
  no_default_guess: true
```

`SYS-WORKFLOW-V5` 启用后，旧动态路由 `run-workflow --formal` 已停用，因为它的实际运行对象仍是
Trial/Attempt，不能与新的四类实验目录可靠绑定。正式训练改由标准实验目录内的
`freeze-parameter-matrix` 和 `prepare-run-start-receipt` 逐行启动；两者都会读取 `EXPERIMENT.yaml`，
确认冻结母版绑定。`run-workflow --debug-smoke` 仍可用于不进入正式证据的链路探针。
旧的 `run-workflow --formal --experiment-dir ...` 即使提供了合法目录也会被拒绝，不能把它当作另一套 Trial 代码的通行证。

Owner 简单口令优先按下列映射解释：
```text
本地正式，干净 -> live_multi_agent_monitor；侧边栏干净；授权创建本轮左侧命名 Codex 线程；禁止启动服务器 runner
开启多agents智能体工作流，开始 / 跑N轮 / 做N轮实验 -> live_multi_agent_monitor；不得反复确认 workflow 模式或启动意图；通过硬门后继续执行
服务器冻结，开始 -> server_frozen_runner；不创建命名线程；允许服务器 detached runner
只做本地规划 -> role_only；不进入正式证据
```

如果 owner 只说 `本地正式` 但没有说 `干净`，Coordinator 只问一次侧边栏是否干净；不能展开成长授权模板。

- `live_multi_agent_monitor` 表示动态多 agents 监控工作流。它必须使用 `activation_mode: real_multi_agent`、`agent_instance_mode: named_owner_thread`，并通过左侧命名 Codex 线程 gate。
- `server_frozen_runner` 表示本地规划、冻结计划、服务器 detached 训练工作流。它必须使用 `activation_mode: role_only`、`formal_runtime_backend: server_detached_role_only`、`thread_creation_allowed: false`，不能自动创建线程。
- 如果 owner 只说“用工作流”但没有说明是哪一种，必须先问清楚；不能把服务器冻结训练当成动态多 agents 工作流，也不能把动态多 agents 工作流偷偷降级成离线训练。
- 如果 owner 已经说“开启多agents智能体工作流”“多agents智能体工作流，开始”“跑N轮”或“做N轮实验”，它不是模糊的“用工作流”。Coordinator 必须按 `live_multi_agent_monitor` 执行，不得反复确认规范，不得只写 planning gate 后停止。只有运行模式仍冲突、侧边栏干净状态未确认且无法验证、硬门失败、或 push / 删除 / 覆盖数据 / 密钥等安全边界动作，才允许再问一次。

代码审核不被 `server_frozen_runner` 豁免。代码、workflow、helper、模板或训练配置生成逻辑改动必须完成两轮不同子 Agent 的对抗式只读审核，两轮绑定同一个最终 `reviewed_code_id` 并通过后，才能进入 `pre-run freeze commit` 或正式 Runner。

没有显式 `--debug-smoke` 或 `--formal` 时必须阻断。选择 `--formal` 时必须提供并通过
`agent_runtime.yaml`；选择 `--debug-smoke` 时结果只能证明工程链路可运行，不能回填为正式证据。

## 2.1 正式待跑 ledger 硬规则

正式待跑实验由正式 ledger 决定，不由运行缓存决定。任何“待跑”结论必须先读对应类型的表格：

```text
framework tune            -> experiments/vX/tune/INDEX.md
framework ablation        -> experiments/vX/ablation/INDEX.md
framework innovation      -> experiments/vX/innovation/INDEX.md
framework confirmation    -> experiments/vX/confirmation/INDEX.md
legacy Trial/Attempt      -> compatibility evidence only; map back with legacy_ref
mixed campaign            -> experiments/campaigns/.../WORK_ITEMS.md / RESULT_INDEX.md，只作 derived index
```

正式表格中的一行只有同时满足下面条件，才算 `formal_pending`：

```text
有 subject_id 或实验 id
有实验类型
有 run_id、计划目录或 attempt 目录；正式批次中的 run_id 必须与参数表逐行一致
状态是 planned / pending / pre_run / pre_run_gated / ready_to_run
不属于 debug_smoke，或明确 formal_evidence: true
```

`.gtpj_runtime/` 只保存运行中状态和 runner 执行包。目录存在、`batch_status.status=planned`
或旧 `events.jsonl` 为空，不能单独构成待跑实验。若 runtime 目录没有正式 ledger 行，统一记为
`orphan_runtime_plan`；它可以用于历史参考或排障，但不得自动续跑、不得写入 keep / best /
confirmation / promotion。

## 2.1.1 参数矩阵硬规则（2026-08-04 起）

一轮 batch 只是很多具体任务的容器，不能替代参数表。任何新建正式实验必须把每个 job 写进 `PARAMETER_MATRIX.csv`，并提供自动生成的 `PARAMETER_MATRIX.md` 阅读版。相同配置指纹必须明确标注为 `repeat_of`，否则视为误重复；参数矩阵必须与 pre-run freeze commit 一起冻结，再用 `prepare-run-start-receipt` 由 helper 生成收据并直接拉起训练。helper 会把真实进程号、开始、退出和输出追加到收据哈希之后，结束时记录退出码和整份日志哈希，不能只生成收据再手工开跑，也不能在结束标记后补写指标。跑完后只允许回填状态和结果，所有参数表改写动作共用同一把锁。阅读版与 CSV 不一致、启动收据缺失、真实进程标记缺失、日志未封口或收据与日志不匹配时，`record-result` 和 `record-module-attempt` 都会拒绝正式入账。动态路由正式批次还会逐行核对矩阵 `run_id` 与冻结计划，并要求取回真实 Warehouse manifest 和逐任务启动收据后再同步。完整规范：`docs/workflow/protocols/parameter_matrix_protocol.md`。

## 2.2 实验规划门（Experiment Planning Gate）

正式 batch、Runner、server frozen run 或 promotion-prep run 生成前，必须先通过 `experiment_planning`。
这个阶段必须自动读取当前项目状态，而不是让 owner 手填计划。

最小自动扫描：

```text
repo branch / HEAD / dirty
current_version 和 baseline_repro_status
正式待跑 ledger：只认 experiments/vX/{tune,ablation,innovation,confirmation}/INDEX.md；旧 TRIAL-xxx/ATTEMPTS.md 与 campaign 只作兼容映射
已完成 result / quality / agent_summary
.gtpj_runtime 只作 debug context，不作规划权威
```

输出只保留三张表：

```text
Evidence Summary：证据从哪里来，能支持什么，不能支持什么。
Candidate Decision：哪些候选值得跑，阻塞是什么，允许声称什么。
Current Run Plan：本轮 work item、fingerprint_policy、预算、停止条件和 ledger_target。
```

每个 planned job 必须引用正式 `evidence_ref`，声明 `claim_scope`、`fingerprint_policy`、`budget`、
`stop_condition` 和 `ledger_target`。没有 planning gate，不得生成 batch、启动 Runner 或写入
formal evidence。只读 helper 入口：

```bash
python workflow/gtpj_workflow.py plan-experiments --phrase "<owner 口令>"
```

单项和批量规划使用同一个入口。显式组合口令如 `跑10创新+100调参` 会拆成多个 workstream；
只给总量如 `做50轮实验` 时，planning gate 只能根据当前证据给出候选分配、阻塞和预算建议，
不得在缺少实验类型和 evidence_ref 时直接生成 Runner batch。

## 3. Agent 规则

正式任务默认：

```yaml
activation_mode: real_multi_agent
agent_instance_mode: named_owner_thread
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
- 正式运行必须记录真实 `agent_instance_id` 或可见 thread id；`named_owner_thread` 这类占位词不能冒充实例。
- 需要长期保留的经验必须写回 `agent_summary.md`、角色 `memory.md`、workflow issues、result 文件或 campaign 账本。
- `persistent_thread` 只是跨 workflow 可见追踪的可选上下文，不是 evidence。
- 不要给每个实验 run 创建一个永久 agent/thread。
- 每轮 workflow 结束或阶段结束时，Coordinator 必须先确认已完成 agents 的结论写入
  `agent_summary.md` / `AGENT_ACTIVITY.md` / result / quality / issues / memory 等正式位置，
  然后关闭这些已完成 agents。左侧栏默认只保留当前阶段仍在工作的 active agents。
- 多 agents 必须分文件复核：每个只读角色都要记录 `files_reviewed`、独立输出文件、allow/block/propose 结论和未覆盖范围。Coordinator 不能用一个上下文一次性“看过所有文件”来冒充独立复核；规则改动要同时核对 GitHub 现行文档、helper 测试和本机 Skill 入口。
- 左侧栏命名线程 显示名必须严格按 `<subject_id> | <Role Label>` 命名，例如 `ATTEMPT-007 | Runner Monitor`、`ATTEMPT-007 | Interface Checker`、`ATTEMPT-007 | Evidence Quality Checker`。
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
- `exact_repeat` 必须固定 `original_seed`、原始 config、代码 commit、data/cache、epoch schedule、batch size 和评估口径；改变 seed 或任何参数的多次运行只能叫 `seed_sweep` /
  `score_search` / `multi_seed_stability`，必须写 `not_confirmation_evidence: true`，不能叫严格复现。
- confirmation 默认 `repeat_type: exact_repeat`、`max_attempts: 5`、`max_attempts_hard_cap: true`、`early_stop_on_best_hit: true`。必须声明
  `restore_target_H`；`near_miss_tolerance_H` 只用于标记接近但未还原。复现判定分三层：
  `best_hit` 只看任一 clean repeat 是否达到 `restore_target_H`，用来回答“有没有还原”；`near_miss_not_restored`
  表示接近目标、有希望，但不能停止、不能作为 confirmation；`stable_confirm`
  看同一 `original_seed`、同一配置的 mean/min/max/range 是否满足预设门槛，用来回答“能不能作为稳定 confirmed / promotion / baseline 证据”。
- `max_attempts_hard_cap` 表示同一候选无论是否还原成功最多跑 5 次；达到 `restore_target_H` 可以提前停止，5 次未达到则收口为 not restored / near miss，不能继续追加复现轮数。
- 复现通过 `best_hit` 后，必须记录 `best_single_H` / `best_observed_H`；如果 `stable_confirm` 未通过，
  结论只能是命中候选或继续复现，不能写成稳定确认。
- promotion 和 baseline claim 默认比较 `confirmed_H` / repeat mean，不能只凭 best repeat。
- 不能把未确认的 `best_observed_H` 说成 confirmed baseline。
- 每个正式版本 `experiments/vX/` 必须有版本级 `framework_diagram.md` 和 `MODULES.md`；`VERSION.md` 必须链接它们并包含 `## Framework Diagram`。模块说明不能只列名字，必须解释 purpose、input、output、config switch 和 baseline-off behavior。
- 框架记录绑定“方法框架”，不是绑定每个代码文件。调参、复现、只关闭或旁路既有组件的窄消融不新增框架图；它们只记录 config、manifest、result、quality 和 agent summary。
- 凡是新增或改写 module、forward、loss、evaluation、data view、input/output、tensor flow、接口语义或模块分支逻辑，都视为创新 / module trial 代码变动，而不是普通 tune/ablation。此时必须记录 `module_source.md`、`implementation.md`、`framework_diagram.md`，并说明每个模块来源、接入点、输入输出、baseline-off 行为和 GZSL 语义边界。
- 上述创新代码变动所属 Trial 的 `README.md` 必须包含 `## Code Flow Diagram`，用简洁流程图说明代码实际输入、输出、关键张量流向、分支开关和最终 logits/metric 出口；完整变量/方法说明仍放在 `framework_diagram.md`。
- 批量实验 / mixed campaign 不能单独成为正式结果分支。它只能保存 routing index、run map、work item 映射和监控状态；正式结果必须自动回写到 `experiments/vX/<type>/`。旧 Trial/Attempt 路径只能作为 `legacy_ref`，真正的新创新写所属正式框架的 innovation 账本；候选无 Tag，确认晋级后才注册为新的同级正式框架。

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
thread_archive_policy、archive_completed_threads_on_stage_end、archived_threads_record
agent-cleanup-plan 输出和 archive_result 记录
dataset/split/label mapping 假设
GPU 或 runner slot 锁
result/artifact 写入位置
checkpoint retention 规则
```

如果 label mapping、seen/unseen split、class order、logits shape 或 metric semantics 不清楚，必须硬阻断。
所有正式实验必须满足 `docs/workflow/reference/GZSL_HARD_RULES.md`。

## 6. Checkpoint 保留规范

工作流规范：

```text
每轮实验结束后删除非保留 checkpoint。
除非 playbook 明确另有规定，否则只保留最好的 3 个模型 checkpoint（Top-3）。
永远不要删除 logs、manifest、result、quality_check 或 Warehouse receipt。
```

删除范围必须限制在实验生成的 checkpoint 内，不能碰用户数据或源码历史。

## 7. Promotion 门

只有证据明确支持时才能开始 promotion：

```text
promotion_decision: promote
完整 manifest/result/quality/interface evidence
必要时有 repeat 或 confirmation evidence
目标版本已声明
没有未解决硬门
```

promotion 可以按协议创建本地文件、commit 和 tag，但不能 push，除非 owner 明确要求。

## 8. 停止规则

遇到下面情况要停止或降级：

- 必要证据缺失。
- 服务器/runtime 状态不清楚，可能污染结果。
- workflow 要求正式多 agents，但当前没有真实 multi-agent 支持。
- `activation_mode: real_multi_agent` 但没有真实左侧命名 Codex 线程实例、pre-run allow/check 或 `agent_runtime.yaml`。
- `multi_agent_preflight` 未通过，或 `formal_runner_allowed` / `formal_evidence_allowed` 不是 true。
- owner 改变范围。
- 会跨越安全边界。

停止时只汇报最小 unblock 动作。

## Live Monitor 运行期规则

`live_multi_agent_monitor` 的正式定义是：左侧命名 Codex 线程参与，Runner 可在服务器执行，但当前 owner 线程持续作为监控入口。Runner 仍在 running/pending 时，不得把本轮 active named threads 归档；归档只能发生在 closeout/handoff 后。

每轮监控必须调用或等价执行：

```powershell
python workflow\gtpj_workflow.py monitor-workflow --run-dir <run_dir> --report-new-completions --activity-log <attempt_dir>\AGENT_ACTIVITY.md
```

新增 completed job 必须逐条报告并写入 agent activity。报告至少包含 `job_id`、H/U/S/ZS、当前 best、H>=75/H>=76 命中情况、证据文件和下一步。只看到 server screen 存在或目录存在，不等于监控完成。

## 9. 反膨胀规则

瘦身优先：新增规范、流程或文档前，先检查能否合并、删减或复用现有入口；默认写最小可执行规则，不为完整感新增层级。

新增 workflow 文件、模板或协议前，必须至少满足一项：

```text
可机器检查
能驱动 evidence_state transition
是权威事实源
是正式 evidence 必需模板
```

如果都不满足，不进入日常 workflow。

## 免 owner 日常参与的两轮代码审核

Owner 不参与日常代码审核。Implementer 完成机器验证后，先交给只读子 Agent A 做第 1 轮；问题关闭并重测后，再交给不同的只读子 Agent B 做第 2 轮。两轮必须针对同一份最终代码，且都为 `pass`、未解决阻断为 0。任何一项不满足时，不能进入正式 Runner、keep/best、confirmation、promotion、baseline 或 paper claim。

旧的 `review_tier`、`fast`、`review-1`、`strict-3` 与 `validate-ai-cross-review` 只用于读取历史审核包，不用于决定新代码的审核轮数。push、删除、远端发布和破坏性迁移仍然需要 owner 明确授权。



---

# 归档五：docs/workflow/README.md 与 core/（V6 替换前）

以下七个旧导航与核心文件是 `source_commit` 中的原文快照；只用于历史回查。

---

## docs/workflow/README.md

# GTPJ 工作流

本目录不再要求作为一整片协议森林来阅读。

`WORKFLOW_MANIFEST.yaml` 是当前文档瘦身索引：它把 workflow 文件标成
`daily_entry`、`core`、`playbook`、`protocol`、`reference`、`agents` 和
`archive`。日常只看入口和一个 playbook；长协议只按 playbook 点名读取。

日常规则：

```text
先读 START_HERE.md
再读 WORKFLOW_KERNEL.md
再读一个相关 playbook
只有路由不清楚或 playbook 明确要求时，才读 core/protocols/reference/archive
```

## 当前有效入口

| 文件 | 用途 |
|---|---|
| `START_HERE.md` | 人话入口。每个 GTPJ 工作流任务先从这里开始。 |
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
| `core/AGENT_RUNTIME_HARD_GATE.md` | 正式 Runner 启动前的左侧命名 Codex 线程硬门。 |

## 执行卡 Playbooks

每种任务只选一个执行卡：

```text
docs/workflow/playbooks/paper_intake.md
docs/workflow/playbooks/paper_to_experiment.md
docs/workflow/playbooks/tune.md
docs/workflow/playbooks/ablation.md
docs/workflow/playbooks/confirmation.md
docs/workflow/playbooks/innovation.md
docs/workflow/playbooks/promotion.md
docs/workflow/playbooks/mixed_campaign.md
docs/workflow/playbooks/autonomous_campaign.md
```

这些 playbook 是很薄的操作卡，只在任务真的需要细节时才指向旧的长协议。

## 当前简化规则

旧的详细文件保留作审计和边界场景参考，不再作为日常必读。

如果多个工作流文件冲突，按下面优先级处理：

```text
本轮 owner 明确要求
WORKFLOW_KERNEL.md
START_HERE.md
core/WORKFLOW_ROUTER.md
core/TASK_START_CARD.md
被选中的 playbook
protocols/reference 文件
archive 历史文件
```

GitHub 仍然是工作流规范的权威来源。本地 Codex skill 只是执行镜像，工作流规则改变后必须同步。

正式实验的最短硬门：

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

正式待跑实验的最短查询链是：

```text
experiments/vX/<type>/INDEX.md
-> experiments/vX/<type>/<TYPE-xxx>/PARAMETER_MATRIX.csv
-> 旧 experiments/module_trials/... 仅由 legacy_ref 回查
-> .gtpj_runtime/batches/<run_id> 只核对执行状态
```

`.gtpj_runtime` 不是正式待跑表；没有正式表格行的运行目录统一视为 `orphan_runtime_plan`。

组合实验用同一个入口自动路由：

```bash
python workflow/gtpj_workflow.py start --phrase "跑2创新+8调参"
```

论文到实验闭环用桥接执行卡，不直接从 paper intake 开训；正式实验必须由 owner 指定 base version：

```bash
python workflow/gtpj_workflow.py start --phrase "基于 v5 从论文开始做实验"
```

最小闭环是：

```text
plan -> agent_runtime -> preflight -> runner -> evidence -> cleanup -> sync
```

不要为了“完整”默认搬运或阅读整个 `docs/workflow/`。

检查当前瘦身索引：

```bash
python workflow/gtpj_workflow.py list-workflow-files
python workflow/gtpj_workflow.py validate-workflow-consistency
```

---

## docs/workflow/core/QUICK_START.md

# GTPJ 工作流快速入口

## 先认代码起点

- `TEMPLATE.yaml` 登记框架的只读代码母版 `MODEL-VX-TEMPLATE-VN`。
- `EXPERIMENT.yaml` 登记当前实验实际从哪份母版、哪个准确提交开始。
- 没有这两份身份记录，不得启动新的正式实验。

现在的精简入口是：

```text
docs/workflow/START_HERE.md
docs/workflow/WORKFLOW_KERNEL.md
```

本文件只作为 owner 人话短语速查表。

## Owner 三句入口

| owner 口令 | 含义 |
|---|---|
| `本地正式，干净` | 启动 `live_multi_agent_monitor`；确认侧边栏干净，并授权创建本轮左侧命名 Codex 线程；不启动服务器 runner。 |
| `开启多agents智能体工作流，开始` / `开启多agents智能体工作流，跑N轮` | 启动 `live_multi_agent_monitor`；不再反复确认 workflow 模式或启动意图；通过硬门后继续创建角色、生成计划并启动对应 runner。 |
| `服务器冻结，开始` | 启动 `server_frozen_runner`；不创建命名线程，允许走服务器 detached runner。 |
| `只做本地规划` | 使用 `role_only`；只做本地计划、账本、状态和 debug/smoke，不进入正式证据。 |

如果 owner 只说 `本地正式`，Coordinator 只问：`侧边栏干净吗？回复：干净。`

如果 owner 已经说 `开启多agents智能体工作流`、`开始`、`跑N轮` 或 `做N轮实验`，Coordinator 不得再要求长授权模板，也不得把任务停在“只规划”。只有模式不明、侧边栏未确认且无法验证、硬门失败或安全边界动作，才允许再问一次。

## 通用话入口

| 你可以直接说 | Coordinator 必须做 |
|---|---|
| `规划下一轮实验` / `下一轮怎么跑` | 运行 `plan-experiments`，自动读当前 repo、ledger、result/quality 和 runtime context，输出三张规划表。 |
| `批量规划50轮实验` / `给我规划50轮` | 运行 `plan-experiments --max-jobs 50`；只规划，不启动 Runner。 |
| `规划10创新+100调参` / `跑10创新+100调参` | 解析成 mixed campaign workstreams，先出规划表，再进入 campaign gate。 |
| `按这个计划开多agents工作流` | 解释为 `live_multi_agent_monitor`；通过 agent_runtime 和 preflight 后才能启动正式 Runner。 |
| `按这个计划服务器冻结跑` | 解释为 `server_frozen_runner`；训练运行期不创建命名线程，走服务器 detached gate。若涉及代码/helper/template 改动，先完成代码审核门。 |

代码审核不被 `server_frozen_runner` 豁免：改代码、workflow、helper、模板或训练配置生成逻辑时，先跑机器验证，再由两个不同的只读子 Agent 依次做两轮对抗式审核。第 1 轮问题修复、重测并复核通过后才能开始第 2 轮；两轮绑定同一个最终 `reviewed_code_id`，都通过后才允许正式训练。

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
agent_instance_mode: named_owner_thread
lifecycle: workflow_scoped
```

长期 agent 是文件支撑的角色身份和累积证据，不等于必须常驻的聊天窗口。

`persistent_thread` 是可选活上下文，适合可见的长周期监控，但不能替代文件、日志、result、quality check 或 Warehouse artifact。

正式写入或运行前，先按 `START_HERE.md` 输出启动摘要；需要正式证据时再填写完整 task card。

baseline 复现状态仍然是硬门。状态比较、best 选择、复现确认、升版、tag/version 表述前，必须运行或记录：

```bash
python workflow/gtpj_workflow.py repro-status --version <vX>
```

启动摘要必须包含 `baseline_repro_status`。除非 `confirmed_H` 和 `confirmation_status` 支持，否则不能把 `best_observed_H` 当成已确认 baseline。

---

## docs/workflow/core/WORKFLOW_ROUTER.md

# GTPJ Workflow Router

正式写入前先绑定 `FRAMEWORK-VX`。调参写 `VX-TUNE-xxx`，消融写 `VX-ABLATION-xxx`，
创新写 `VX-INNOVATION-xxx`，确认写 `VX-CONFIRM-xxx`。旧 `TRIAL / ATTEMPT` 只作为
`legacy_ref`；创新通过确认和接纳后，才允许注册新的同级正式框架 `FRAMEWORK-VY`。

## 默认 agent 路由

Router 默认把真实实验类任务路由到 `real_multi_agent`，并把正式角色实例路由到 workflow-scoped
`named_owner_thread`。如果目标是服务器 detached 连续训练、owner 明确不希望创建线程，允许走第二条正式路径：`role_only + formal_runtime_backend=server_detached_role_only`。无论哪条路径，正式事实都必须沉淀到文件和 artifact。

默认 `real_multi_agent` 的范围包括：真实 Runner、正式 attempt/result/quality 证据、代码或配置语义变化、结果解释、best 选择、promotion、版本判断、论文实验路线或下一轮高成本实验决策。

`role_only` 默认只允许用于纯只读状态/解释、训练前候选 triage、不改变结论的机械账本格式整理，或 debug/smoke 且结果不进入正式证据。唯一正式例外是 `server_detached_role_only`：它要求独立 sequential role outputs、formal gate 和 detached server monitoring。

`named_owner_thread` 是本轮 workflow / campaign 的活上下文默认形态。`persistent_thread` 只在角色需要跨多个 workflow 连续追踪、owner 明确要求可见长期线程，或当前 campaign 的 Coordinator/Monitor 需要跨天保留连续上下文时启用。若采用 `server_detached_role_only`，则不创建线程，改为 owner 当前线程 + 独立 role outputs + server status files 共同构成 formal gate。无论使用哪种形态，正式证据都必须写入 repo、Research、Warehouse、result、quality 和 agent summary。

本文件是 GTPJ 的总教官。它不替代具体协议，而是在任何任务开始前先做路由判断：

```text
用户请求 -> 任务类型 -> 是否进入 idea_tree -> 写入位置 -> 需要读取的协议 -> agents -> gates
```

默认范围：本 Router 只服务“跑实验、做创新、复现、消融、调参、debug 和实验结果记账”。

Owner 不需要说“开启动卡”或自己判断任务类型。默认先读 `START_HERE.md`；`QUICK_START.md` 只作为人话短口令备忘。
Owner 可以只说：

```text
查状态
复现
调参
消融
开新模块
开下一个新模块
试这个：<一句话想法>
读论文
基于 vX 从论文开始做实验
全自动研究 campaign
跑10创新+100调参
继续上一个
别问，给我三个候选
升版本
切版本
```

Router 和 Coordinator 必须自动判断这是什么任务、能不能开工、缺什么、下一步最小动作是什么。
不要要求 owner 口头说 `module trial`、`innovation workflow`、`real_multi_agent`、`Review 0-3`、
`artifact boundary` 或 `pre-run freeze`。这些内部词由 Coordinator 展开到 mini 启动卡和完整启动卡。

如果其它文档分散描述了某条规则，先用本文件判断任务归类，再进入对应协议细节。

## Owner 人话入口

| owner 口令 | Router 默认归类 | 默认行为 |
|---|---|---|
| `查状态` | read-only status | 只读检查仓库、active baseline 复现状态、队列和阻塞项。 |
| `复现` | confirmation | 默认先查当前 active baseline 是否已复现；未要求正式证据时优先 `quick_local` 或准备路径。 |
| `调参` | tune | 默认当前 active baseline；先给最多 3 个候选，不直接训练。 |
| `消融` | ablation | 确定目标框架和单一消融因素，并先检查接口门。 |
| `读论文` / `找创新点` | paper intake / idea discovery | 只做来源复核和候选创新登记，不直接开 trial 或训练。 |
| `基于 vX 从论文开始做实验` / `论文到实验闭环` | paper -> idea -> module trial closed loop | 缺 owner 指定 base version 时只读论文和建候选；成熟 IDEA 进 selected queue 且指定 base code tag 后才进入正式实验硬门。 |
| `开新模块` | innovation / module trial | 基于当前 active baseline，从 selected ready idea 队列自动选一个，不 push。 |
| `开下一个新模块` | innovation / module trial | 明确继续当前版本 selected 队列的下一个 ready idea。 |
| `试这个：...` | local heuristic idea 或 innovation / module trial | 先判断能否成为 idea / trial，不能直接跳过 source 和 interface gate。 |
| `全自动研究 campaign` | autonomous research campaign | owner 给来源、评估标准、安全边界和实验标准；Coordinator 自行拆分 paper intake、idea、tune、ablation、confirmation、module trial、promotion 和最终交付。 |
| `跑10创新+100调参` / 任意数量组合 | mixed experiment campaign | 解析 requested_mix，拆成 workstreams，按 `mixed_experiment_campaign_protocol.md` 调度 agents、Runner、证据和收口。 |
| `继续上一个` | 当前正式框架实验续跑 | 优先读取框架四类账本；旧 trial/attempt 只用于定位兼容证据。 |
| `别问，给我三个候选` | read-only idea selection | 只读列候选，不改代码、不建 trial。 |
| `升版本` | promotion | 检查 promotion gate，不把单次 H 提升直接当 baseline。 |
| `切版本` | set-current-version 或 activate-version | 默认只解释差异；activate-version 必须 owner 明确授权。 |

`开新模块` 的 ready idea 必须满足：有 `idea_id`、当前版本 `version_scores`、`selected/ready`
状态、空 blockers、明确 source/ref/status、hypothesis、implementation scope 和 risk。没有 ready idea
时，只问一个最小问题。

## 0. 优先级

发生冲突时按下面顺序处理：

1. 用户本轮明确要求。
2. 安全边界：不 push、不发布、不删远端、不重写历史，除非用户明确要求。
3. 复现状态硬门：先判断 `baseline_repro_status`，不能把未确认 `best_observed_H` 当 confirmed baseline。
4. 硬门：`code_interface_contract.md`、`quality_gate.md`、`promotion.md`。
5. 本文件的路由判断。
6. 具体协议：`idea_tree_protocol.md`、`experiment_protocol.md`、`module_trial_protocol.md` 等。
7. `IMPLEMENTATION_STATUS.md` 的已落地/按需创建状态。

Router 只负责决定走哪条路；证据是否有效，由接口硬门、质量门和 promotion gate 决定。

## 0.1 复现状态快速判定

每次 `查状态`、`复现`、`升版本`、结果比较、tag 或 promotion 前，Coordinator 必须读取当前版本的
`evidence_level`、`best_observed_H`、`confirmed_H`、`confirmation_status` 和 `status`，或直接运行：

```bash
python workflow/gtpj_workflow.py repro-status --version <vX>
```

判定：

```text
confirmation_status=confirmed 且 confirmed_H 非 pending -> confirmed baseline。
best_observed_H 有值但 confirmed_H=pending -> unconfirmed reference。
status=owner_activated_unconfirmed -> active code 可以使用，但 baseline-grade 结论必须阻断。
```

因此，`H=74.29` 这类单次高点只能写成 `best_observed_H`，不能让 agent 凭记忆或聊天上下文把它当
已复现 baseline。任何 mini 启动卡如果涉及状态、复现、比较或 promotion，`gates` 必须包含
`baseline_repro_status`。

## 1. 总判断规则

最重要的两条：

```text
实验是为了调/查/验证已有正式 baseline -> experiments/vX，不进 idea_tree。
实验是为了调/查/确认旧 module trial 内部模块 -> 回到所属 FRAMEWORK-VX 的四类账本，用 legacy_ref 指旧证据。
实验是为了证明一个新方法值得存在 -> idea_tree + 所属正式框架 innovation 账本；候选无 Tag，接纳后才注册新的同级正式框架。
```

不要因为一次实验有“想法”两个字就写入创意树。只有可复用的新机制、新模块、新方法，或者可能成为新 baseline 的设计，才进入 `idea_tree/`。

## 2. 任务分类表

| 用户请求 | 任务类型 | 是否进 `idea_tree/` | GitHub 写入 | 本地外部写入 | 必读协议 | 必需 agents/gates |
|---|---|---:|---|---|---|---|
| 读一篇论文，找创新点 | paper intake / idea discovery | 候选成熟后才进 | `idea_tree/sources/`、必要时 `idea_tree/inbox.md` 或 `idea_tree/ideas/` | `GTPJ_Research/papers/`、`notes/`、`source_reviews/`、`ideas/` | `docs/workflow/protocols/paper_intake.md`, `docs/workflow/protocols/idea_tree_protocol.md` | Reader/Planner，source review |
| 基于 vX 从论文开始，形成创新并验证 | paper -> idea -> module trial closed loop | 成熟 IDEA 才进 | `idea_tree/sources/`、`idea_tree/ideas/`、`idea_tree/queues/`、`experiments/module_trials/` | `GTPJ_Research`、`GTPJ_Warehouse`、服务器 runner 状态 | `docs/workflow/playbooks/paper_to_experiment.md` 加 paper intake / idea_tree / module template / module trial 协议 | Reader/Planner、Source Reviewer；正式 trial 前加 Implementer、Interface Checker、Runner、Quality Checker、Reviewer，并通过 base_code_tag / module_source / agent_runtime / preflight / cleanup |
| 给论文来源、评估标准、安全边界和实验标准，让 workflow 全部接管 | autonomous research campaign | 由子任务决定 | campaign ledger、`idea_tree/`、`experiments/` 各子目录 | `GTPJ_Research`、`GTPJ_Warehouse`、服务器 runner 状态 | `autonomous_research_campaign.md` 加各子任务协议 | Coordinator、Source Reader、Idea Planner、Runner Monitor、Log Metric Parser、Result Comparator、Evidence Quality Checker，按阶段加 Implementer/Interface/Reviewer/Promotion |
| 任意组合实验，例如 `跑10创新+100调参` | mixed experiment campaign | 由 workstream 决定 | `experiments/campaigns/` + 各实验归属目录 | `GTPJ_Warehouse`、必要时 `GTPJ_Research`、服务器 runner 状态 | `mixed_experiment_campaign_protocol.md` 加各子任务协议 | Workflow Coordinator、Campaign Planner、Runner Monitor、Result Comparator、Evidence Quality Checker；按 workstream 加专用角色 |
| 自己想到一个新机制 | local heuristic idea | 是，但先写来源和假设 | `idea_tree/inbox.md` 或 `idea_tree/ideas/IDEA-xxxx/` | `GTPJ_Research/ideas/` | `idea_tree_protocol.md` | Reader/Planner，Interface Checker 预审 |
| 调正式 baseline 的参数、seed、epoch、loss weight | tune | 否 | `experiments/vX/tune/` | Warehouse logs/runs | `experiment_protocol.md` | Coordinator、Runner、Log Analyst、Quality Checker |
| 对正式 baseline 做关掉/旁路/替换已有模块看贡献 | ablation | 否 | `experiments/vX/ablation/` | Warehouse logs/runs | `experiment_protocol.md`, `code_interface_contract.md` | Implementer、Interface Checker、Runner、Quality Checker |
| 复现 baseline 或确认某个版本级结果 | confirmation | 否 | `experiments/vX/confirmation/` | Warehouse logs/runs | `experiment_protocol.md` | Runner、Log Analyst、Quality Checker |
| 调某个旧 module trial 的参数、头数、ratio、dropout、seed | 所属正式框架 tune | 已有 idea | `experiments/vX/tune/`，并用 `legacy_ref` 回指旧 Trial | Warehouse logs/runs | `experiment_protocol.md`, `module_trial_protocol.md` 仅查旧证据 | Coordinator、Runner、Log Analyst、Quality Checker、Result Analyst |
| 对某个旧 module trial 做窄消融或 clean confirmation | 所属正式框架 ablation / confirmation | 已有 idea | `experiments/vX/ablation/` 或 `experiments/vX/confirmation/`，并用 `legacy_ref` 回指旧 Trial | Warehouse logs/runs | `experiment_protocol.md`, `code_interface_contract.md` | Coordinator、Interface Checker 视风险、Runner、Log Analyst、Quality Checker、Result Analyst |
| debug、smoke test、环境验证 | debug / smoke | 否 | 通常不写；若结果要引用，必须转为对应实验目录并标明 `evidence_level: debug_smoke`、`formal_evidence: false` | 可写临时本地输出；长期证据进 Warehouse | `docs/workflow/protocols/experiment_protocol.md` 视情况 | 不得作为有效结果，除非补齐 manifest/result/quality 并重新按正式证据运行 |
| 加新模块、新结构、新 forward 路径、新 loss 机制，或把 idea/创新落成代码 | framework innovation | 是 | `idea_tree/` + `experiments/vX/innovation/` | Research 长推理，Warehouse 运行证据 | `idea_tree_protocol.md`, `experiment_protocol.md`, `code_interface_contract.md`, `innovation_code_review_protocol.md` | Reader/Planner、Implementer、Interface Checker、Runner、Quality Checker、Reviewer；按风险多轮审查 |
| 结果想成为新 baseline | promotion | 通常已有 idea 或实验来源 | `config/versions/vY.yaml`、`experiments/vY/`、`experiments/VERSION_TREE.md` | Warehouse 证据引用 | `docs/workflow/protocols/promotion.md`, `docs/workflow/protocols/quality_gate.md`, `docs/workflow/protocols/versioning.md` | Coordinator、Quality Checker、Reviewer、Result Analyst |
| 只切换创意树当前视图 | set-current-version | 使用已有 idea_tree | `idea_tree/idea_tree.json`、`idea_tree/versions/vX.md` | 不写 | `idea_tree_protocol.md` | 不切 main active code |
| 切换 main 当前运行代码到某版本 | activate-version | 否 | `config/GTPJ_*.yaml` 等 active code/config | 不写 | `versioning.md`, `git_policy.md` | 必须 owner 明确要求 |
| 创建或查看运行看板状态 | progress dashboard | 否 | 不写长期 GitHub 账本 | `.gtpj_runtime/` | `progress_dashboard.md` | 只读看板，不启动训练 |

## 2.1 正式待跑表格

当 owner 问“有哪些待跑实验”“表格中有没有”时，Coordinator 必须从正式表格回答，而不是从
`.gtpj_runtime/` 目录数量回答。

| 范围 | 正式表格 | 待跑行由什么决定 | runtime 的作用 |
|---|---|---|---|
| 框架 tune | `experiments/vX/tune/INDEX.md` | `Status` 为 `planned`、`pending`、`pre_run`、`pre_run_gated` 或 `ready_to_run` 的实验行 | 只核对运行包和事件，不新增待跑事实 |
| 框架 ablation | `experiments/vX/ablation/INDEX.md` | 同上，且实验类型必须是 ablation | 只核对运行包和事件 |
| 框架 innovation | `experiments/vX/innovation/INDEX.md` | 同上，候选仍归所属正式框架且没有 Tag | 只核对运行包和事件 |
| 框架 confirmation | `experiments/vX/confirmation/INDEX.md` | 同上，且目标必须是 baseline、candidate 或正式 config | 只核对运行包和事件 |
| mixed campaign | `experiments/campaigns/.../WORK_ITEMS.md` / `RESULT_INDEX.md` | 只列 work item；每个 work item必须回指上述四类正式表格行 | 只核对调度和 monitor 状态 |

正式待跑的统一判定名为 `formal_pending`。如果 `.gtpj_runtime/batches/<run_id>` 存在，但上面任一正式表格都没有对应行，判为 `orphan_runtime_plan`。`orphan_runtime_plan` 只能作为历史参考、排障证据或重新登记新实验的输入，不能直接续跑，也不能进入 keep / best / confirmation / promotion。

debug/smoke 不进入正式待跑表。若必须长期保留，只能写成 `evidence_level: debug_smoke`、
`formal_evidence: false`，并放在对应实验目录的 debug 记录或 Warehouse 引用里。

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

- 框架 tune 参数搜索。
- 框架 ablation 问题本身。
- 框架 confirmation 复现实验。
- 来源于旧 module trial 的 param_tune、窄 ablation、confirmation/rerun。
- debug/smoke test。
- 只为了排查环境、日志、cache 或数据路径。

框架调参或消融中如果发现了可复用新机制，先把原实验记入 `experiments/vX/...`，再创建 idea 和
`INNOVATION-xxx`。旧 module trial 的后续动作如果超出原实现假设，则在所属正式框架新建创新实验，
不要继续扩大旧 Trial 目录。

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
| 四类正式实验配置、manifest、result、quality_check | `experiments/vX/<type>/...` |
| 旧模块 Trial/Attempt 证据 | 原目录保留，只由正式实验用 `legacy_ref` 引用 |
| raw logs、checkpoint、generated figures、failure cases | `GTPJ_Warehouse`；模型 checkpoint 按 retention 规则最多保留 3 个 |
| 运行中状态 | `.gtpj_runtime/`，不进 Git |
| 本机真实路径 | `.gtpj/local_paths.yaml`，不提交 |

## 6.1 联动更新规则

GitHub 和本地不是机械“每次同时写”，而是按任务类型成对更新：

| 触发场景 | 先写 | 后写 | 收尾检查 |
|---|---|---|---|
| 读论文、提取创新点 | `GTPJ_Research/papers/`、`source_reviews/`、`ideas/` | GitHub `idea_tree/sources/`、`idea_tree/ideas/` 轻量索引 | GitHub 有 `research://` 或本地路径指针 |
| 用户提出新机制 | `GTPJ_Research/ideas/` 长版动机/机制/风险 | GitHub `idea_tree/inbox.md` 或正式 `IDEA.md` | `source_status` 和 owner 接受理由可追溯 |
| 创新实验运行 | Warehouse raw artifacts | GitHub 所属正式框架 `innovation/` 的 matrix/manifest/result/quality | GitHub artifact URI/hash/size 可反查 Warehouse |
| trial 改变 idea 结论 | Research `decision_history.md`、`experiment_plan.md` | GitHub `idea_tree.json`、`IDEA.md`、版本视图 | 人类版和机器版状态一致 |
| framework tune/ablation/innovation/confirmation | Warehouse + GitHub `experiments/vX/...` | 创新需要 Research 来源，其他类型通常不写 | 若产生新机制，再另走 idea discovery |

如果某个结论影响后续实验选择、promotion、版本适配分或论文叙述，不能只留在聊天里。
Coordinator 收尾时必须说明：

```text
GitHub 写了什么：
Research 写了什么：
Warehouse 写了什么：
哪些内容没有联动，为什么：
```

Paper intake 的细化流程见 `docs/workflow/protocols/paper_intake.md`。论文是否读过、读到哪一步，以
`GTPJ_Research/papers/PAPERS_INDEX.md` 为准，不以 PDF 是否存在为准。

## 7. Agent 路由

| 任务类型 | 默认 agents |
|---|---|
| paper intake / idea discovery | Coordinator、Reader/Planner |
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
- 必须用 `real_multi_agent` 的任务，默认启动 workflow-scoped named threads，并把只读审查角色并行执行，不串行排队等待。
- Runner 串行并持有 GPU lock；同一代码路径只能有一个 Implementer；Coordinator 是最终账本 writer。
- 被跳过的 agent 必须在启动卡 `agents.decision_basis.fastest_valid_path.skipped_agents` 中说明。
- 如果启用了 persistent thread，启动卡必须列出 thread id 或可见 label；如果未启用，必须说明状态如何写回 campaign ledger、agent_summary、memory 或 issues。

Runner 串行。多个 agents 可以并行读文档、审查和分析，但同一代码路径只能有一个 writer。
`Experiment Runner` 是实际启动训练命令的运行者；`Runner Monitor` 是服务器/GPU/队列/失败隔离监控者。小规模任务可由同一 Runner family 承担，但启动卡和 summary 必须写清楚显示名、`role_key` 和职责。

## 8. 强制阻断

以下情况 Router 必须阻断继续执行：

- 当前动作试图 push、发布、删除远端或改写历史，但用户未授权。
- 当前任务会写 raw logs、checkpoint 或 generated figures 到 GitHub。
- 任务需要有效实验结果，但缺少 split、label mapping、class order、logits shape 或 metric semantics。
- module trial 没有 idea_id。
- idea 的 `source_status` 是 `unknown` 或 `unverified`，却要开 trial。
- idea / 创新 / module trial 将改代码，但没有遵守 `innovation_code_review_protocol.md` 的
  Review 0-3 多轮审查。
- 创新代码改动的 task-start card 没有写 `agents.activation_mode: real_multi_agent`
  或没有列出 `required_real_agents`。
- 正式 evidence、best、promotion 或 owner 明确要求多 agents，但 task-start card 没有写
  `agents.agent_instance_mode`、`lifecycle` 和各角色独立输出位置。
- promotion 只凭一次 H 提升，没有完整 manifest/result/quality/interface 证据。
- promotion 或 baseline 表述只凭 `best_observed_H`，没有 `confirmation_grade` /
  `baseline_grade` 证据。
- 运行前 dirty、`run_commit` 不明确，或 `git_dirty: true`，却要把结果写成 confirmed /
  stable baseline。
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
最快合规路径：
硬门：
当前阻塞：
下一步最小动作：
```

这个摘要是给 owner 和后续 agent 的共同入口。

---

## docs/workflow/core/TASK_START_MINI.md

# Task Start Mini Card

本文件定义 owner 可见的极简启动卡。完整 `TASK_START_CARD.md` 仍然是正式审查模板，但默认由
Coordinator 在后台展开；owner 日常只看这些最小字段。

只读预览入口：

```bash
python workflow/gtpj_workflow.py start --phrase "开新模块"
```

该命令只打印下面的字段，不写文件、不建分支、不跑训练。

## 1. Mini 启动卡

```yaml
owner_phrase:
task_type:
workflow_mode:
base_version:
base_template_id:
base_template_tag:
base_template_commit:
template_ledger: experiments/vX/TEMPLATE.yaml
experiment_binding: experiments/vX/<type>/<experiment-id>/EXPERIMENT.yaml
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

`workflow_mode` 必填：`live_multi_agent_monitor` 表示动态多 agents 监控工作流；
`server_frozen_runner` 表示本地规划、冻结计划、服务器 detached 训练工作流。
owner 只说“用工作流”但没有说明哪一种时，必须先确认这一项，不能由 Coordinator 猜测。

字段含义：

| 字段 | 含义 |
|---|---|
| `owner_phrase` | owner 的原始口令，例如 `开新模块`、`复现`、`试这个：...`。 |
| `task_type` | Coordinator 路由后的任务类型。 |
| `base_version` | 默认当前 active baseline；只有 owner 明确指定时才改历史版本。 |
| `base_template_id` | 本实验复制的只读母版编号，例如 `MODEL-V5-TEMPLATE-V1`。 |
| `template_ledger` | 母版身份来源，必须是所属框架的 `TEMPLATE.yaml`。 |
| `experiment_binding` | 实验起点记录，必须是本实验目录的 `EXPERIMENT.yaml`。 |
| `target` | 本次目标，例如 baseline、参数、idea、trial 或候选列表。 |
| `subject_id` | 本次被路由或检查的对象，例如 `TRIAL-003`、`ATTEMPT-007`、`RUN-...`、`CAMP-...`。 |
| `evidence_state` | 当前证据成熟度；正式状态必须能由 `TRANSITIONS.jsonl` 派生。 |
| `writes` | 本次会写哪里；只读任务写 `none`。 |
| `agent_mode` | `role_only` 或 `real_multi_agent`，附一句为什么。 |
| `agent_instance_mode` | `role_only`、`named_owner_thread` 或 `persistent_thread`；正式实验默认 workflow-scoped `named_owner_thread`，跨 workflow 连续追踪才启用 `persistent_thread`。 |
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

Mini 启动卡是 owner-facing 摘要，不替代完整卡。只要任务会改文件、跑实验或登记结果，
Coordinator 必须能从 mini 卡展开出完整 `TASK_START_CARD.md` 字段：

```text
router
version
inputs
agents
hard_gates
expected_outputs
stop_if
```

如果 mini 卡里出现阻断，先停在最小补齐动作，不创建分支、不建实验目录、不启动训练。

## 3. 示例

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
agent_instance_mode: named_owner_thread, lifecycle workflow_scoped
runner_scope: formal_runner
formal_runner_allowed: false until multi_agent_preflight pass
formal_evidence_allowed: false until formal Runner completes with evidence chain
agent_runtime_gate: required before Runner; must record left_sidebar_named_threads
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
agent_instance_mode: 正式运行用 named_owner_thread；跨 workflow 追踪才用 persistent_thread
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
confirmation_policy:
  repeat_type: exact_repeat
  original_seed: must match source result
  max_attempts: 5
  max_attempts_hard_cap: true
  early_stop_on_best_hit: true
  restore_target_H: must be reached to count as reproduced
  near_miss_tolerance_H: default 0.2, records hope only
  near_miss_not_restored: true
  seed_sweep_or_multi_seed_stability: not_confirmation_evidence
```

同一候选不管是否还原成功，exact repeat 最多 5 次；命中 `restore_target_H` 可提前停止，5 次未命中则收口为 not restored / near miss。

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
agent_instance_mode: 纯 triage 用 role_only；进入正式证据后用 named_owner_thread
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
agent_instance_mode: named_owner_thread, lifecycle workflow_scoped; persistent_thread optional for cross-workflow coordinator/monitor
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
agent_instance_mode: named_owner_thread, lifecycle campaign_scoped/workstream_scoped/task_scoped/run_scoped
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

---

## docs/workflow/core/TASK_START_CARD.md

# Task Start Card

启动卡必须显式写 `workflow_mode`，只能是：
- `live_multi_agent_monitor`：动态多 agents 监控工作流，要求 `activation_mode: real_multi_agent`、`agent_instance_mode: named_owner_thread`。
- `server_frozen_runner`：本地规划、冻结计划、服务器 detached 训练工作流，要求 `activation_mode: role_only`、`formal_runtime_backend: server_detached_role_only`、`thread_creation_allowed: false`。

如果 owner 只说“用工作流”，Coordinator 必须先确认是哪一种；不能默认把任务冻结到服务器跑，也不能自动创建命名线程。

如果 owner 已经说“开启多agents智能体工作流”“多agents智能体工作流，开始”“跑N轮”或“做N轮实验”，启动卡必须直接写 `workflow_mode: live_multi_agent_monitor`，不得反复确认 workflow 模式或启动意图。只有模式冲突、侧边栏干净状态缺失且无法验证、硬门失败或安全边界动作，才允许再问一次。包含“开始/跑N轮/做N轮实验”的请求视为执行授权；通过 hard gate 后必须继续到 runner 计划和启动动作，而不是停在 planning gate。

## 默认真实多 Agent 策略

启动卡默认应为真实实验写：

```yaml
agents:
  activation_mode: real_multi_agent
  agent_instance_mode: named_owner_thread
  lifecycle: workflow_scoped
  formal_runner_allowed: true
  formal_evidence_allowed: true
  owner_monitor_mode: true
  owner_role: monitor
```

原因是不同角色必须拥有独立上下文，避免规划、执行、日志解析、质量检查、结果解释和复核互相污染。
`named_owner_thread` 在这里不是“一次性几分钟工具”，而是本轮 workflow / campaign 的活上下文。
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

如果没有真实左侧命名 Codex 线程、没有 `named_threads.instances`、没有 pre-run allow/check，
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

如果当前主对话要暂停或结束，必须先给出监控交接：

```text
monitor_handoff_on_pause: required
当前状态：
下一次检查命令：
可见活动流：
跑完后接手 agents：
```

如果启用 persistent thread，启动卡必须列出 thread id 或可见 label。如果不启用，启动卡必须写明本轮 workflow-scoped agents 如何把状态写回 `agent_summary.md`、result、quality、Research、Warehouse 或 campaign ledger。

本文件是每次 GTPJ 工作开始前由 Coordinator 自动生成的启动卡。它不替代
`WORKFLOW_ROUTER.md`，而是把 Router 的判断落成一张可检查的任务单，避免每次靠口述重新解释。

Owner 不需要说“开启动卡”，也不需要自己填表。Coordinator 默认先读 `START_HERE.md`，
`QUICK_START.md` 只是短口令备忘；Coordinator 先输出 `TASK_START_MINI.md` 的 8 字段 mini
启动卡，再在后台展开完整启动卡字段。

启动卡可以先写在当前对话里。纯规划阶段不要为了启动卡提前创建空 run 目录。只有当 owner 明确同意开工，
或本轮请求已经明确包含“开始/你来操作/跑这个实验”时，才把启动卡转成正式文件、分支、实验目录或运行动作。

## 0. Owner 极简输入

Owner 最简单只需要说这些口令：

```text
查状态
复现
调参
消融
开新模块
开下一个新模块
试这个：<一句话想法>
继续上一个
别问，给我三个候选
升版本
切版本
```

常见说法：

```text
复现。
调参，先给三个候选。
消融，把 topo loss 关掉看看。
开新模块。
开下一个新模块。
试这个：把 CLIP-A-self 接进文本 adapter。
继续上一个。
别问，给我三个候选。
```

如果 owner 只说：

```text
开新模块
```

Coordinator 必须默认理解为：基于当前 active baseline，从该版本 selected ready idea 队列自动选一个
new module trial；允许改代码；走 module trial 合规路径；不 push。若没有 ready idea，只问一个最小问题。

Owner 不需要提前判断：

- 是否进入 `idea_tree`；
- 应该写 GitHub 还是本地 Research/Warehouse；
- 需要哪些 agents；
- 需要哪些 hard gates；
- 分支名、目录名、artifact id 怎么写。
- 是否要说 `real_multi_agent`、`Review 0-3`、`artifact boundary` 或 `pre-run freeze`。

这些都由 Coordinator 在启动卡里给出。

## 0.1 对话先行

每次正式开工前，Coordinator 先输出一个简短判断：

```text
能不能开工：
任务类型：
基于版本：
为什么这样归类：
当前缺口：
下一步最小动作：
```

如果能开工，Coordinator 再给启动卡摘要。
如果不能开工，Coordinator 只问最关键的 1 个问题，或给出最小补齐动作。

在下面情况出现前，不要改代码、跑实验、建实验目录或登记结果：

- owner 明确说“开始”“跑”“你来操作”“按这个做”；
- 或者 owner 本轮请求本身已经明确授权实际操作；
- 或者任务只是只读检查、解释或建议，不会写文件也不会跑训练。

## 1. 使用时机

每次出现下面任一动作前，都先填写启动卡：

- 读论文并准备产出 idea；
- 修改模型、forward、loss、eval 或数据流；
- 跑 tune、ablation、confirmation 或 debug/smoke；
- 登记实验结果、日志、checkpoint 或 generated figures；
- promotion、set-current-version 或 activate-version。

如果只是普通聊天解释，可以不写完整启动卡；但只要要改文件、跑实验或登记结果，Coordinator 就必须自动写。

## 2. 最小启动卡

```yaml
task_id:
date:
owner_request:

router:
  task_type:
  enters_idea_tree:
  github_writes:
  local_writes:
  coupled_update:
    required:
    order:
    skip_reason:
  required_protocols:

version:
  base_version:
  base_code_tag:
  base_template_id:
  base_template_tag:
  base_template_commit:
  template_ledger: experiments/vX/TEMPLATE.yaml
  experiment_binding: experiments/vX/<type>/<experiment-id>/EXPERIMENT.yaml
  current_branch:
  suggested_branch:

inputs:
  paper_or_source:
  idea_id:
  config:
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

experiment_planning:
  required_before_formal_runner: true
  plan_id:
  auto_state_scan:
    repo_state:
    baseline_repro_status:
    formal_pending_ledgers:
    completed_result_quality_refs:
    runtime_cache_context_only:
  evidence_summary_table:
  candidate_decision_table:
  current_run_plan_table:
  runner_start_allowed: false until plan accepted and hard gates pass

workflow_mode:
workflow_mode_reason:

agents:
  activation_mode:
  agent_instance_mode:
  lifecycle:
  runner_scope:
  formal_runtime_backend:
  thread_creation_allowed:
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
      named_thread_reason:
  required_roles:
  disabled_roles:
  required_real_agents:
  agent_instance_status:
  agent_status_refs:
  agent_output_refs:
  role_file_plan:
    <role_key>:
      input_refs:
      files_reviewed_expected:
      output_ref:
      not_checked_allowed: false
      uncovered_scope_policy:
  persistent_threads:
    required:
    thread_ids:
    missing:
    reused:
  named_threads:
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
      required_threads_created:
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
    report_interval_minutes:
    agent_activity_stream:
    handoff_on_pause:
    visible_report_fields:
      - role
      - agent_instance_id
      - current_action
      - evidence_ref
      - next_action
  tool_support:
    real_multi_agent_available:
    fallback_mode:
    checked_by:
  serial:
  parallel:
  writer_roles:
  reviewer_roles:
  runner_required:
  gpu_lock_required:
  transition_permissions:
    proposers:
    checkers:
    applier: Coordinator
  memory_policy:
    session_context_allowed:
    codex_memory_allowed:
    repo_state_required:
    memory_used:
    memory_sources:
    persistent_thread_ids:
    agent_profile_files:
    agent_memory_files:
    verified_against_current_repo:

hard_gates:
  gzsl_hard_rules:
  agent_runtime:
  interface_contract:
  innovation_code_review:
  source_status:
  artifact_boundary:
  metric_semantics:
  evidence_level:
  confirmation_grade:
  promotion_gate:

expected_outputs:
  github:
  research:
  warehouse:
  transitions:
  sync_check:

stop_if: copy the mandatory blocker checklist from section 5; never leave this field empty. 新实验缺少 TEMPLATE.yaml 或 EXPERIMENT.yaml，或者母版仍是 legacy_frozen 时必须阻塞。
```

## 3. 必填判断

`router.task_type` 只能从 Router 支持的任务类型中选择：

```text
paper intake / idea discovery
autonomous research campaign
mixed experiment campaign
local heuristic idea
tune
ablation
confirmation
debug / smoke
innovation / module trial
promotion
set-current-version
activate-version
progress dashboard
```

`enters_idea_tree` 使用总判断规则：

```text
实验是为了调/查/验证已有正式 baseline -> experiments/vX，不进 idea_tree。
实验是为了调/查/确认旧 module trial 内部模块 -> 回到所属 FRAMEWORK-VX 的四类账本，用 legacy_ref 指旧证据。
实验是为了证明一个新方法值得存在 -> idea_tree + 所属正式框架 innovation 账本；候选无 Tag，接纳后才注册新的同级正式框架。
```

`router.coupled_update` 必须写清 GitHub、Research、Warehouse 是否需要联动：

- 读论文、提取 idea、新机制设计：通常 `required: true`，先 Research，后 GitHub 轻量索引。
- 真实实验运行：通常 `required: true`，先 Warehouse raw artifact，后 GitHub 账本。
- 普通 tune / ablation / confirmation：如果只改变结果账本，不改变 idea 结论，可写 `required: false`，
  但必须在 `skip_reason` 说明为什么不更新 Research。
- trial 结论、version score、promotion 或 next_action 改变：必须同步 GitHub idea index 和
  Research decision/history。

`expected_outputs.sync_check` 必须回答：

```text
GitHub 轻量记录能否找到 Research 长版材料？
GitHub 结果记录能否找到 Warehouse artifact？
人类版记录和机器版记录是否一致？
哪些同步被跳过，原因是什么？
```

`agents.activation_mode` 只能选择：

```text
role_only
real_multi_agent
```

`agents.agent_instance_mode` 只能选择：

```text
role_only
named_owner_thread
persistent_thread
```

正式 `real_multi_agent` 默认使用 workflow-scoped `named_owner_thread`。`persistent_thread` 是跨 workflow 活上下文，用于 owner 明确要求可见长期追踪、跨天 campaign coordinator/monitor，或某角色需要跨多个 workflow 复用连续上下文时。

`agents.lifecycle` 必须选择或描述：

```text
role_only
workflow_scoped
campaign_scoped
cross_workflow
```

`workflow_scoped` 表示 agent 在本轮 workflow 全程存在；`campaign_scoped` 表示它在一个长周期 campaign 阶段内存在；`cross_workflow` 才要求 persistent thread 或等价长期可见线程。

`role_only_with_independent_sequential_review` 不是第三种 `activation_mode`。它只能写在：

```yaml
agents:
  activation_mode: role_only
  agent_instance_mode: role_only
  tool_support:
    real_multi_agent_available: false
    fallback_mode: role_only_with_independent_sequential_review
```

该 fallback 只能说明当前环境无法启动真实 sub-agent 后的顺序独立复核状态；不能用于
promotion、正式 best 结论、正式 Runner 或 owner 已明确要求真实多 agents 的任务。若
owner 明确接受 debug/smoke 降级，必须同时写 `formal_evidence: false`。

必须选择 `real_multi_agent` 的情况：

- owner 明确要求多 agents、独立 review 或多方验证；
- 启动真实 Runner，或单一 Runner 按 frozen config 串行训练且结果会进入正式 evidence；
- 任务修改模型结构、forward、loss、eval、数据流、label mapping、seen/unseen split、class order 或 logits shape；
- 新 module trial 的实现、接口检查、promotion 前复核；
- 结果异常、指标争议较大，或 owner 明确质疑当前解释；
- 准备写 `promotion_decision: promote`、创建新 `vX` 或打 version tag；
- 任务需要同时阅读论文、源码、日志和质量证据，且这些输入可以被不同角色独立检查。

允许选择 `role_only` 的情况：

- 只读解释、状态检查、配置查看；
- 不改代码、不改实验语义的窄范围 rerun / confirmation 准备；
- 结果只作为 debug/smoke；
- 只做账本格式整理且不改变实验结论。

如果选择 `role_only`，启动卡必须写明为什么不启用真实多 agents，以及哪些角色由主 agent 代执行。

真实 `real_multi_agent` 的启动卡必须列出分文件复核计划：每个角色负责哪些文件、输出到哪个 `agent_output_refs` 文件、哪些范围未覆盖。缺少 `files_reviewed`、独立输出或未覆盖范围说明时，不能把本轮记为完整多 agents 复核。

`agents.decision_basis.fastest_valid_path` 必须说明本次为什么选择最快合规路径：

- 简单只读、debug/smoke、训练前候选 triage、账本格式整理等任务，可以选择 `role_only`；单 Runner frozen config 如果会进入正式 evidence，仍默认 `real_multi_agent`。
- 如果 hard gate 或 owner 要求 `real_multi_agent`，默认并行执行只读审查角色，只串行 Implementer、Runner 和 Coordinator 写账本。
- 被跳过的角色必须写入 `skipped_agents`，并说明跳过后为什么仍然满足 hard gates。

`agents.required_real_agents` 是真实 sub-agent 硬需求角色列表：

- `activation_mode: real_multi_agent` 时，填写必须独立执行的角色列表；
- `activation_mode: role_only` 时，填写 `[]`；
- 如果按规则应使用真实多 agents 但工具不可用，填写 `[]`，并在 `tool_support.fallback_mode` 写
  `role_only_with_independent_sequential_review`，同时触发正式阻断；只有 owner 改成
  debug/smoke 时，才允许继续非正式排障。

`agents.persistent_threads` 必须记录跨 workflow 线程状态：

- `required: true`：owner 明确要求跨 workflow 可见线程，或 campaign 设计要求某角色跨多轮连续跟踪时填写；
- `thread_ids`：按角色记录当前使用的 thread id 或可见 label；
- `missing`：记录缺失的长期角色 thread；
- `reused`：说明本轮是否复用已有长期线程。

`agents.required_roles` 必须写角色名，不写“按需”。常用角色集合：

| 任务 | 必需角色 |
|---|---|
| 只读状态 / 配置检查 | Coordinator，必要时 Reader/Planner |
| 调参建议 | Coordinator、Reader/Planner、Result Analyst |
| 调参真实运行 | Coordinator、Runner、Log Analyst、Result Analyst、Quality Checker |
| confirmation / rerun | Coordinator、Runner、Log Analyst、Result Analyst、Quality Checker |
| ablation | Coordinator、Runner、Log Analyst、Interface Checker、Result Analyst、Quality Checker |
| innovation / module trial | Coordinator、Reader/Planner、Implementer、Interface Checker、Runner、Log Analyst、Result Analyst、Quality Checker、Reviewer |
| promotion | Coordinator、Quality Checker、Reviewer、Result Analyst，必要时 Interface Checker |
| debug / smoke | Coordinator、Runner、Log Analyst，必要时 Interface Checker |

`real_multi_agent` 下，Reader/Planner、Log Analyst、Quality Checker、Result Analyst、Reviewer 默认可以并行。
Runner 永远串行并锁 GPU。Implementer 是同一代码路径的唯一 writer。Coordinator 是最终 GitHub 账本唯一写入者。

`agents.memory_policy` 必须写清：

- session context 只能作为任务上下文，不能直接当证据；
- Codex 全局 memory 或历史会话摘要只能用于定位，必须回到当前仓库、日志或 artifact 验证；
- 长期 agent 记忆必须来自 `docs/workflow/agents/shared_roles/<role>/memory.md`，并记录实际读取文件；
- workflow-scoped agent 活上下文必须记录输出位置；persistent thread 如启用，必须记录 `persistent_thread_ids`；线程内容只能辅助定位，不能替代 repo/log/artifact 证据；
- repo state 和 artifact 是正式实验事实源；
- 使用 memory 时，必须记录 `memory_sources` 和 `verified_against_current_repo`。

## 4. 各任务补充字段

### Paper Intake / Idea Discovery

必须记录：

- paper id 或 source id；
- `_inbox` 输入文件；
- `PAPERS_INDEX.md` 当前状态和目标状态；
- Research 写入位置；
- 论文是否包含官方 GitHub / code URL；
- 若包含，`official_code_url`、`official_code_path`、clone commit、是否排除了数据/权重；
- 是否只进 inbox；
- 是否已经 source review；
- 何时允许升级成正式 `IDEA-xxxx`。
- 是否同步 GitHub `idea_tree/sources/`、`idea_tree/inbox.md` 或正式 `IDEA.md`。

### Tune

必须记录：

- base version；
- 目标正式框架和 `TUNE-xxx` 实验号；
- 调哪个参数；
- old value / new value；
- 预期成本；
- 是否已经试过；
- 为什么不改变模型结构、forward、loss 语义或 eval 语义。

如果来源是旧 Trial/Attempt，仍写入所属正式框架 `experiments/vX/tune/`，并用 `legacy_ref` 回指旧证据。

### Ablation

必须记录：

- 目标正式框架和 `ABLATION-xxx` 实验号；
- disabled module / disabled factor；
- switch key；
- baseline-off path；
- interface_check 是否阻塞；
- 一次只消融的主因素。

如果消融来源是旧 Trial，只能解释该框架中的对应因素，并用 `legacy_ref` 回指旧证据；如果改变
实现假设、forward 路径、新 loss 或评估语义，改走所属正式框架的 `INNOVATION-xxx`。

### Confirmation

必须记录：

- 目标正式框架、`CONFIRM-xxx` 实验号和要确认的来源运行；
- 要确认的 baseline tag；
- config；
- seed；
- 数据 split、class order、label mapping；
- 预期对齐的旧结果；
- 证据等级目标：`debug_smoke`、`quick_local`、`valid_single_run`、`confirmation_grade` 或 `baseline_grade`；
- `best_observed_H` 和 `confirmed_H` 的当前状态；
- confirmation target、tolerance 和失败时的降级规则；
- `repeat_type: exact_repeat`、`original_seed`、`max_attempts: 5`、`max_attempts_hard_cap: true`、`early_stop_on_best_hit: true`、
  `restore_target_H`、`near_miss_tolerance_H`、`near_miss_not_restored`，并确认不改 seed、不改任何参数；
- `max_attempts_hard_cap` 表示同一候选无论是否还原成功最多 5 次，5 次未达 `restore_target_H` 时收口为 not restored / near miss；
- `near_miss_not_restored` 只能说明实验有效果、还有希望；不能写成还原，不能触发 early stop；
- 若是 `seed_sweep`、`score_search` 或 `multi_seed_stability`，必须写
  `not_confirmation_evidence: true`，不得登记为复现；
- 将被锁定的 `run_commit`；
- 这次 confirmation 是从哪个 `pre-run freeze commit` 启动。

如果要确认旧 `best_attempt_id`，在所属正式框架 `confirmation/` 建正式实验，用 `legacy_ref` 指向旧记录。

### Debug / Smoke

必须记录：

- debug 目标；
- 是否会产生长期证据；
- 如果要引用结果，转入哪个正式实验目录；
- debug 结果默认不能作为有效实验结论。

### Innovation / Module Trial

必须记录：

- 正式 `IDEA-xxxx`；
- `source_type`、`source_ref`、`source_status`；
- `version_scores.<base_version>`；
- source idea file；
- module insertion point；
- input/output contract；
- shape invariants；
- baseline-off switch；
- trial branch 和 trial tag 计划；
- 正式实验的 `PARAMETER_MATRIX.csv` 和四类 `INDEX.md` 计划行是否已经冻结到 `pre-run freeze commit`；旧 Attempt 只在兼容修复时检查；
- 本次真实 run 将使用的 `run_commit`。
- 是否触发 `innovation_code_review_protocol.md`；
- `idea_intent_check.md`、`interface_precheck.md`、`review_round_1.md`、
  `review_round_2.md` 的计划位置；
- 命名线程 是否允许，哪些角色必须由真实独立 agents 执行；
- Review 0-3 的阻断条件和当前状态。

### Promotion

必须记录：

- 来源正式框架 / 来源 Tag；
- trial code tag；
- baseline H、trial H、delta H；
- U/S/ZS、seed、best epoch；
- 完整 manifest/result/quality/interface evidence；
- `evidence_level: baseline_grade`；
- `confirmation_status: confirmed`；
- `best_observed_H` 和 `confirmed_H` 已区分；
- owner override 是否只是激活主线代码，且是否需要标成 `owner_activated_unconfirmed`；
- target version；
- 是否只是生成版本账本，还是 owner 明确要求 activate-version。

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
- 正式 evidence、best、promotion 或 owner 要求多 agents，但缺少各角色 `files_reviewed` / `input_refs` / `agent_output_refs` / 独立输出文件；
- 使用 `named_owner_thread` 却没有写 lifecycle、独立输出位置和本轮结束后的 agent_summary / memory / issues 写回规则；
- 工具不可用但任务硬门要求 `real_multi_agent`，却仍试图启动正式 Runner；debug/smoke 只能在 owner 改目标后另走非正式路径；
- 正式 Runner 启动卡没有 `formal_runner_allowed: true`、`formal_evidence_allowed: true` 和通过的 `multi_agent_preflight`；
- `agents.activation_mode` 写成了 `role_only_with_independent_sequential_review`；
- 正式 Runner 启动卡没有 `owner_monitor.enabled: true`、`agent_activity_stream`、
  `report_channel` 或 `handoff_on_pause`；
- 使用了 memory-derived fact，却没有说明 memory 来源和当前仓库 / artifact 验证方式；
- 这是一个真实训练 / confirmation / tune / trial run，但工作区不是 clean；
- 运行前新增了实验 config、`PARAMETER_MATRIX.csv`、四类 `INDEX.md`、启动卡或其他预跑账本，但还没有先提交成 `pre-run freeze commit`；
- 预期运行 commit 不明确，或无法把本次 run 唯一映射到一个冻结后的 `run_commit`；
- module trial 没有正式 idea；
- idea 来源是 `unknown` 或 `unverified` 却要开 trial；
- idea / 创新 / module trial 将改代码，但没有写明
  `innovation_code_review_protocol.md` 的 Review 0-3 计划；
- 创新代码改动没有使用 `real_multi_agent`，或没有把 Reader/Planner、Interface Checker、
  Quality Checker、Reviewer 等必须独立复核角色写入 `required_real_agents`；
- Review 0-3 任一轮存在 blocking issue，却要启动 Runner、选择 best 或 promotion；
- label mapping、seen/unseen split、class order、logits shape 或 metric semantics 不清楚；
- 没有填写 `evidence_level`，或把 `quick_local` / `valid_single_run` 结果写成 confirmed baseline；
- `best_observed_H` 和 `confirmed_H` 混写，导致无法判断复现失败影响哪个结论；
- 启动卡涉及状态、复现、结果比较、promotion 或 tag，但没有先检查 `baseline_repro_status`；
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
  use codex_app.create_thread for runner_monitor and evidence_quality_checker,
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
分角色文件阅读/输出计划：
owner_monitor.enabled：
owner_monitor.report_channel：
owner_monitor.agent_activity_stream：
evidence_routing.subject_id：
evidence_routing.current_state：
transition_permissions：
硬门：
当前阻塞：
是否需要再次确认及原因：dangerous_action | mode_ambiguous | gate_blocked | none
pre-run freeze commit：
run_commit：
post-run result commit：
sync_check：
```

这段输出就是后续 agent 的共同入口。

---

## docs/workflow/core/AGENT_RUNTIME_HARD_GATE.md

# Agent Runtime Hard Gate

> 当前状态：历史兼容，可选，不再是 `SYS-WORKFLOW-V6` 的默认开跑门。普通实验和论文实验不需要为了正式性创建命名线程或 `agent_runtime.yaml`。只有 owner 明确要求多智能体实时监控，或当前任务确有多人并行协作风险时才启用本文件；其余情况使用“唯一提交 + 参数表 + 一次开跑检查 + 独立 RUN 目录”的短流程。

本文件是 GTPJ workflow-v2 的正式 Runner 启动闸机。它解决一个具体问题：正式实验不能由 Coordinator 单窗口代办所有角色，也不能再依赖旧 UI 临时 agent 面板。

## 1. 核心规则

只要一次任务会启动真实 Runner、登记正式 attempt/result、选择 best、安排 repeat、影响下一轮高成本实验或进入 promotion 判断，就必须先通过 agent runtime hard gate。

```text
没有左侧命名 Codex 线程 -> 不准启动正式 Runner。
没有独立线程输出 -> 不准 apply advance transition。
没有 pre-run allow/check -> 不准冻结并启动服务器 batch。
没有 owner 可见监控流 -> 不准声称 workflow 全程接管。
```

旧 `temporary_subagent` / `spawn_agent` / UI 临时 agent 只允许作为非正式诊断历史，不允许作为新的 formal evidence gate。状态机只记录证据迁移，不能替代 agents。Runner 只执行训练，也不能替代 workflow。

## 2. 必需启动顺序

正式实验必须按这个顺序执行：

```text
1. Coordinator 生成 task start card。
2. Coordinator 确认 owner 允许创建左侧命名 Codex 线程。
3. Coordinator 为必需角色创建命名线程，标题使用 <subject_id> | <Role Label>。
4. Planner / Interface / Quality / Runner Monitor 等角色在线程内独立输出 allow/block/propose。
5. Coordinator 写 agent_runtime.yaml。
6. 运行 validate-agent-runtime 和 multi-agent-preflight，通过后才允许 pre-run freeze。
7. Coordinator apply evidence transition。
8. Runner 生成 frozen batch 并启动服务器。
9. Coordinator 进入 owner-visible monitor loop，按间隔汇报线程活动、batch 状态、证据位置和下一步。
10. Log / Quality / Result 线程分别审查运行证据。
11. Coordinator 写 result、quality、agent_summary 和下一条 transition。
12. Coordinator 归档已完成且结论已入账的命名线程；左侧栏只保留当前仍 active 的工作线程。
```

如果第 3 步没有发生，本轮必须阻断正式 Runner。只有 owner 明确把目标改成非正式 `debug_smoke` 排障时，才允许另走 debug 路径；该路径不能作为正式 evidence、candidate keep、best、confirmation、promotion 或 version 判断依据。

## 3. Runtime Gate 文件

每个正式 Runner start 前必须有一个轻量文件：

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
agent_instance_mode: named_owner_thread
lifecycle: workflow_scoped
ui_visibility: left_sidebar_named_threads
tool_support_real_multi_agent_available: true
thread_management_tool: codex_app.create_thread
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
thread_archive_policy: archive_completed_threads_on_stage_end
archive_completed_threads_on_stage_end: true
archived_threads_record: AGENT_ACTIVITY.md

named_thread_ids:
  runner_monitor: 019...
  interface_checker: 019...
  evidence_quality_checker: 019...

named_thread_titles:
  runner_monitor: "ATTEMPT-007 | Runner Monitor"
  interface_checker: "ATTEMPT-007 | Interface Checker"
  evidence_quality_checker: "ATTEMPT-007 | Evidence Quality Checker"

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
  required_threads_created: true
  agent_instance_ids_present: true
  agent_status_refs_valid: true
  independent_outputs_present: true
  agent_output_refs_valid: true
  pre_run_allow_checks_passed: true
  agent_runtime_validated: true
  threads_archivable: true

authority_refs:
  task_start_card: task_start_card.md
  agent_summary: agent_summary.md
  quality_check: quality_check.md
  transitions: TRANSITIONS.jsonl
  agent_activity: AGENT_ACTIVITY.md
```

`named_thread_ids` 不能写成 `named_owner_thread`、`temporary_subagent`、`not_recorded`、`role_only`、`current Codex session` 这类占位文本。必须记录真实可见 thread id。

`named_thread_titles` 必须记录左侧栏实际线程标题。标题使用严格格式：

```text
<subject_id> | <Role Label>
```

禁止使用与任务无关的随机英文昵称，例如 `Herschel`、`Galileo`、`Feynman`、`Bohr`。标题必须同时说明“属于哪个任务”和“承担哪个角色”；否则 `validate-agent-runtime` 必须阻断正式 Runner。

## 3.1 分文件复核契约

正式 `real_multi_agent` 不能只记录“有多个 agent”。每个必需角色的输出文件必须包含：

```yaml
role:
agent_instance_id:
files_reviewed:
decision: allow | block | propose
uncovered_scope:
```

`files_reviewed` 必须列出该角色实际阅读的文件或 artifact。入口规则修改至少要分成三组独立复核：owner 入口文档、runtime/orchestration hard gate、helper 测试与本地 skill 镜像。Coordinator 可以整合结论，但不能把一个 agent 的阅读结果复制给其他角色，也不能用单一上下文冒充分文件复核。

## 4. allow / block 语义

Runner start 之前，所有 pre-run 必需角色必须是 `allow` 或 `pass`。任一 `block`、`not_checked` 或缺失，都必须阻断正式 run。

最低必需角色族：

```text
Runner Monitor
Evidence Quality Checker / Quality Checker
Interface Checker（涉及代码、配置、GZSL、评估语义或新模块时必需）
```

Log Analyst 和 Result Analyst 可以在 run 后进入，但如果它们的结论影响 best、repeat、promotion 或下一轮实验，也必须是独立线程输出。

## 5. formal runner 判定

正式 Runner 同时要求：

```text
formal_evidence: true
activation_mode: real_multi_agent
agent_instance_mode: named_owner_thread
workflow_mode_pairing: live_multi_agent_monitor
ui_visibility: left_sidebar_named_threads
tool_support_real_multi_agent_available: true
single_agent_execution: false
runner_start_allowed: true
formal_runner_allowed: true
formal_evidence_allowed: true
multi_agent_preflight 全部为 true
validate-agent-runtime 通过
```

其中 `multi_agent_preflight` 是启动前的机器可读汇总，不替代角色输出。它必须由 `named_thread_ids`、`named_thread_titles`、`agent_instance_status`、`agent_status_refs`、`agent_output_refs`、`pre_run_required_checks`、`agent_summary.md`、`quality_check.md`、`AGENT_ACTIVITY.md` 等文件支撑。

如果 owner 明确禁止创建线程，但仍要把 detached 服务器训练计入正式 evidence，则允许第二条 formal gate：

```text
formal_evidence: true
activation_mode: role_only
agent_instance_mode: role_only
formal_runtime_backend: server_detached_role_only
workflow_mode_pairing: server_frozen_runner
ui_visibility: current_owner_thread_only
thread_creation_allowed: false
formal_runner_allowed: true
formal_evidence_allowed: true
sequential_role_preflight 全部为 true
validate-agent-runtime 通过
```

这条路径不是 debug/smoke。它要求独立 sequential role outputs、detached server status file、stop 机制和恢复 handoff。

## Live Monitor Gate

`workflow_mode: live_multi_agent_monitor` 必须同时满足：

```text
agent_instance_mode: named_owner_thread
ui_visibility: left_sidebar_named_threads
owner_visible_reporting: true
current_stage_status: running | closeout_complete
report_new_completions: true
monitor_command: monitor-workflow --report-new-completions
active_named_threads_visible_until_closeout: true
archive_after_closeout_only: true
```

Runner 运行期每个新增 completed job 必须通过 `monitor-workflow --report-new-completions` 或等价证据写入 `AGENT_ACTIVITY.md`。如果只能启动服务器 detached runner、不能保持左侧命名线程和逐 job 监控，则必须改走 `server_frozen_runner`，不能把它标成 live multi-agent。

## 6. 降级规则

如果 owner 不允许创建命名线程，或者当前任务只是 debug/smoke，必须写：

```yaml
formal_evidence: false
activation_mode: role_only
agent_instance_mode: role_only
runner_scope: debug_smoke
evidence_level: debug_smoke
formal_runner_allowed: false
formal_evidence_allowed: false
```

debug/smoke 可以帮助排障，但不得升级成正式 attempt 证据。要升级，必须重新走 formal gate：`named_owner_thread` 或 `server_detached_role_only`。

## 7. 收尾归档

阶段结束前运行只读计划：

```bash
python workflow/gtpj_workflow.py agent-cleanup-plan --path <agent_runtime.yaml>
```

`agent-cleanup-plan` 只读列出 keep / archive / unknown；真正归档由 Coordinator 使用线程归档能力完成，并把结果写入 `archived_threads_record`。

---

## docs/workflow/core/WORKFLOW_VERSION.md

# Workflow Version

```yaml
current_workflow_version: SKILL-GTPJ-WORKFLOW-V2.2
previous_workflow_version: SKILL-GTPJ-WORKFLOW-V2.1
workflow_v2_status: evidence_state_machine_plus_agent_runtime_gate_plus_hardened_parameter_matrix
model_version_scope: separate_from_v1_v2_v3_v4_v5
```

## Version Meaning

```text
model vX:
  method/framework/baseline state.

workflow-vX:
  experiment governance, agent orchestration, evidence routing, and helper checks.
```

`workflow-v2` does not mean model `v6`. It adds the evidence routing kernel on top of the already usable slim workflow.

## workflow-v2 Kernel

```text
tamper-evident append-only evidence state machine
```

Minimum executable layer:

```text
schemas/evidence_routing.schema.yaml
TRANSITIONS.jsonl
evidence_routing.yaml
validate-evidence-routing
```

Runtime gate layer:

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
left_sidebar_named_threads
thread_archive_policy: archive_completed_threads_on_stage_end
archive_completed_threads_on_stage_end
```

The evidence state machine records state changes. The agent runtime gate decides whether
a formal Runner is allowed to start and whether the owner-visible right sidebar stays
limited to the current active roles.

## SKILL-GTPJ-WORKFLOW-V2.1：参数矩阵规则

这次升级改的是工作流规则，不是模型版本。新实验必须先有一张逐任务的
`PARAMETER_MATRIX.csv`，再提交冻结并生成正式批次；`PARAMETER_MATRIX.md`
是同一张表的阅读版。相同完整配置必须标明是复跑，避免以后不知不觉重复调参。

唯一正式说明在：`docs/workflow/protocols/parameter_matrix_protocol.md`。

## SKILL-GTPJ-WORKFLOW-V2.2：正式证据加固

V2.2 不改变模型结构，只把逐任务参数表、唯一启动收据、Warehouse 只写一次、动态排名复核、
历史身份永久保留和三轮审核一致性变成可执行检查。


---

# 归档四：docs/workflow/playbooks/（V6 替换前）

以下九张活动执行卡是 `source_commit` 中的原文快照；只用于历史回查。

---

## tune.md

# 执行卡：调参 Tune

正式入口固定为 `experiments/vX/tune/INDEX.md`，人看编号为 `VX-TUNE-xxx`。必须先由
`EXPERIMENT.yaml` 绑定 `TEMPLATE.yaml` 登记的准确母版 commit，再开 `exp/vX/tune/...` 分支；一个调参问题只有一张参数矩阵，每个参数组合
是一行 `RUN-xxx`。纯调参永远留在当前框架，不注册正式框架，也不创建 Tag。

用于参数、seed、epoch、batch、loss weight 或不改变方法语义的窄配置搜索。

## 必读

```text
START_HERE.md
WORKFLOW_KERNEL.md
docs/workflow/reference/GZSL_HARD_RULES.md
docs/workflow/core/AGENT_RUNTIME_HARD_GATE.md
docs/workflow/protocols/experiment_protocol.md
产生 raw artifact 时读 docs/workflow/protocols/ARTIFACT_REGISTRATION.md
```

如果调参发生在 module trial 内部，还要读：

```text
docs/workflow/protocols/module_trial_protocol.md
```

## 角色

正式 tune 默认使用 `real_multi_agent`：

```text
总控 (Coordinator)
调参规划 (Tune Planner)
运行监控 (Runner Monitor)
日志分析 (Log Analyst)
证据质量检查 (Evidence Quality Checker)
结果比较 (Result Comparator)
```

正式 Runner 启动前必须写 `agent_runtime.yaml`，记录左侧命名 Codex 线程的真实
`agent_instance_id`，并通过 `validate-agent-runtime` 和 `multi-agent-preflight`。
否则正式 tune 必须阻断。只有 owner 明确把目标改成非正式 `debug_smoke` 排障时，
才允许继续；该结果不能进入 keep / best / confirmation / promotion。

## 输出

版本级 tune：

```text
experiments/vX/tune/
```

trial 内部 tune：

新调参一律放在所属框架的 `experiments/vX/tune/TUNE-xxx/`，并登记到同目录的 `INDEX.md`。旧 Trial/Attempt 只用于回查；如果调参来自旧记录，把旧编号写进 `legacy_ref`，不要再创建新的 Attempt。

raw logs 和 checkpoints 留在 Warehouse。

## 决策规则

只调参数带来的提升不能开新的 `vX`。

重要 tuned config 必须经过 `repeat_type: exact_repeat` 后，才能作为正式数据表述：
锁定 `original_seed` 和原始配置，`max_attempts: 5`、`max_attempts_hard_cap: true`、`early_stop_on_best_hit: true`，
并声明 `restore_target_H`、`near_miss_tolerance_H` 和 `near_miss_not_restored`。接近但未达到目标
只能说明有效果、还有希望，不能说还原；同一候选无论是否还原成功都最多 5 次，5 次未还原不能继续加跑复现。换 seed 的 `seed_sweep` / `multi_seed_stability`
必须写 `not_confirmation_evidence: true`，只能作为搜索或稳定性诊断。

tune transition 默认只能进入：

```text
single_run_valid
tune_promising
rerun_required
rejected
stopped_no_gain
```

## 参数矩阵（2026-08-04 起）

每个具体调参任务都必须写入同一批次的 `PARAMETER_MATRIX.csv`，并自动生成给人阅读的 `PARAMETER_MATRIX.md`。一行是一个参数组合，不是一行概括整个 50/100 任务批次。开跑前必须写清相对基线的改动、随机种子、配置指纹和是否复跑；同一指纹已经出现时，必须明确 `repeat_of`，否则不得重复运行。详见 `docs/workflow/protocols/parameter_matrix_protocol.md`。

---

## ablation.md

# 执行卡：消融 Ablation

正式入口固定为 `experiments/vX/ablation/INDEX.md`，人看编号为 `VX-ABLATION-xxx`。
必须先由 `EXPERIMENT.yaml` 绑定 `TEMPLATE.yaml` 登记的准确母版 commit，再开 `exp/vX/ablation/...` 分支；每个对照是一行 `RUN-xxx`。
消融只回答模块贡献，不注册正式框架，也不创建 Tag。

用于移除、替换、关闭或隔离既有组件。普通消融不新增方法模块；如果需要新增或改写
module、forward、loss、eval、data view 或接口语义，必须改走 innovation / module trial。

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

如果消融发生在 module trial 内部，还要读：

```text
docs/workflow/protocols/module_trial_protocol.md
```

## 角色

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

只有需要添加关闭开关、旁路或空路径时才加入 `实现者 (Implementer)`。如果实现者要新增或改写
方法模块，本任务必须停止并重新路由为 innovation / module trial。

正式 Runner 启动前必须写 `agent_runtime.yaml` 并通过 `validate-agent-runtime` 和
`multi-agent-preflight`。
Interface / Quality / Runner Monitor 没有独立 allow/pass 时，不得把消融结果作为正式证据。

## 阻断门

- label mapping、seen/unseen split、class order、logits shape 或 metric semantics 不清楚。
- 消融暗中改变了目标组件之外的东西。
- 消融需要新增或改写模块代码、forward、loss、eval、data view 或接口语义；这种情况不是普通消融。
- 要和 unconfirmed baseline 比较，却没有标出这个边界。

ablation 只有在组件贡献证据成立时才能进入 `ablation_supported`；如果消融不支持贡献，必须记录
`stopped_ablation_not_supported` 或 `rejected` transition。

## 参数矩阵（2026-08-04 起）

消融也必须逐任务登记到 `PARAMETER_MATRIX.csv`：每行写清关掉或替换了哪个因素、对照是什么、随机种子、配置指纹、结果和最终判断。批次摘要不能替代逐行表。重复运行相同消融时必须标明 `repeat_of`，完整规则见 `docs/workflow/protocols/parameter_matrix_protocol.md`。

---

## confirmation.md

# 执行卡：复现 / 确认 Confirmation

用于复现或确认一个结果。

## 当前短流程

确认实验与调参、消融使用同一套五步流程，不再额外搭一套发布系统：

1. 在 `EXPERIMENT.yaml` 写清要复现的准确 code commit、config、seed、data/split 和评估口径。
2. 在一张 `PARAMETER_MATRIX.csv` 中预先列完全部 repeat。
3. 做一次 clean/data/GPU/输出目录检查后，直接从同一提交运行。
4. 每个 repeat 写入独立 `RUN-xxx` 目录，保留完整日志、U/S/H/ZS、best epoch 和需要的最佳模型。
5. 全部跑完后统一报告逐次值与 mean/min/max/range；失败也保留，不悄悄追加次数。

默认不用专用控制器、Git bundle、多层收据、永久 claim、固定三波调度、三路审核或第二次冻结。改了模型/训练/数据/评估时做 1 次独立审核；只重复现有提交时做开跑检查即可。下面旧角色和 agent runtime 内容仅用于回查历史 confirmation。

正式入口固定为 `experiments/vX/confirmation/INDEX.md`，人看编号为 `VX-CONFIRM-xxx`。
每次 exact repeat 都是同一参数矩阵中的一行 `RUN-xxx`。确认实验本身不注册正式框架；
只有它确认的是创新且 promotion 被接纳时，才由该创新生成新的框架节点。

## 必读

```text
START_HERE.md
WORKFLOW_KERNEL.md
docs/workflow/reference/GZSL_HARD_RULES.md
docs/workflow/protocols/experiment_protocol.md
docs/workflow/protocols/quality_gate.md
产生 raw artifact 时读 docs/workflow/protocols/ARTIFACT_REGISTRATION.md
```

## 角色

正式默认角色：

```text
总控 (Coordinator)
运行监控 (Runner Monitor)
日志分析 (Log Analyst)
证据质量检查 (Evidence Quality Checker)
结果比较 (Result Comparator)
```

正式 confirmation / rerun 启动 Runner 前，必须写 `agent_runtime.yaml`，记录真实
左侧命名 Codex 线程，并通过 `validate-agent-runtime` 和 `multi-agent-preflight`。否则
confirmation 必须阻断；不能用单窗口 sequential review 生成 confirmed evidence。

## 复现 / Repeat 类型

必须先声明本轮是哪一种：

```text
exact_repeat:
  固定原始 code commit、config、original_seed、data/cache、epoch schedule、batch size 和评估口径。
  不允许换 seed，不允许换任何参数。
  max_attempts: 5
  max_attempts_hard_cap: true
  early_stop_on_best_hit: true
  restore_target_H: 原始结果水平，必须达到才算还原。
  near_miss_tolerance_H: 默认 0.2；只用于记录接近但未还原。
  near_miss_not_restored: 接近只能说明实验有效果、还有希望。
  用来回答“原始结果能不能原样再跑出来”。
  只有 exact_repeat 才能叫严格复现。

same_seed_repeat:
  同一个 original_seed 重跑，最多 5 次，命中即停。
  用来检查非确定性、环境漂移和同配置可重复性。

seed_sweep / score_search:
  主配置固定，但 seed 变化。
  用来冲分、找 seed 敏感性或观察稳定性；必须写 not_confirmation_evidence: true，不能叫严格复现，也不能单独作为 confirmed evidence。

multi_seed_stability:
  预先声明多个 seed，报告 mean/min/max/range。
  可作为稳定性证据，但必须和 exact_repeat 区分，并写 not_confirmation_evidence: true。
```

seed 是实验配置的一部分。改变 seed 就不是“同配置严格复现”，只能是
`seed_sweep`、`score_search` 或 `multi_seed_stability`。

默认 confirmation 必须写明 repeat 类型。正式复现默认 `repeat_type: exact_repeat`、
`max_attempts: 5`、`max_attempts_hard_cap: true`、`early_stop_on_best_hit: true`。一旦任一 clean run 达到 `restore_target_H`，
立刻停止后续 pending repeat；无论是否还原成功，同一候选最多 5 次，5 次未达到则收口为 not restored。落入 `near_miss_tolerance_H` 但未达到 `restore_target_H` 时，
只能写 `near_miss_not_restored`：说明实验有效果、还有希望，不能说还原，不能停止。

如果复现有单次命中：

```text
best_hit = true
best_single_H = best repeat H
best_observed_H = best repeat H
结论 = 命中候选 / 继续复现
```

如果稳定确认也通过：

```text
stable_confirm = true
confirmed_H = repeat mean 或协议指定的 confirmed metric
official single = best repeat
reported stability = mean / min / max
promotion_compare_metric = repeat mean / confirmed_H
```

不能隐藏较弱 repeat。稳定性属于正式证据的一部分。
不得只凭 best repeat 做 promotion 或 baseline claim。
不得把 multi-seed 的最高值写成 exact-repeat confirmed。
也不得用 mean H 掩盖单次最高命中；回答“有没有复现到”时优先报告 best single，
回答“能不能 promotion / baseline claim”时再报告 mean/min/max/range。

## 输出

版本级 confirmation：

```text
experiments/vX/confirmation/
```

trial 内部 confirmation：

新确认实验一律放在所属框架的 `experiments/vX/confirmation/CONFIRM-xxx/`，并登记到同目录的 `INDEX.md`。旧 Trial/Attempt 只用于回查；旧编号写进 `legacy_ref`，不要再创建新的 Attempt。

---

## innovation.md

# 执行卡：创新 / Module Trial

当 owner 要求开新模块、测试新机制或把 idea 落成代码时使用。

正式的人类入口是所属正式框架的 `innovation/INDEX.md`，编号为 `VX-INNOVATION-xxx`。旧
`IDEA / TRIAL / ATTEMPT` 可以继续承载历史实现和证据，但必须映射回这个创新实验项。
创新确认并接纳后，才注册同级 `FRAMEWORK-VY` 并创建 Tag；新正式框架拥有自己的四类实验，不在创新目录里
再套一整套四类实验。

## 必读

```text
START_HERE.md
WORKFLOW_KERNEL.md
docs/workflow/reference/GZSL_HARD_RULES.md
docs/workflow/reference/innovation_decomposition_protocol.md
docs/workflow/protocols/module_template_selection.md
docs/workflow/protocols/idea_tree_protocol.md
docs/workflow/protocols/module_trial_protocol.md
docs/workflow/protocols/code_interface_contract.md
docs/workflow/protocols/innovation_code_review_protocol.md
docs/workflow/protocols/agent_orchestration.md
docs/workflow/protocols/agent_report_policy.md
docs/workflow/core/AGENT_RUNTIME_HARD_GATE.md
```

## 角色

正式创新工作必须使用 `real_multi_agent`。

默认角色：

```text
总控 (Coordinator)
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

正式 Runner 启动前必须先创建或绑定左侧命名 Codex 线程，写 `agent_runtime.yaml`，并通过
`validate-agent-runtime` 和 `multi-agent-preflight`。如果只是 Coordinator 单窗口代办
Review 0-3，本轮不能作为正式 `real_multi_agent` 创新证据。

## 探索 / 正式分界

探索性 trial 只允许做这些事：

```text
idea triage
接口草图
debug_smoke
本地 shape / script / speed probe
```

探索性输出必须写：

```yaml
formal_evidence: false
evidence_level: debug_smoke
formal_runner_allowed: false
formal_evidence_allowed: false
eligible_for_keep_best_promotion_confirmation: false
```

正式 module trial 才能登记 attempt/result、选择 best、影响下一轮高成本实验或进入
promotion。正式路径必须通过真实 `real_multi_agent` gate；不能把探索性结果事后补签成
正式证据。

探索性结果如果看起来有价值，升级路径只能是重新跑正式证据：

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
    - exact repeat confirmation when used for confirmed_H or promotion:
      `repeat_type: exact_repeat`, `original_seed`, `max_attempts: 5`,
      `max_attempts_hard_cap: true`,
      `early_stop_on_best_hit: true`, `restore_target_H`, `near_miss_tolerance_H`,
      `near_miss_not_restored`; each candidate has at most 5 exact repeats regardless of success or failure; seed_sweep /
      multi_seed_stability must be `not_confirmation_evidence: true`
  forbidden:
    - promote exploration run in place
    - rewrite debug_smoke as valid_single_run
    - use sequential review as formal audit
```

## 创新拆解

创新必须按下面层级管理：

```text
Paper
-> Claim / Mechanism
-> Hypothesis
-> Interpretation
-> Attachment Point
-> Trial
-> Attempt
```

`Hypothesis` 是科学假设；`Trial` 是该假设在某个接入点和实现契约下的一次工程绑定；
`Attempt` 才是同一 Trial 内的参数、seed、epoch、权重或 top-k 尝试。

同一个 Hypothesis 加到不同位置，通常新开 Trial；只调参数才留在 Attempt。

## 模板选择

新 module trial 必须先按 `docs/workflow/protocols/module_template_selection.md` 选模板。

```text
feature_adapter
fusion_gate
auxiliary_loss
sampler_or_data_view
composite
```

选择原则：先确定论文/idea 的 mechanism claim，再找 attachment point，最后选最窄模板。
如果两个子模块可以独立验证，拆成多个 Trial；只有机制不可拆时才用 `composite`。
如果 owner 没有明确 `base_version` / `base_code_tag`，只能做 idea discovery，不能开正式 trial。

每个新模块必须写 trial-local `module_source.md`，说明模块来源、论文机制、GTPJ 适配方式、
模板族、接入点、baseline-off 解释和之后写论文可用的表述。
每个正式 Trial 还必须写 `trial_meta.yaml` 并通过 `validate-trial-meta`，用于硬判定
`single_module`、`composite` 或 `architecture_change`。
如果 owner 明确说“用新模板”或“不继承老模板”，`trial_meta.yaml` 必须设置
`training_entry.mode: strict_template_entry`，Runner 只能使用 trial-local
`training_entry.py`。旧入口中本次需要打开的模块必须迁移到新入口，不能继续把分支堆到
`train_GTPJ_CUB.py`。

## 代码流程图

只要创新会改变代码逻辑、forward、loss、evaluation、输入输出或关键张量流向，Trial
`README.md` 必须有 `## Code Flow Diagram`：

```text
input tensors -> changed modules / gates / branches -> logits / loss / metrics
```

这张图是 owner 读代码路径的入口，不替代 `framework_diagram.md`。完整变量 glossary、
method glossary、loss flow、baseline-off 和 code-vs-intent 仍写入 trial 级
`framework_diagram.md`。

## 复核循环

保留 Review 0-3：

```text
Review 0: 编码前检查 idea 和接口
Review 1: 检查实现边界
Review 2: 检查 runtime 和 evidence readiness
Review 3: 检查结果和 promotion 边界
```

## 输出

```text
idea_tree/
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
- 没有真实左侧命名 Codex 线程、没有 `agent_runtime.yaml` 或 `validate-agent-runtime` 未通过。
- 正式 multi-agent 支持不可用。owner 只能把本轮改成 debug-only 排障；不能继续正式 trial。

---

## promotion.md

# 执行卡：升版 Promotion

当某个结果可能成为新 baseline/version 时使用。

## 必读

```text
START_HERE.md
WORKFLOW_KERNEL.md
docs/workflow/protocols/promotion.md
docs/workflow/protocols/quality_gate.md
docs/workflow/protocols/versioning.md
docs/workflow/protocols/git_policy.md
```

## 角色

promotion 必须做正式独立检查：

```text
总控 (Coordinator)
证据质量检查 (Evidence Quality Checker)
接口检查 (Interface Checker)
结果比较 (Result Comparator)
复核者 (Reviewer)
```

promotion、baseline-grade、新版本、tag 和争议结果复核必须使用真实 `real_multi_agent`。
如果不能证明各角色有独立 agent 实例、独立输入和独立输出，promotion 必须阻断；
不能用 sequential review 或单窗口自查替代。

## 必要证据

```text
promotion_decision: promote
完整 manifest/result/quality/interface evidence
必要时有 repeat 或 confirmation evidence
已声明目标版本
没有未解决硬门
```

## 边界

只调参数不能创建新的 `vX`。

promotion 可以在协议要求时创建本地文件、commit 和 tag。

除非 owner 明确要求，否则不能 push。

---

## mixed_campaign.md

# 执行卡：混合实验 Campaign

用于 `跑10创新+100调参` 这类任意组合实验命令。

先用 helper 自动路由，不要手工拆任务：

```bash
python workflow/gtpj_workflow.py start --phrase "跑2创新+8调参"
```

## 必读

```text
START_HERE.md
WORKFLOW_KERNEL.md
docs/workflow/core/WORKFLOW_ROUTER.md
docs/workflow/protocols/mixed_experiment_campaign_protocol.md
docs/workflow/core/AGENT_RUNTIME_HARD_GATE.md
每个 requested workstream 对应的 playbook
```

## 结构

```text
campaign
  -> workstream: innovation / tune / ablation / confirmation / debug
    -> task
      -> run
```

不要给每个 run 创建一个永久 agent。

但 campaign / workstream / task 级正式角色必须是真实左侧命名 Codex 线程，并在
`agent_runtime.yaml` 中记录实例 id。没有通过 `validate-agent-runtime` 和
`multi-agent-preflight` 的 campaign 不能启动正式 Runner；不能用 sequential review
替代正式 campaign evidence。

生成 campaign manifest、batch 或 runner plan 前，先运行只读规划门：

```bash
python workflow/gtpj_workflow.py plan-experiments --phrase "<owner 组合口令>"
```

规划必须根据当前 repo、baseline、正式待跑 ledger 和已完成 result/quality 自动生成
Evidence Summary、Candidate Decision、Current Run Plan 三张表；`.gtpj_runtime` 只能作
debug context。

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

`RESULT_INDEX.md` 只能做派生索引，不能自建正式 H/U/S/ZS。

Campaign 目录不能成为单独的正式结果分支。每个 work item 必须回写到所属 subject：
全部正式 work item 写入目标框架的 `experiments/vX/<type>/`。旧 Trial/Attempt 只作为
`legacy_ref`；真正新创新写入所属正式框架的 innovation 账本，并由 campaign 只保存链接和调度索引。

`WORK_ITEMS.md` 必须把 owner-facing 编号和 runner job 编号拆开：

```text
INNOVATION-001 -> RUN-001 -> 兼容 runner job DR-001
TUNE-001 -> RUN-001 -> 兼容 runner job DR-003
```

不要直接用 `DR-003` 解释成第三个 tune，也不要把 runner-local `attempt_id`
解释成 GitHub 正式 `ATTEMPT-003`。

`campaign_run_map.md` 必须说明本 campaign 的调度和归属：哪些 work item、哪些 runner job、
正式写回哪个 subject、哪些只是 derived summary。不要把它叫作新方法
`framework_diagram.md`；新创新 / 新 Trial 自己必须有 trial-level framework diagram。

## 角色

campaign 级默认角色：

```text
工作流总控 (Workflow Coordinator)
Campaign 规划 (Campaign Planner)
运行监控 (Runner Monitor)
结果比较 (Result Comparator)
证据质量检查 (Evidence Quality Checker)
Warehouse 登记 (Warehouse Registrar)
```

再按对应 playbook 加入 workstream 专属角色。

## 调度规则

总控 (Coordinator) 负责优先级和边界。

运行监控 (Runner Monitor) 负责 GPU/服务器执行和失败隔离。

结果比较 (Result Comparator) 根据 evidence 决定哪些方向需要 exact-repeat confirmation：
`repeat_type: exact_repeat`、`original_seed`、`max_attempts: 5`、
`max_attempts_hard_cap: true`、`early_stop_on_best_hit: true`、`restore_target_H`、`near_miss_tolerance_H`、
`near_miss_not_restored`。接近但未达到目标只能说明有效果、还有希望，不能说还原；同一候选无论是否还原成功都最多 5 次，5 次未还原不能继续加跑复现。换 seed 的
`seed_sweep` / `multi_seed_stability` 必须写 `not_confirmation_evidence: true`。

调度按 evidence state machine，不按 run 数硬排：

```text
hypothesis_ready -> interface_precheck_passed -> smoke_passed -> single_run_valid -> tune_promising -> ablation_supported -> exact_repeat_best_hit -> stable_confirmed
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
checkpoint retention 结果
work item id -> runner job id 映射
campaign run map 路径
formal subject result/quality 路径
```

---

## autonomous_campaign.md

# 执行卡：全自动研究 Campaign

用于长期目标：用户只给论文来源、评估标准、安全边界和实验标准，工作流接管剩余过程。

## 必读

```text
START_HERE.md
WORKFLOW_KERNEL.md
docs/workflow/core/WORKFLOW_ROUTER.md
docs/workflow/protocols/autonomous_research_campaign.md
如果请求包含多种实验类型，再读 docs/workflow/protocols/mixed_experiment_campaign_protocol.md
```

## 用户输入

```text
论文/来源范围
评估指标和 baseline
安全边界
实验预算和停止条件
升版标准
最终交付标准
```

## 工作流负责

```text
论文读取
来源复核
idea 发现和排序
实验规划
代码修改
服务器运行
证据登记
repeat/confirmation
promotion proposal
最终结果和代码报告
```

## Agent 形态

使用 campaign-scoped real multi-agent。只有在可见长周期总控/监控连续性确实有用时，才额外加 `persistent_thread`。

正式证据仍然以文件为准。

如果真实 multi-agent 工具不可用，campaign 只能停在 paper intake、idea extraction、
config 草案和 debug/smoke 排障层；不能启动正式 Runner、登记正式结果、promotion proposal
或 baseline claim。

## 最终交付

```text
最终实验表
最佳已确认框架和参数
失败方向及原因
代码/config diff 摘要
Warehouse artifact 索引
升版建议
剩余风险
```

---

## paper_intake.md

# 执行卡：论文读取 / Idea Discovery

当 owner 要求读论文、处理来源、提取创新点时使用。

## 必读

```text
START_HERE.md
WORKFLOW_KERNEL.md
docs/workflow/protocols/paper_intake.md
docs/workflow/protocols/idea_tree_protocol.md
```

## 角色

默认角色：`阅读/规划 (Reader/Planner)`、`来源复核 (Source Reviewer)`、`总控 (Coordinator)`。

如果输出会影响正式 idea 选择、module trial、baseline 表述或论文实验规划，使用
`real_multi_agent`。如果真实 multi-agent 工具不可用，只能输出待复核来源笔记或 idea 草案，
不能直接进入正式 trial / promotion 证据。

## 输出

长证据写入 `GTPJ_Research`。

轻量 GitHub 记录写入：

```text
idea_tree/sources/
idea_tree/inbox.md
idea_tree/ideas/<IDEA-ID>/
idea_tree/idea_tree.json
idea_tree/versions/<vX>.md
```

## 阻断门

- 没有 verified source 或 owner 接受的 local heuristic。
- 缺少 hypothesis、implementation scope 或 risk。
- idea 没有关联 active version view。
- owner 只要求阅读，没有授权实验执行。

---

## paper_to_experiment.md

# 执行卡：论文到实验闭环

当 owner 要求“从论文开始”“论文到实验闭环”“读论文并验证创新”时使用。

这张卡只是把已有链路接起来：paper intake 负责来源和创新提取；idea_tree 负责选择和排队；
module trial / experiment 负责正式验证；结果必须再反馈回 Research 和 idea_tree。

## 必读

```text
START_HERE.md
WORKFLOW_KERNEL.md
docs/workflow/playbooks/paper_intake.md
docs/workflow/playbooks/innovation.md
docs/workflow/protocols/paper_intake.md
docs/workflow/protocols/idea_tree_protocol.md
docs/workflow/protocols/module_template_selection.md
docs/workflow/protocols/module_trial_protocol.md
```

正式 Runner 前再读：

```text
docs/workflow/core/AGENT_RUNTIME_HARD_GATE.md
docs/workflow/protocols/agent_cleanup_protocol.md
```

## 最小闭环

```text
paper_inbox
-> source_review
-> idea_candidate
-> formal_IDEA
-> selected_queue
-> trial_preflight
-> runner_evidence
-> idea_feedback
```

## 阶段

1. 论文读取：扫描 `GTPJ_Research/papers/_inbox/` 和 `PAPERS_INDEX.md`，更新
   `paper_meta.yaml`、`reading_notes.md`、`source_review.md`、`code_review.md`、
   `extracted_ideas.md`。
2. 来源复核：记录 `source_status`、`source_ref`、官方代码链接、本地代码路径和 clone commit。
3. 候选创新：粗想法只进 `idea_tree/inbox.md`；成熟机制才创建或更新
   `idea_tree/ideas/IDEA-xxxx_slug/IDEA.md` 和 `idea_tree/idea_tree.json`。
4. 正式 IDEA 门：必须有 owner 指定的 `base_version`、`base_code_tag`、`hypothesis`、
   `implementation_scope`、`risk`、
   `version_scores.<base_version>`、空 blockers，以及可检查的接口影响。
5. 选择队列：只有 owner 或当前计划明确选中后，才写入
   `idea_tree/queues/01_selected_next.md` 或当前版本 view。
6. 模板选择：按 `module_template_selection.md` 选择最窄模板，写 `module_source.md`，
   并确认标准 GZSL 数据集、split、label mapping、class order、U/S/H/ZS 语义不变。
   如果 owner 指定“用新模板”，必须设置 `training_entry.mode: strict_template_entry`，
   复制标准训练模板为 trial-local `training_entry.py`，并迁移旧入口中需要打开的模块。
7. Trial 预检：按 `innovation.md` 和 `module_trial_protocol.md` 创建 trial 前检查
   base version、base code tag、分支、接口契约、Review 0 和 artifact 边界。
8. 正式实验：必须生成或读取 `agent_runtime.yaml`，记录真实 `agent_instance_id`
   与 UI 显示名/role 映射，依次通过 `validate-agent-runtime`、`multi-agent-preflight`
   和 `agent-cleanup-plan`，并明确 owner-visible monitor loop。
9. 结果反馈：`record-module-attempt`、`sync-trial-summary`、`closeout-check` 后，更新
   Research 的 `decision_history.md` 或 `experiment_plan.md`，并回写 idea_tree 的
   status、version score、risk、linked_trials、evidence 和必要的版本适配说明。具体下一步动作
   只能写入 selected queue、trial/attempt、task card 或 result/quality 文件，不写入全局 idea 总表。

## 写入边界

```text
Research: 长阅读、长推理、源码复核、失败原因、决策历史
GitHub: paper/source 轻量索引、正式 IDEA、版本评分、trial 结果索引
Warehouse: 正式 runner 的日志、checkpoint、receipt 和大 artifact
```

Paper intake 本身不启动训练，也不直接创建 module trial。
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
- 正式实验前缺少真实左侧命名 Codex 线程、`agent_runtime.yaml`、preflight 或 cleanup plan。
- 阶段结束时没有汇报 keep / archive / unknown agents，或 completed threads 未归档并记录 `archive_result`。

## 启动口径

Owner 只说“从论文开始”时，默认先做只读 intake 和候选排序：

```text
能不能开工：能做论文读取和候选提取；不能直接训练。
任务类型：paper -> idea -> module trial closed loop。
当前最小动作：读取 PAPERS_INDEX/_inbox，列出候选来源和缺口。
正式实验条件：selected IDEA + owner approval + agent_runtime + preflight + cleanup plan。
```
