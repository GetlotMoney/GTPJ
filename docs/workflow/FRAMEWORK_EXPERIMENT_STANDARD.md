# GTPJ 框架与实验正式规范

```yaml
standard_id: SYS-WORKFLOW-V5
ledger_id: DATA-FRAMEWORK-TEMPLATE-V1
status: active
effective_date: 2026-08-06
amendment_date: 2026-08-08
amendment_id: candidate-framework-validation-tree
owner_approved: true
owner_approval_source: 2026-08-08，owner 确认代码创新先作为候选框架，完成候选自身消融、调参和确认后才能晋级
canonical_entry: docs/workflow/FRAMEWORK_EXPERIMENT_STANDARD.md
```

## 一句话规则

所有已经确定的正式框架都在同一层，也都拥有正式版本号、长期分支和冻结 Tag。框架之间可以保留“从哪个正式框架演变而来”的历史连线，但这条线只表示来源，不表示包含、上下级或目录嵌套。

每个正式框架固定拥有调参、消融、创新、确认四类实验。创新候选暂时放在所属正式框架的创新实验下面，不拥有正式框架编号、长期框架分支或 Tag；只有确认并接纳后，候选代码才注册为一个新的同级正式框架。

每个正式框架还必须登记一份可版本化的只读代码母版 `MODEL-VX-TEMPLATE-VN`。`framework.yaml` 说明“这是什么方法”，`TEMPLATE.yaml` 说明“实验复制哪一份不可变代码”，`EXPERIMENT.yaml` 说明“本实验实际从哪个准确提交开始”。普通版本级实验，以及创新候选的第一次实现，都从准确母版提交独立分叉；实验代码不得并回母版。

代码创新完成第一次实现后，可以冻结成一份“候选框架快照”。候选自己的消融、调参和确认不再直接从正式框架母版开始，而是都从同一份冻结候选提交独立分叉；它们不能从彼此继续叠代码。候选不是正式框架，没有正式框架编号、长期框架分支或正式 Tag。

本文件是今后唯一的正式结构规范。旧文档中的 `TRIAL / ATTEMPT` 继续保留用于回查历史，但不能再作为新实验入口。

## 1. 五层对象

| 层级 | 人话解释 | 正式例子 |
|---|---|---|
| 正式框架 | 已确定、已登记、拥有 Tag 的一套模型代码与方法 | `FRAMEWORK-V5`、Tag `v5` |
| 代码母版 | 该框架可复制、不可直接修改的代码快照 | `MODEL-V5-TEMPLATE-V1`、Tag `model/v5-template-v1` |
| 候选框架快照 | 改过代码、但尚未晋级的完整候选实现；用准确提交冻结，供候选自身验证共同起步 | `CANDIDATE-001-R1` |
| 实验项 | 在某个正式框架下回答一个具体问题；可以是版本级实验，也可以验证某个候选 | `V5-ABLATION-001` |
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

## 3. 候选可以有验证树，正式框架不能嵌套

```text
FRAMEWORK-V5
└─ innovation/V5-INNOVATION-001
   └─ CANDIDATE-001-R1  冻结候选提交，无正式 Tag
      ├─ V5-ABLATION-002  去掉候选组件 A
      ├─ V5-ABLATION-003  去掉候选组件 B
      ├─ V5-TUNE-002      候选参数选择
      └─ V5-CONFIRM-001   候选完整版本确认
```

这是一棵研究和证据关系树，不是 Git 目录或正式框架的嵌套树。`V5-ABLATION-002` 仍放在 `experiments/v5/ablation/`，但在自己的 `EXPERIMENT.yaml` 里写明它验证 `V5-INNOVATION-001` 的 `CANDIDATE-001-R1`。

候选验证必须按下面顺序进行：

1. `V5-INNOVATION-001` 从 V5 的冻结母版实现新代码，并先冻结完整候选的准确 commit、配置和候选编号；
2. 候选内部每项消融、调参或确认都从该准确候选 commit 单独开分支，只允许改本项要验证的一个因素；
3. 每项子实验同时记录候选编号、父创新实验、候选冻结 commit、候选冻结配置和最初的 V5 模板身份；
4. 候选代码或行为发生实质改变时，必须建立新的候选修订号，例如 `CANDIDATE-001-R2`，并重新完成受影响的消融和确认；`R1` 的证据不能直接拿来晋级 `R2`；
5. 候选完整版本与来源正式框架的公平对照、必要的内部消融、参数冻结和多 seed 确认都完成后，才允许进入晋级判断。

