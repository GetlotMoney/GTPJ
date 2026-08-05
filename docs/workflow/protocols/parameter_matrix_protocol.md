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

表中只写“这次改了什么”；完整配置仍由每个任务的配置快照保存。不要把数百个没有变化的字段重复塞进表格。

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
  --directory experiments/module_trials/.../attempts/ATTEMPT-xxx `
  --job-id JOB-001 --job-kind ablation --base-version v5 `
  --base-config experiments/module_trials/.../config.yaml `
  --config experiments/module_trials/.../attempts/ATTEMPT-xxx/config.yaml --seed 5
```

动态路由的标准入口是：

```powershell
python workflow\gtpj_workflow.py prepare-dynamic-routing-matrix `
  --trial-dir experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing `
  --attempt-id ATTEMPT-019 --run-id <固定RUN-ID> `
  --profile <profile> --jobs <任务数> --base-version v5

# 检查、提交 pre-run freeze commit 后：
python workflow\gtpj_workflow.py validate-parameter-matrix `
  --path experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/attempts/ATTEMPT-019/PARAMETER_MATRIX.csv `
  --expected-jobs <任务数> --require-ready
```

若基线代码标签不是版本号，在“生成矩阵”和“规划正式批次”两步都传同一个
`--base-code-tag <tag-or-commit>`，否则会因冻结对象不一致被拒绝。

从本规范生效后，正式动态路由批次必须传入同一个 `--attempt-id` 和 `--run-id`；一张矩阵只能绑定一个 Run。正式计划会逐行核对矩阵中的 `run_id` 是否等于本次计划的 Run 编号，再核对全部冻结字段并保存不可变快照；因此为 `RUN-A` 冻结的表不能拿去规划或回填 `RUN-B`。结果回填不能覆盖既有结果。`debug_smoke` 仅用于排障，不受此硬门限制，也不能作为正式证据。

## 跑完后

动态路由把服务器的 `summary.csv` 取回后，用下面命令回填同一张表：

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
