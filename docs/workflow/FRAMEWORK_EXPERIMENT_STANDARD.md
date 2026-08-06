# GTPJ 框架与实验正式规范

```yaml
standard_id: SYS-WORKFLOW-V4
ledger_id: DATA-FRAMEWORK-LEDGER-V2
status: active
effective_date: 2026-08-06
owner_approved: true
owner_approval_source: 当前任务明确要求正式框架平级并保留历史来源指针
canonical_entry: docs/workflow/FRAMEWORK_EXPERIMENT_STANDARD.md
```

## 一句话规则

所有已经确定的正式框架都在同一层，也都拥有正式版本号、长期分支和冻结 Tag。框架之间可以保留“从哪个正式框架演变而来”的历史连线，但这条线只表示来源，不表示包含、上下级或目录嵌套。

每个正式框架固定拥有调参、消融、创新、确认四类实验。创新候选暂时放在所属正式框架的创新实验下面，不拥有正式框架编号、长期框架分支或 Tag；只有确认并接纳后，候选代码才注册为一个新的同级正式框架。

本文件是今后唯一的正式结构规范。旧文档中的 `TRIAL / ATTEMPT` 继续保留用于回查历史，但不能再作为新实验入口。

## 1. 三层对象

| 层级 | 人话解释 | 正式例子 |
|---|---|---|
| 正式框架 | 已确定、已登记、拥有 Tag 的一套模型代码与方法 | `FRAMEWORK-V5`、Tag `v5` |
| 实验项 | 在某个正式框架下回答一个具体问题 | `V5-ABLATION-001` |
| 运行 | 参数表里真正执行的一行 | `RUN-003`，旧系统任务号可为 `DR-003` |

禁止把一次包含 50 个任务的批次写成 50 个互不相关的实验。正确做法是：一个实验项、一张参数表、50 行 `RUN`。

## 2. 正式框架平级表与历史来源连线

```text
正式框架区——所有节点同级

├─ FRAMEWORK-V1  [framework/v1, tag v1]  来源：none
├─ FRAMEWORK-V2  [framework/v2, tag v2]  来源：FRAMEWORK-V1
├─ FRAMEWORK-V3  [framework/v3, tag v3]  来源：FRAMEWORK-V2
└─ FRAMEWORK-V5  [framework/v5, tag v5]  来源：FRAMEWORK-V3

历史来源指针——箭头从当前框架指向来源框架

FRAMEWORK-V2 ──derived_from──> FRAMEWORK-V1
FRAMEWORK-V3 ──derived_from──> FRAMEWORK-V2
FRAMEWORK-V5 ──derived_from──> FRAMEWORK-V3
```

来源连线写在每个正式框架的 `framework.yaml` 附属信息中。它回答“这套代码从哪里演变来”，不能被解释成 V2 放在 V1 里面、V3 放在 V2 里面。

## 3. 尝试可以隶属，正式框架不能嵌套

```text
FRAMEWORK-V5
└─ innovation/V5-INNOVATION-001
   ├─ RUN-001  候选尝试，无正式 Tag
   ├─ RUN-002  候选尝试，无正式 Tag
   └─ RUN-003  候选尝试，无正式 Tag
```

候选没有通过确认时，只留在 `V5-INNOVATION-001` 中。确认并接纳后：

1. 来源创新记录保留在 V5 下面，并把 `promoted_framework` 写成新框架编号；
2. 从已确认代码提交创建新的 `framework/vY`；
3. 创建冻结 Tag `vY`；
4. 在正式框架区新增同级 `FRAMEWORK-VY`；
5. 新框架用 `derived_from_framework: FRAMEWORK-V5` 记录来源，不成为 V5 的子目录或子节点。

纯调参、纯消融、纯确认以及未确认创新都不能占用正式框架编号或创建 Tag。

## 4. Git 分支

| 分支 | 用途 | 是否长期保留 |
|---|---|---|
| `main` | 总索引、规范、当前正式状态 | 是 |
| `framework/vX` | 某个同级正式框架的代码主线 | 是 |
| `exp/vX/tune/...` | 某个框架的调参实验 | 临时，但不自动删除 |
| `exp/vX/ablation/...` | 某个框架的消融实验 | 临时，但不自动删除 |
| `exp/vX/innovation/...` | 某个框架的创新实验与候选尝试 | 临时，但不自动删除 |
| `exp/vX/confirmation/...` | 某个框架的确认实验 | 临时，但不自动删除 |

