# 实验协议

本文件只规定 standalone / version-level 的普通实验。也就是：为了调、查、确认某个正式
baseline 版本 `vX`，而不是为了筛选某个 module trial 内部 attempt。

版本级 tune、ablation 和 confirmation 都属于某个正式 baseline 版本 `vX`。它们保存证据，
不自动产生新版本。

纯调参只改变 config 或训练超参，不改变模型/训练代码语义、forward 结构、模块连接、loss
形式、logits shape 或 eval 语义，因此不能开新的 `vY`。即使 exact repeat 复现通过，也只能成为该
`vX` 下面的 confirmed config / confirmed tune record。

只有存在框架/代码语义变化，且满足 `docs/workflow/protocols/promotion.md` 的自动 promotion gate，
才会生成新的正式 `vY`。

模块 trial 内部也可以、也应该做参数尝试、窄消融和 clean confirmation。那类运行写在：

```text
experiments/module_trials/IDEA-xxxx_*/TRIAL-xxx_*/ATTEMPTS.md
experiments/module_trials/IDEA-xxxx_*/TRIAL-xxx_*/attempts/ATTEMPT-xxx/
```

并遵守 `docs/workflow/protocols/module_trial_protocol.md`。不要因为 trial 内部有 `param_tune` 或
`ablation` 字样，就把它误放到 `experiments/vX/tune/` 或 `experiments/vX/ablation/`。

示例：

```text
experiments/v1/tune/TUNE-001_topo008/
experiments/v1/ablation/ABL-001_disable_jepa/
experiments/v1/confirmation/CONFIRM-001_v1_seed5/
```

每个普通实验目录必须包含：

```text
README.md
config.yaml
manifest.yaml
result.yaml
result.md
quality_check.md
agent_summary.md
```

普通实验目录不得新增 raw logs、checkpoint、feature cache 或 generated figures。
这些资产必须写入外部 `GTPJ_Warehouse`，GitHub 只通过 `manifest.yaml` 和
`result.yaml` 保存 artifact identity、URI、hash 和结果摘要。

实验结束后执行 checkpoint retention：完成日志解析、指标确认、hash/size 和
manifest/result 登记后，每个普通实验最多保留 3 个模型 checkpoint。默认保留按主指标
GZSL-H 排名最高的 3 个；其余 `.pth`、`.pt`、`.ckpt`、`.safetensors` 权重文件必须从运行目录
或 Warehouse checkpoint 目录清理。不得删除日志、配置、manifest、result、quality_check、
runner receipt 或 registry。需要超过 3 个时，必须在 `quality_check.md` 写明例外理由。

如果实验改代码，必须额外包含：

```text
implementation.md
code.diff
interface_check.md
```

每次真实实验都必须留下 agent 工作凭证。默认保存 `agent_summary.md`，记录参与角色、
检查范围、发现、结论和证据引用。不要把完整聊天流水写入 GitHub；长报告放 Warehouse，
GitHub 只记录 artifact id。具体规则见 `docs/workflow/protocols/agent_report_policy.md`。

## 共同记录字段

每个普通实验 README 至少记录：

```text
experiment_id:
kind:
version:
base_code_tag:
branch_source: main | tag vX
code_branch:
run_commit:
dirty_state:
command:
seed:
config:
python_env:
torch_cuda:
dataset_split:
cache_fingerprint:
log_artifact_id:
log_uri:
log_sha256:
log_size_bytes:
manifest: manifest.yaml
result_yaml: result.yaml
result_md: result.md
agent_summary: agent_summary.md
attempt_id:
failure_stage:
U:
S:
H:
ZS:
best_epoch:
decision: keep | reject | rejected | rerun | needs_confirmation | blocked
promotion_decision: not_applicable | promote | blocked | rejected
promote_to:
evidence_level: debug_smoke | quick_local | valid_single_run | confirmation_grade | baseline_grade
result_status: debug | valid_observation | needs_confirmation | confirmed | blocked | rejected
best_observed_H:
confirmed_H:
max_attempts_hard_cap:
restore_target_H:
near_miss_tolerance_H:
near_miss_not_restored:
confirmation_status: not_applicable | pending | confirmed | failed
```

## 参数矩阵（2026-08-04 起）

上述字段记录“一次实验”的总结果；从本规则生效后，还必须用 `PARAMETER_MATRIX.csv` 逐行记录该实验内的每个真实任务。CSV 是唯一机器来源，`PARAMETER_MATRIX.md` 由它生成，给人直接阅读。每一行必须有基线版本、基线配置哈希、改动参数、配置指纹、种子、复跑来源、结果和决定。正式运行前，矩阵必须没有草稿行、任务数量必须与冻结计划一致，并且同一配置指纹若再次出现必须写 `repeat_of`。完整规则见 `docs/workflow/protocols/parameter_matrix_protocol.md`。