晋级硬门是：候选完整版本对照、候选自身调参结论、候选自身必要消融和候选完整版本确认必须全部有完成记录。调参结论可以是“沿用冻结参数且无需搜索”的书面理由，不强迫无意义扫参；必要消融的范围必须在候选冻结后、训练前写清，不能事后删掉。任何一项缺失，`promotion_status` 必须是 `blocked`，不得创建 `FRAMEWORK-VY`、`framework/vY` 或正式 Tag。

候选没有通过确认或晋级判断时，只留在 `V5-INNOVATION-001` 中。确认并接纳后：

1. 来源创新记录保留在 V5 下面，并把 `promoted_framework` 写成新框架编号；
2. 新正式框架代码必须是已验证的候选冻结提交，或者是只删除未用路径后、已完成行为对照的清理提交；任何功能性改动都必须先生成新的候选修订并重新验证；
3. 用上述已确认提交登记历史来源分支 `framework/vY` 和冻结 Tag `vY`；
4. 把通过对照的干净代码冻结为 `framework/vY-template-v1`、Tag `model/vY-template-v1` 和 `MODEL-VY-TEMPLATE-V1`；
5. 在正式框架区新增同级 `FRAMEWORK-VY`，并写入 `TEMPLATE.yaml`；
6. 新框架用 `derived_from_framework: FRAMEWORK-V5` 记录来源，不成为 V5 的子目录或子节点。

纯调参、纯消融、纯确认以及未确认创新都不能占用正式框架编号或创建 Tag。

## 4. Git 分支和只读母版

| 分支 | 用途 | 是否长期保留 |
|---|---|---|
| `main` | 总索引、规范、当前正式状态 | 是 |
| `framework/vX` | 新规范启用前的正式框架历史代码线；V0 只读回查 | 是 |
| `framework/vX-template-vN` | 某个正式框架第 N 份干净母版；冻结后分支头不得移动 | 是 |
| `exp/vX/tune/...` | 某个框架的调参，或候选内部的参数选择 | 临时，但不自动删除 |
| `exp/vX/ablation/...` | 某个框架的消融，或候选内部的组件消融 | 临时，但不自动删除 |
| `exp/vX/innovation/...` | 某个框架的创新实现和候选快照 | 临时，但不自动删除 |
| `exp/vX/confirmation/...` | 某个框架或候选完整版本的确认 | 临时，但不自动删除 |

直接实验必须读取所属框架的 `TEMPLATE.yaml`，从其中登记的冻结 Tag 和准确 commit 开分支；这包括普通调参、普通消融和创新候选的第一次实现。候选内部验证实验必须从 `candidate_freeze_commit` 开分支，且 `HEAD` 必须正好等于该候选提交。两种路径都要求干净工作树、冻结参数和独立分支；实验代码不得并回母版，也不得以另一个子实验为代码起点。`legacy_frozen` 不能启动新实验，它只解释新规范启用前的历史结果。不会自动 push，也不会自动激活主线。

## 5. 每个正式框架的固定目录

```text
experiments/vX/
├─ VERSION.md
├─ framework.yaml
├─ TEMPLATE.yaml
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
├─ EXPERIMENT.yaml
├─ PARAMETER_MATRIX.csv
├─ PARAMETER_MATRIX.md
├─ result.md
└─ evidence/
```

`EXPERIMENT.yaml` 必须写清 `base_identity_kind`、母版编号、母版 Tag、母版 commit、登记这份母版的 `template_registry_commit`、实验分支和旧记录引用。母版代码提交与登记提交必须分开记录，避免一个提交要求预先知道自己的哈希。

- 创新根实验使用 `base_identity_kind: framework_template`；一旦冻结候选，必须补齐 `candidate_id`、`candidate_status`、`candidate_freeze_commit`、`candidate_freeze_branch` 和 `candidate_freeze_config_ref`。`candidate_status` 只能是 `frozen`、`under_validation`、`accepted`、`rejected` 或 `blocked`。
- 候选内部验证使用 `base_identity_kind: candidate_frozen`；必须额外写 `parent_innovation_id`、`parent_candidate_id`、`study_kind`、`candidate_freeze_commit`、`candidate_freeze_branch`、`candidate_freeze_config_ref` 和 `branch_source_commit`。其中 `branch_source_commit` 必须等于 `candidate_freeze_commit`，并仍保留最初正式母版的身份，方便一路追溯回 V5。
- 当前发布版 helper 仍要求实验分支包含 `main`，既不能正确创建从冻结母版开始的正式实验，也不支持 `candidate_frozen`。在专门的模板绑定 helper 升级通过审核前，不能用它启动任何新的正式实验；更不能把候选子实验伪装成 `framework_template`，或以手改账本绕过这条限制。

旧 helper 需要的 `config.yaml`、`manifest.yaml`、`result.yaml`、`quality_check.md` 和 `agent_summary.md` 可以继续存在。

## 7. 命名

