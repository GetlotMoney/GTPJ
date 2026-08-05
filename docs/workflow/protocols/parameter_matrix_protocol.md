# 参数矩阵规范

```text
policy_status: active
policy_version: LEDGER-V1
effective_date: 2026-08-04
scope: 所有新建的 tune、ablation、confirmation 和 module trial attempt
```

## 这条规则解决什么问题

一轮 50 或 100 个任务不是“一次实验”，而是一批很多个具体参数组合。以后每一个具体任务都必须有自己的一行，避免只留下批次摘要，导致后来不知道某个参数是否已经试过。

不保存原始日志和模型到 GitHub：它们仍留在 Warehouse。本规范只保存轻量、可查、可复现的参数和结果索引。

## 固定文件

每个新实验目录或每个新的 `attempts/ATTEMPT-xxx/` 目录必须有：

```text
PARAMETER_MATRIX.csv   # 机器校验、查重和结果回填的唯一来源
PARAMETER_MATRIX.md    # 由 CSV 生成，给人直接阅读
```

CSV 一行对应一个真实任务，不是一行对应整个 50/100 任务批次。Markdown 只是同一数据的阅读版，禁止分别手工维护两份内容。

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
U/S/H/ZS、best_epoch   实际结果；未跑时为空
decision               保留、放弃、继续确认等决定
artifact_ref           Warehouse 中结果摘要的位置
```

表中只写“这次改了什么”；完整配置仍由每个任务的配置快照保存。不要把数百个没有变化的字段重复塞进表格。

## 开跑前的硬步骤

```text
1. 生成参数矩阵。
2. 逐行看清任务数、参数变化和复跑对象。
3. 查重：同一个 config_fingerprint 已经存在时，必须改参数，或明确写 repeat_of。
4. 把参数矩阵和计划一起提交为 pre-run freeze commit；训练与结果入账都引用这个提交。
5. 通过参数矩阵校验后，才能生成正式 Runner 批次。
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

即使有人绕过这一步直接运行，`record-result` 也会拒绝把结果写成正式账本。它只会把指标
回填到已冻结的对应行。模块内部 Attempt 同样由 `record-module-attempt` 执行这一检查。两个结果命令都必须显式传入 `--pre-run-freeze-commit <commit>`；helper 会确认参数行和训练配置确实存在于这个训练前提交中。

普通 module attempt 没有专用批次建表器时，先用最小入口建立一行草稿，再冻结：

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

从本规范生效后，正式动态路由批次必须传入同一个 `--attempt-id` 和 `--run-id`；一张矩阵只能绑定一个 Run。正式计划逐行核对全部冻结字段并保存不可变快照，结果回填不能覆盖既有结果。`debug_smoke` 仅用于排障，不受此硬门限制，也不能作为正式证据。

## 跑完后

动态路由把服务器的 `summary.csv` 取回后，用下面命令回填同一张表：

```powershell
python workflow\gtpj_workflow.py sync-dynamic-routing-matrix --run-dir .gtpj_runtime/batches/<RUN_ID>
```

回填后再次校验，再写 `result.yaml`、`result.md` 和质量检查。每一行的 `artifact_ref`
必须指向该任务在 Warehouse 的目录，不得只指向 `.gtpj_runtime` 运行缓存。参数列属于运行前冻结内容；
跑完后只能补状态、指标、决策和 Warehouse 引用，不能暗中改参数。
回填还必须核对逐任务 Warehouse 目录、`artifact_manifest.json`、manifest 哈希和其中的
`job_id/run_id/attempt_id`，不能只凭一个非空路径入账。

对于“按前序排名复跑”的动态任务，开跑前可暂写 `top_rank:n`；回填时 helper 必须把它解析为
真实 `DR-xxx`、实际完整配置指纹和实际参数变化。若服务器摘要没有给出这个来源任务，回填会拒绝，
不会把不完整的表当成完成。

## 版本实验与模块内部实验放在哪里

```text
版本级调参：experiments/vX/tune/TUNE-xxx/PARAMETER_MATRIX.*
版本级消融：experiments/vX/ablation/ABLATION-xxx/PARAMETER_MATRIX.*
版本级确认：experiments/vX/confirmation/CONFIRM-xxx/PARAMETER_MATRIX.*
模块内部：experiments/module_trials/.../attempts/ATTEMPT-xxx/PARAMETER_MATRIX.*
```

版本文件只说明“版本为什么变化”；参数矩阵负责完整记录“每一个候选怎么试、结果如何、为什么留下或停止”。

## 历史记录迁移

历史 Attempt 和 v3/v4 不能补造数据。迁移时只允许从 Warehouse 的 `plan.json`、`summary.csv`、每任务配置和日志登记中恢复；恢复不了的行可以标成 `legacy_summary_only`，但这种行不能开跑、不能写成 keep/best，也不能进入 promotion。旧目录确实没有矩阵时，结果迁移必须显式使用 `--legacy-summary-only` 和非提升决定；新实验不得借这个开关绕过矩阵。历史缺口不会伪装成已经完成的参数表，也不阻碍新规范从今天起执行。

跨历史矩阵复跑时，`repeat_of` 使用 `matrix:<历史 PARAMETER_MATRIX.csv 路径>#<job_id>`；同一张表内则直接写原 `job_id`。helper 会确认来源任务存在，且版本、代码引用和完整配置指纹完全相同；不同参数不能借用一个旧任务号绕过查重。