## 证据等级和做数规则

实验结果不是只有“做数/不做数”两种状态。以后所有结果必须先标证据等级，再决定能不能用于
baseline、论文结论或下一步调参。

```text
debug_smoke          只用于环境/流程排障；formal_evidence=false，不能进入 keep/best/promotion/confirmation。
quick_local          只用于本地快速复线或趋势观察；不能用于 promotion 或正式 baseline。
valid_single_run     config、log、checkpoint、manifest、result、quality 完整；可记录 best_observed_H。
confirmation_grade   从 clean pre-run freeze commit 启动，clean exact repeat 达到 restore_target_H；可确认某个结果。
baseline_grade       confirmation_grade 通过，或按质量门要求完成多 run 稳定性证据；可写成稳定 baseline。
```

硬规则：

- 单次最高结果只能写为 `best_observed_H`，不能直接写成 `confirmed_H`。
- 正式复现必须写 `repeat_type: exact_repeat`、`original_seed`、`max_attempts: 5`、
  `max_attempts_hard_cap: true`、`early_stop_on_best_hit: true`、`restore_target_H`、`near_miss_tolerance_H` 和
  `near_miss_not_restored`；原始 config、seed、代码 commit、
  data/cache、epoch schedule、batch size 和评估口径都不能改。
- 只有任一 clean exact repeat 达到 `restore_target_H` 时，才记录 `best_hit: true`、
  `best_single_H`、`best_observed_H`，并停止后续 pending repeat。
- 同一候选不管有没有还原成功都最多 5 次；5 次仍未达到 `restore_target_H` 时，必须收口为 not restored / near miss，不能继续加跑复现。
- 落入 `near_miss_tolerance_H` 但未达到 `restore_target_H` 时，只能记录
  `near_miss_not_restored`，表示实验有效果、还有希望；不能写成复现通过，不能停止后续 repeat。
- 只有另行要求 `stable_confirm` 时，才把同一 `original_seed`、同一配置的多次 clean repeat
  计算为 `H_mean` / `H_min` / `H_max` / range；`seed_sweep`、`score_search` 和
  `multi_seed_stability` 必须写 `not_confirmation_evidence: true`，不能写成 exact-repeat confirmed。
- 任意结果比较、`delta_H` 解释、promotion 或 tag 决策前，先运行或等价执行
  `python workflow/gtpj_workflow.py repro-status --version <vX>`。如果对照版本只有
  `best_observed_H` 且 `confirmed_H=pending`，它只能写成未确认参考，不能写成 confirmed baseline。
- `git_dirty: true`、`dirty_state: dirty`、`run_commit` 缺失或运行前未冻结时，结果最多是
  `quick_local` 或普通 debug 证据，不能进入 `confirmation_grade` 或 `baseline_grade`。
- clean confirmation 失败不会删除原始实验记录；它会把该结果维持在 `valid_single_run` 或
  `needs_confirmation`，并阻断 promotion。
- 如果同一 frozen config、同一 seed 的 clean confirmation 出现一过一不过，必须标记
  `mixed_confirmation`，先做 reproducibility diagnosis，不能继续 tune、promotion 或 tag。
  诊断 run 优先显式记录 `strict_determinism`、`use_dedicated_batch_rng`、`batch_sampling_seed`
  和 training log 中的 torch/cuda/cuDNN 状态。
- owner 可以显式把某个版本激活为当前主线代码，但如果缺 clean confirmation，状态必须写成
  `owner_activated_unconfirmed` 或 `provisional`，不能写成 `confirmed baseline`。
- 后续比较必须同时区分 `best_observed_H` 和 `confirmed_H`；没有 confirmed 值时写
  `confirmed_H: pending` 或留空，并说明 confirmation 状态。

## 运行前冻结与运行后记账

对 tune、ablation、confirmation 这三类会产出正式证据的真实 run，统一执行两阶段规则。

### 第一阶段：`pre-run freeze commit`

启动 Runner 前，先把本次 run 依赖的仓库内输入冻结成一次独立提交。至少包括：

- 本次 run 的 `config.yaml` 或 attempt 级配置副本；
- 运行计划所需的人类可读索引，例如 tune 表计划行、启动卡、trial 内 `ATTEMPTS.md` 计划行；
- 必要的轻量预跑元数据，例如 `base_code_tag`、目标 seed、预计命令。

