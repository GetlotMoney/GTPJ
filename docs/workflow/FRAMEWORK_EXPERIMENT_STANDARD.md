# GTPJ 框架与实验正式规范

```yaml
standard_id: SYS-WORKFLOW-V3
ledger_id: DATA-FRAMEWORK-LEDGER-V1
status: active
effective_date: 2026-08-06
owner_approved: true
owner_approval_source: 当前任务明确要求正式采用本规范
canonical_entry: docs/workflow/FRAMEWORK_EXPERIMENT_STANDARD.md
```

## 一句话规则

一个正式框架就是一套可长期维护的代码和方法。每个框架固定拥有调参、消融、创新、确认四类同级实验；创新被确认并接纳后，才长出一个新的子框架，子框架再拥有同样的四类实验。

本文件是今后唯一的正式结构规范。旧文档中的 `TRIAL / ATTEMPT` 继续保留用于回查历史，但不能再作为人平时查看实验的主名称。

## 1. 三层对象

| 层级 | 人话解释 | 正式例子 |
|---|---|---|
| 框架 | 一套确定的模型代码与方法 | `FRAMEWORK-V5` |
| 实验项 | 在该框架下回答一个具体问题 | `V5-ABLATION-001` |
| 运行 | 参数表里真正执行的一行 | `RUN-003`，旧系统任务号可为 `DR-003` |

禁止把一次包含 50 个任务的批次写成 50 个互不相关的实验。正确做法是：一个实验项、一张参数表、50 行 `RUN`。

## 2. 框架树

```text
FRAMEWORK-V1
├─ tune / ablation / innovation / confirmation
└─ V1-INNOVATION-001 ──历史 owner 接纳，未按新规确认──> FRAMEWORK-V2
   ├─ tune / ablation / innovation / confirmation
   └─ V2-INNOVATION-001 ──历史 owner 接纳，未按新规确认──> FRAMEWORK-V3
      ├─ tune / ablation / innovation / confirmation
      └─ V3-INNOVATION-001 ──历史 owner 激活──> FRAMEWORK-V5
         └─ tune / ablation / innovation / confirmation
```

框架树是逻辑嵌套，不复制代码目录。父子关系写在 `framework.yaml` 和父框架的 `innovation/INDEX.md` 中，所以既能像家谱一样查看，也不会出现目录无限套娃。

## 3. Git 分支

| 分支 | 用途 | 是否长期保留 |
|---|---|---|
| `main` | 总索引、规范、当前正式状态 | 是 |
| `framework/vX` | 某个正式框架的代码主线 | 是 |
| `exp/vX/tune/...` | 某个框架的调参实验 | 临时，但不自动删除 |
| `exp/vX/ablation/...` | 某个框架的消融实验 | 临时，但不自动删除 |
| `exp/vX/innovation/...` | 某个框架的创新实验 | 临时，但不自动删除 |
| `exp/vX/confirmation/...` | 某个框架的确认实验 | 临时，但不自动删除 |

新实验必须从对应的 `framework/vX` 开分支。纯调参不会生成新框架；只有创新实验通过确认、质量检查和接纳门槛后，才允许建立新的 `framework/vY` 和 `vY` 标签。不会自动 push，也不会自动激活主线。

## 4. 每个框架的固定目录

```text
experiments/vX/
├─ VERSION.md
├─ framework.yaml
├─ framework_diagram.md
├─ MODULES.md
├─ EXPERIMENTS.md          # 由四个 INDEX 生成，禁止手工维护第二份数据
├─ tune/INDEX.md
├─ ablation/INDEX.md
├─ innovation/INDEX.md
└─ confirmation/INDEX.md
```

`EXPERIMENTS.md` 是人看的总览；四个 `INDEX.md` 是正式台账；参数矩阵 CSV 是机器事实源，Markdown 是它的人类阅读版。

## 5. 每个实验项的固定入口

```text
TUNE-001_example/
├─ README.md
├─ PARAMETER_MATRIX.csv
├─ PARAMETER_MATRIX.md
├─ result.md
└─ evidence/
```

旧 helper 需要的 `config.yaml`、`manifest.yaml`、`result.yaml`、`quality_check.md` 和 `agent_summary.md` 可以继续存在，但人平时只需看上面五个入口。

## 6. 命名

| 类型 | 人看的编号 | 目录编号 |
|---|---|---|
| 调参 | `V5-TUNE-001` | `TUNE-001_slug` |
| 消融 | `V5-ABLATION-001` | `ABLATION-001_slug` |
| 创新 | `V5-INNOVATION-001` | `INNOVATION-001_slug` |
| 确认 | `V5-CONFIRM-001` | `CONFIRM-001_slug` |
| 实际运行 | `RUN-001` | 参数矩阵的一行 |

`TRIAL-xxx`、`ATTEMPT-xxx`、`DR-xxx` 是历史或 Runner 内部编号，只能放进 `legacy_ref`、`run_id`、`work_item_id` 或说明列。

## 7. 旧记录迁移

1. 不移动、不改名、不删除旧实验结果、日志指针、哈希和提交号。
2. 在新框架的四类索引中建立映射，例如 `V5-ABLATION-001 -> ATTEMPT-019`。
3. 能恢复逐运行参数时，补成 `RUN-001...RUN-N`；不能恢复时写 `legacy_summary_only`，绝不猜参数。
4. 正在运行的旧实验先保持原样，结束后再补映射。仅处于 `planned` 的实验可以先登记为 `planned`，但不能写成已完成。

## 8. 新框架必须记录的身份

`framework.yaml` 至少记录：`framework_id`、`parent_version`、`source_experiment`、`source_legacy_ref`、`framework_branch`、`framework_tag`、`framework_commit`、`governance_source_commit`、`lineage_status`（这个子框架是怎样来的）、`change_type`、`modules`、`inherits`、`does_not_inherit` 和 `status`。

父框架的创新索引必须反向写出子框架编号。两边对不上时，校验失败。

## 9. 当前历史特例

`v4` 是历史上把纯调参配置误当成框架版本留下的标签。它必须保留用于回查，但不是正式框架节点，也不能创建 `framework/v4`。正式引用仍是 `v3` 下的确认配置。

V1→V2、V2→V3、V3→V5 都早于本规范。它们保留为真实历史框架，但不能倒推成“已经通过新规确认”：V1→V2、V2→V3 标为 `legacy_owner_accepted_unconfirmed`，V3→V5 标为 `legacy_owner_activated`。只有规范生效后的新子框架，才允许使用 `confirmed_promoted`，并且必须同时有 `promotion_decision: promote` 和通过的质量检查。

## 10. 签署行

> 自 2026-08-06 起，GTPJ 正式采用“框架版本 + 四类同级实验 + 创新生成子框架 + 每个实验一张参数矩阵”的唯一规范；旧规范仅作历史兼容，不再作为新工作的入口。
