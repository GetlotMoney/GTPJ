# 实验协议

tune、ablation 和 confirmation 都属于某个正式 baseline 版本 `vX`。它们保存证据，
不自动产生新版本；只有满足 `docs/workflow/promotion.md` 的自动 promotion gate，
才会生成新的正式 `vY`。

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
quality_check.md
logs/
```

如果实验改代码，必须额外包含：

```text
implementation.md
code.diff
interface_check.md
```

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
original_log:
copied_log:
artifact_manifest:
attempt_id:
failure_stage:
U:
S:
H:
ZS:
best_epoch:
decision: keep | reject | rerun | needs_confirmation
promotion_decision: not_applicable | promote | blocked | rejected
promote_to:
```

## Promotion 字段映射

普通实验使用上面的轻量字段记录证据。进入 `docs/workflow/promotion.md` 时，Coordinator 按下面规则读取：

```text
base_version     = version
parent_version   = version
parent_tag       = base_code_tag
code_commit      = run_commit
run_config       = config
run_command      = command
run_log          = copied_log
original_run_log = original_log
```

如果普通实验显式写了 `base_version`，它必须和 `version` 一致。`copied_log` 是长期证据路径；
`original_log` 是原始日志路径，两者都应保留。

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

调参不自动生成新版本。调参结果如果想成为新 baseline，必须先记录
`promotion_decision: promote`，再走 `docs/workflow/promotion.md`。

### 当前版本调参

当前 `main` 就是目标 `vX` 代码时：

```text
从当前 main 开 exp/vX-tune-XXX-xxx 分支
base_code_tag: vX
branch_source: main
跑实验
回 main 更新 experiments/vX/tune/
```

### 历史版本调参

`vX` 已经存在，但当前 `main` 不是 `vX` 代码时：

```text
从 vX tag 开 exp/vX-tune-XXX-xxx 临时运行分支
只用于跑 vX 代码
保存 config、command、original_log、copied_log、结果
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

建议列：

```text
| Tune ID | 参数 | 原值 | 新值 | Seed | U | S | H | ZS | 结果 | 决策 | 目录 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|---|
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
Coordinator -> Reader -> 用户选择 -> Runner -> Log Analyst + Quality Checker -> Coordinator
```

同一时间只允许一个 Runner 占用 GPU。

## 消融实验

消融实验用于回答：某个模块、loss、分支、特征或约束是否真的有贡献。

消融可以改代码，但只能是可解释的移除、关闭、旁路或替换为空路径。消融代码是临时实验代码，
不自动进入 `main`，也不自动产生新版本。

允许的消融代码形式：

- 关闭一个模块；
- 绕过一个 loss；
- 去掉一个 fusion 分支；
- 替换为 identity、zero、detach 或固定 baseline path；
- 增加 config 开关，使目标模块不生效。

硬规则：

- 一次只消融一个主要因素；
- 必须对照目标 baseline；
- 必须记录 `disabled_module` 或 `disabled_factor`；
- 必须记录 `switch_key` 或代码旁路位置；
- 必须保留 `code.diff`；
- 必须写 `implementation.md`；
- 必须写 `interface_check.md`；
- 必须确认没有顺手改到其他结构。

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
`docs/workflow/promotion.md` 自动 promotion gate，把干净代码重新整理成正式 baseline。

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
- 记录完整命令、日志、U/S/H/ZS 和 best epoch。

confirmation 分支：

```text
exp/vX-confirm-XXX-xxx
```

历史版本 confirmation 可以从 `vX` tag 开临时运行分支；跑完后回当前 `main`
写 `experiments/vX/confirmation/`，确认入账后删除临时运行分支。

confirmation 多 agent 编排：

```text
Coordinator -> Runner -> Log Analyst + Quality Checker -> Coordinator
```

confirmation 不改模型结构。若复现失败，记录失败证据和下一步建议，不直接改 baseline。