硬规则：

- `pre-run freeze commit` 完成后，必须满足 `git status --short` 为空；
- Runner 只能从这个 clean worktree 启动；
- 本次 run 的 `run_commit` 必须等于这个冻结后的 commit；
- 这次提交不允许提前写入本次 run 的 `manifest.yaml`、`result.yaml`、`result.md`、`quality_check.md`、指标结论或 artifact 注册。

### 第二阶段：`post-run result commit`

训练完成并取得日志后，再单独写入：

- `manifest.yaml`
- `result.yaml`
- `result.md`
- `quality_check.md`
- `agent_summary.md`
- 各类索引和 artifact 注册

硬规则：

- `post-run result commit` 只能记录已经完成的 run 结果；
- 不要在结果记账提交里再改会影响该 run 语义的配置、开关或参数；
- 如果 run 启动前工作树不干净，或 `run_commit` 不明确，这次结果最多记为 debug 证据，不能直接记为正式 keep / best / confirmation evidence。
- post-run 记账前必须执行 checkpoint retention：模型 checkpoint 最多保留 3 个，或在
  `quality_check.md` 记录超过 3 个的明确理由。

## Promotion 字段映射

普通实验使用上面的轻量字段记录证据。进入 `docs/workflow/protocols/promotion.md` 时，Coordinator 按下面规则读取：

```text
base_version     = version
parent_version   = version
parent_tag       = base_code_tag
code_commit      = run_commit
run_config       = config
run_command      = command
run_log_artifact = log_artifact_id
run_log_uri      = log_uri
run_log_sha256   = log_sha256
```

如果普通实验显式写了 `base_version`，它必须和 `version` 一致。GitHub 不保存 raw log；
长期证据是 `manifest.yaml` 中的 artifact identity，以及 `result.yaml` 中的
`evidence.log_artifact_id`。

失败运行也是证据，必须记录：

- `failure_stage`: setup / data / forward / backward / eval / logging / unknown；
- 错误摘要；
- stderr 或 log 路径；
- 是否需要 retry；
- 本次失败是否改变下一步实验计划。

## 调参实验

调参实验是在某个正式版本 `vX` 上只改变参数，不改变模型结构。

允许范围：

- learning rate、batch size、epoch、scheduler；
- loss weight、temperature、dropout；
- seed、训练轮数、config 中已有开关或数值；
- 不改变 forward 结构、模块连接、loss 形式、logits shape 或 eval 语义。

调参不生成新 `vY`。调参结果如果复现通过，可以成为当前 `vX` 下的 confirmed config
或 confirmed reference，但不得创建新的正式框架版本。若调参过程中引入了模型/训练代码语义变化，
必须改走 innovation / module trial 规则，而不是继续记为纯 tune。

### 当前版本调参

当前 `main` 就是目标 `vX` 代码时：

```text
从当前 main 开 exp/vX-tune-XXX-xxx 分支
base_code_tag: vX
branch_source: main
先写 config 和计划行，提交 pre-run freeze commit
确认 git status --short 为空，并记录 run_commit
跑实验
回 main 或当前实验分支写结果账本，形成 post-run result commit
更新 experiments/vX/tune/
```

### 历史版本调参

`vX` 已经存在，但当前 `main` 不是 `vX` 代码时：

```text
从 vX tag 开 exp/vX-tune-XXX-xxx 临时运行分支
只用于跑 vX 代码
保存 config、command、log_artifact_id、log_uri、log_sha256、result.yaml 和 result.md
回到当前 main
只把实验证据写入 experiments/vX/tune/
确认入账后删除本地临时运行分支
如果推过远端，也删除远端临时运行分支
```

历史版本调参的长期资产是 `main` 里的 `experiments/vX/tune/` 账本，不是运行分支。

### 调参表

每个正式版本单独维护调参表：

```text
experiments/v1/tune/INDEX.md
experiments/v2/tune/INDEX.md
experiments/v3/tune/INDEX.md
```

不维护全局大调参表。

版本级 `tune`、`ablation` 和 `confirmation` 的待跑入口都使用各自 `INDEX.md`。正式计划一旦被 owner 接受，必须先在对应表格写入一行，至少包含：

```text
experiment_id / type / status / directory / run_id 或计划说明 / formal_evidence / note
```

这种正式待跑统一标记为 `formal_pending`。`Status` 为 `planned`、`pending`、`pre_run`、`pre_run_gated` 或 `ready_to_run` 的正式行，表示该版本仍有待跑实验。`.gtpj_runtime/` 中的 batch 目录不能单独创建待跑事实；如果 runtime 目录没有对应 `INDEX.md` 行，统一视为 `orphan_runtime_plan`。debug/smoke 只能写 `formal_evidence: false`，不得混入正式待跑清单。

