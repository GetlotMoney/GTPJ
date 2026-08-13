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
run_start_receipt_sha256 可选兼容收据的固定哈希；V6 直接训练时留空
run_command_sha256      使用兼容收据入口时记录的训练命令哈希；V6 直接训练时可留空
run_log_sha256          训练日志哈希
run_exit_code           使用兼容收据入口时记录的退出码；V6 直接训练时可留空
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
5. 做一次 clean worktree、数据/划分身份、GPU 可见和输出目录不存在检查。
6. 用现有训练入口直接运行，把完整输出保存到独立 `RUN-xxx/training.log`；不得覆盖历史目录。
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

冻结提交完成后，使用现有训练入口直接运行。默认环境是 `dvsr_gpu`，每个任务使用独立输出目录并保存完整日志：

```powershell
conda run -n dvsr_gpu python <现有训练入口.py> --config <实际训练配置> <其他参数>
```

训练完成后，用 `record-result` 回填对应行。必须提供 `--pre-run-freeze-commit <commit>`，helper 会再次核对冻结提交中的参数表、配置快照、配置指纹、seed 和调参值，解析日志中的完整 U/S/H/ZS，并保存日志哈希与轻量证据索引。无收据日志必须包含训练入口实际打印的唯一代码 commit、配置 SHA-256 和随机种子，且与冻结运行完全一致；U/S/H/ZS 必须位于 0..100，H 必须与 U/S 的调和平均一致。`--run-start-receipt` 不是 V6 默认门槛；传入时继续严格核验旧收据、结束标记、命令和日志封口，供历史运行或真实高风险任务兼容使用。

同一张参数表的所有改写动作共用同一把锁。冻结配置、刷新阅读版和登记结果都会在锁内重新读取当前表，再一起写回 CSV 与 Markdown，避免两个进程各自拿旧表覆盖对方。正式账本中的代码提交固定写训练前的冻结提交，不会被训练后推进的当前 `HEAD` 偷换。

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
再使用该实验目录自己的 `PARAMETER_MATRIX.csv`、`freeze-parameter-matrix` 和现有训练入口直接运行。
旧 planner 只允许 `--debug-smoke`，产物不能进入正式证据。

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