| 类型 | 人看的编号 | 目录编号 |
|---|---|---|
| 调参 | `V5-TUNE-001` | `TUNE-001_slug` |
| 消融 | `V5-ABLATION-001` | `ABLATION-001_slug` |
| 创新 | `V5-INNOVATION-001` | `INNOVATION-001_slug` |
| 确认 | `V5-CONFIRM-001` | `CONFIRM-001_slug` |
| 实际运行 | `RUN-001` | 参数矩阵的一行 |

`TRIAL-xxx`、`ATTEMPT-xxx`、`DR-xxx` 是历史或 Runner 内部编号，只能放进 `legacy_ref`、`run_id`、`work_item_id` 或说明列。

候选快照使用 `CANDIDATE-xxx-Ry` 这种临时编号，不能抢占 `V6`、`FRAMEWORK-V6`、`framework/v6` 或正式 Tag。只有晋级通过后，才生成新的正式框架编号。

## 8. 正式框架附属信息

每个 `framework.yaml` 至少记录：

- `registry_level: formal_peer`：说明它与其他正式框架同级；
- `derived_from_framework`：它从哪个正式框架演变来，V1 为 `none`；
- `promoted_from_experiment`：是哪项创新实验确认出了它；
- `framework_branch`、`framework_tag`、`framework_commit`：正式代码身份；
- `origin_status`：历史上怎样被确定；
- `modules`、`inherits`、`does_not_inherit`：实际代码和能力差异。

每个同级 `TEMPLATE.yaml` 至少记录：

- `template_id`：母版编号，例如 `MODEL-V5-TEMPLATE-V1`；
- `template_status`：`legacy_frozen`、`draft`、`confirmed`、`frozen` 或已退役状态；
- `template_branch`、`template_tag`、`template_commit`：三者在冻结后必须指向同一提交；
- `source_framework_tag`、`source_framework_commit`：母版从哪个正式历史快照清理而来；
- `behavior_contract`：新旧行为对照合同；历史 V0 可写 `none`。

来源创新的 `innovation/INDEX.md` 使用 `Promoted framework` 反向登记新正式框架。两边对不上、来源框架不存在、来源指针成环时，机器校验必须失败。

## 9. 旧记录迁移

1. 不移动、不改名、不删除旧实验结果、日志指针、哈希和提交号。
2. 在正式框架的四类索引中建立映射，例如 `V5-ABLATION-001 -> ATTEMPT-019`。
3. 能恢复逐运行参数时补成 `RUN-001...RUN-N`；不能恢复时写 `legacy_summary_only`，绝不猜参数。
4. 正在运行的旧实验先保持原样；仅处于 `planned` 的实验可以登记为 `planned`，不能写成已完成。
5. 每个正式实验补 `EXPERIMENT.yaml`：已发生的旧实验使用 `historical_code_ref + historical_read_only`；尚未运行且等待干净母版的实验使用 `pending_clean_template + blocked_pending_clean_template`。
6. 旧 `vX` Tag 先登记为 `MODEL-VX-TEMPLATE-V0 / legacy_frozen`，只负责回查；不能把旧结果倒填成从未来 V1 干净母版运行。

规范启用后，`record-module-attempt` 只允许补录能由旧提交证明的历史摘要，并且不能写成 keep、best 或 promotion。任何新运行必须先在所属正式框架的四类账本创建实验，再使用 `record-result`。

## 10. 当前历史特例

V1、V2、V3、V5 都是同级正式框架并保留现有正式 Tag。V2 的来源指针指向 V1，V3 指向 V2，V5 指向 V3。历史来源状态继续如实记录，但不再展示成上下级树。

`v4` 是历史上把纯调参配置误当成框架版本留下的 Tag。它必须保留用于回查，但不是正式框架节点，也不能创建 `framework/v4` 或 `experiments/v4/framework.yaml`。

动态路由仍只是 V5 下的候选创新，因为精确复跑没有还原；它没有新的正式框架编号或 Tag。

V5 局部分支消融已作为 `V5-ABLATION-001` 完成并审核：FULL 与 GLOBAL_ONLY 各完成 seed 5、17、29 三条有效训练，平均 H 差值为 `+0.08`。旧 `ATTEMPT-019` 只作规划来源，不能继续沿用其代码分支。

## 11. 签署行

> 自 2026-08-06 起，GTPJ 正式采用“正式框架全部平级 + 历史来源指针 + 每框架一套可版本化只读母版 + 直接实验从准确母版独立分叉 + 候选内部验证从同一冻结候选提交独立分叉 + 实验不回写母版 + 创新完成自身消融和确认后才注册新同级框架”的唯一规范；旧 Trial/Attempt 原地只读保留，任何正式框架套娃或实验互相叠代码的做法停止使用。