建议列：

```text
| Tune ID | Status | Run ID | Formal | 参数 | 原值 | 新值 | Seed | U | S | H | ZS | 结果 | 决策 | 目录 |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|---|
```

调参前必须先生成建议清单，但不能自动执行。建议清单最多 3 个候选，每个候选说明：

- 参数；
- 当前值；
- 建议值；
- 为什么调；
- 风险；
- 预计成本；
- 是否已经试过。

用户明确选择后，才开分支、跑代码、记账。

调参多 agent 编排：

```text
Coordinator -> Reader -> 用户选择 -> Runner -> Log Analyst + Quality Checker + Result Analyst -> Coordinator
```

同一时间只允许一个 Runner 占用 GPU。

## 消融实验

消融实验用于回答：既有模块、loss、分支、特征或约束是否真的有贡献。

普通消融不创建新方法框架。它只能关闭、旁路或替换既有因素为空路径；如果需要新增或改写
module、forward、loss、eval、data view 或接口语义，那已经是 innovation / module trial，
不能继续记为普通 ablation。

允许的消融代码形式：

- 关闭一个模块；
- 绕过一个 loss；
- 去掉一个 fusion 分支；
- 替换为 identity、zero、detach 或固定 baseline path；
- 增加 config 开关，使既有目标模块不生效。

硬规则：

- 一次只消融一个主要因素；
- 必须对照目标 baseline；
- 必须记录 `disabled_module` 或 `disabled_factor`；
- 必须记录 `switch_key` 或代码旁路位置；
- 必须保留 `code.diff`；
- 必须写 `implementation.md`；
- 必须写 `interface_check.md`；
- 必须确认没有顺手改到其他结构。
- 不要求新增 `framework_diagram.md`；如果本次改动需要新增或改写模块框架，必须转为 innovation / module trial，并补齐 `module_source.md`、`framework_diagram.md` 和 `Code Flow Diagram`。

接口检查必须覆盖：

- 输入维度；
- 输出维度；
- logits shape；
- loss 输入；
- labels 和 class order；
- mask / attention shape；
- config 开关路径；
- baseline-off path 是否真能回到目标 baseline 行为。

当前版本消融：

```text
从当前 main 开 exp/vX-ablation-XXX-xxx
跑完后更新 experiments/vX/ablation/
```

历史版本消融：

```text
从 vX tag 开 exp/vX-ablation-XXX-xxx 临时运行分支
只用于跑 vX 代码和消融代码
回当前 main 写 experiments/vX/ablation/
确认入账后删除临时运行分支
```

如果消融发现“去掉某模块更好”，也不能直接变成新版本。必须记录证据，然后通过
`docs/workflow/protocols/promotion.md` 自动 promotion gate，把干净代码重新整理成正式 baseline。
如果整理过程需要改写方法框架或模块代码，先开 innovation / module trial 记录框架来源和代码流。

消融多 agent 编排：

```text
Coordinator
Reader
Implementer
Interface Checker
Runner
Log Analyst
Quality Checker
Result Analyst
```

训练仍然一次只跑一个。

## 重新复现

confirmation 实验用于确认某个正式 baseline 的结果仍然可信。

目标：

- 固定 `base_code_tag`；
- 固定 config；
- 固定 seed；
- 固定数据 split 和 cache 口径；
- 记录完整命令、日志、U/S/H/ZS 和 best epoch；
- 从 clean worktree 启动，并把冻结后的 `run_commit` 写清楚。

confirmation 分支：

```text
exp/vX-confirm-XXX-xxx
```

历史版本 confirmation 可以从 `vX` tag 开临时运行分支；跑完后回当前 `main`
写 `experiments/vX/confirmation/`，确认入账后删除临时运行分支。

confirmation 不允许从 dirty worktree 直接启动。若需要先补 config 副本、启动卡或索引条目，也必须先提交
`pre-run freeze commit`，再从 clean 状态发起确认运行。

confirmation 多 agent 编排：

```text
Coordinator -> Runner -> Log Analyst + Quality Checker + Result Analyst -> Coordinator
```

confirmation 不改模型结构。若复现失败，记录失败证据和下一步建议，不直接改 baseline。
如果失败表现为 `mixed_confirmation`，Coordinator 先启动 reproducibility diagnosis：
保留模型语义不变，只增加/启用可审计的 deterministic 运行开关或采样隔离开关。