新实验必须从所属的 `framework/vX` 开分支。不会自动 push，也不会自动激活主线。

## 5. 每个正式框架的固定目录

```text
experiments/vX/
├─ VERSION.md
├─ framework.yaml
├─ framework_diagram.md
├─ MODULES.md
├─ EXPERIMENTS.md
├─ tune/INDEX.md
├─ ablation/INDEX.md
├─ innovation/INDEX.md
└─ confirmation/INDEX.md
```

所有 `experiments/vX/` 在文件系统中也是同级目录。`EXPERIMENTS.md` 是人看的总览；四个 `INDEX.md` 是正式台账；参数矩阵 CSV 是机器事实源，Markdown 是人类阅读版。

## 6. 每个实验项的固定入口

```text
INNOVATION-001_example/
├─ README.md
├─ PARAMETER_MATRIX.csv
├─ PARAMETER_MATRIX.md
├─ result.md
└─ evidence/
```

旧 helper 需要的 `config.yaml`、`manifest.yaml`、`result.yaml`、`quality_check.md` 和 `agent_summary.md` 可以继续存在，但人平时只需看上面五个入口。

## 7. 命名

| 类型 | 人看的编号 | 目录编号 |
|---|---|---|
| 调参 | `V5-TUNE-001` | `TUNE-001_slug` |
| 消融 | `V5-ABLATION-001` | `ABLATION-001_slug` |
| 创新 | `V5-INNOVATION-001` | `INNOVATION-001_slug` |
| 确认 | `V5-CONFIRM-001` | `CONFIRM-001_slug` |
| 实际运行 | `RUN-001` | 参数矩阵的一行 |

`TRIAL-xxx`、`ATTEMPT-xxx`、`DR-xxx` 是历史或 Runner 内部编号，只能放进 `legacy_ref`、`run_id`、`work_item_id` 或说明列。

## 8. 正式框架附属信息

每个 `framework.yaml` 至少记录：

- `registry_level: formal_peer`：说明它与其他正式框架同级；
- `derived_from_framework`：它从哪个正式框架演变来，V1 为 `none`；
- `promoted_from_experiment`：是哪项创新实验确认出了它；
- `framework_branch`、`framework_tag`、`framework_commit`：正式代码身份；
- `origin_status`：历史上怎样被确定；
- `modules`、`inherits`、`does_not_inherit`：实际代码和能力差异。

来源创新的 `innovation/INDEX.md` 使用 `Promoted framework` 反向登记新正式框架。两边对不上、来源框架不存在、来源指针成环时，机器校验必须失败。

## 9. 旧记录迁移

1. 不移动、不改名、不删除旧实验结果、日志指针、哈希和提交号。
2. 在正式框架的四类索引中建立映射，例如 `V5-ABLATION-001 -> ATTEMPT-019`。
3. 能恢复逐运行参数时补成 `RUN-001...RUN-N`；不能恢复时写 `legacy_summary_only`，绝不猜参数。
4. 正在运行的旧实验先保持原样；仅处于 `planned` 的实验可以登记为 `planned`，不能写成已完成。

规范启用后，`record-module-attempt` 只允许补录能由旧提交证明的历史摘要，并且不能写成 keep、best 或 promotion。任何新运行必须先在所属正式框架的四类账本创建实验，再使用 `record-result`。

## 10. 当前历史特例

V1、V2、V3、V5 都是同级正式框架并保留现有正式 Tag。V2 的来源指针指向 V1，V3 指向 V2，V5 指向 V3。历史来源状态继续如实记录，但不再展示成上下级树。

`v4` 是历史上把纯调参配置误当成框架版本留下的 Tag。它必须保留用于回查，但不是正式框架节点，也不能创建 `framework/v4` 或 `experiments/v4/framework.yaml`。

动态路由仍只是 V5 下的候选创新，因为精确复跑没有还原；它没有新的正式框架编号或 Tag。

## 11. 签署行

> 自 2026-08-06 起，GTPJ 正式采用“正式框架全部平级 + 历史来源指针 + 四类实验 + 候选无 Tag + 确认后注册同级框架”的唯一规范；任何父子框架、逻辑嵌套或正式框架套娃表述均停止使用。
