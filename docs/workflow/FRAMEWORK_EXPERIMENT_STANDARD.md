# GTPJ 框架树与实验正式规范

```yaml
standard_id: SYS-WORKFLOW-V6
execution_standard: SYS-WORKFLOW-V6
ledger_id: DATA-FRAMEWORK-TREE-V3
status: active
effective_date: 2026-08-15
owner_approved: true
owner_approval_source: 当前任务确认 main 为公共起点、框架按真实继承关系生长、owner 确认后晋级
canonical_entry: docs/workflow/FRAMEWORK_EXPERIMENT_STANDARD.md
```

## 一句话规则

`main` 是默认冻结的公共起点；候选从 `main` 或一个已确认框架的准确 commit 开始。只有 owner 明确确认后，候选才晋级为 `framework/vX`。正式框架本身就是最简模板，不再为新框架另建 `framework/vX-template-vN` 这一层。

## 1. Git 对象只有三层

| 对象 | 含义 | 是否移动 |
|---|---|---|
| `commit:<sha>` | 整个仓库的一张固定快照 | 永不移动 |
| `main`、`framework/vX`、`exp/...` | 指向某个 commit 的分支名 | 只按本规范移动 |
| `vX` | 固定框架 commit 的冻结标记 | 不移动 |

分支名中的 `/` 只是名称，不是磁盘目录。`framework/v2` 在 GitHub 分支列表中是一个直接入口；如果它从 V1 演变，Git 提交历史仍保留 V1→V2 的真实继承关系。

## 2. 框架树

```text
A  main（公共起点）
├─ B  framework/v1
│  └─ C  framework/v2，derived_from_framework: FRAMEWORK-V1
└─ X  framework/vx，derived_from_framework: main
```

- V2 继承 V1：从 V1 的准确框架 commit 开候选分支。
- VX 不继承现有框架：从 `main` 的准确 commit 开候选分支。
- V1、V2、VX 一经确认，都是可以直接选择的正式实验起点。
- `derived_from_framework` 记录真实代码血缘；它不能被抹掉，也不能根据版本号猜测。
- 是否成为正式框架只由 owner 明确确认决定，不能根据代码变化大小自动决定。

## 3. Main 的边界

新标准下，`main` 的目标职责只包括框架共用底座和治理索引：

- 数据读取与数据划分接口；
- U/S/H/ZS 统一评估；
- 通用训练工具；
- workflow、schema 和框架总账。

新公共底座不得把 PSE、Adapter 或任何具体框架专属模型当作默认继承内容。当前仓库的 `main` 仍带有历史 V5 运行文件；本次治理改动不删除或伪装这些历史代码。首次从 `main` 创建完全独立框架前，必须由 owner 明确确认一个已经完成公共底座清理的准确 main commit。

`main` 默认不移动；确有公共修复时，必须先在 `codex/` 分支完成、通过机器检查和规定审核，再由 owner 明确批准进入 `main`。已有框架不会因 `main` 后续变化而自动改变。

## 4. 正式框架本身就是最简模板

每个新标准框架只登记一个代码对象：

```text
framework/vX  → 最简可运行代码 commit
vX            → 同一 commit 的冻结标记
```

Tag 只是固定标记，不是第二份代码母版。`TEMPLATE.yaml` 是这一个框架的绑定卡，不是另一层模型对象：

```yaml
framework_id: FRAMEWORK-VX
template_id: FRAMEWORK-VX
template_status: canonical
template_branch: framework/vx
template_tag: vx
template_commit: <准确40位SHA>
```

最简模板只保留模型、训练入口、必要配置、数据接口、评估接口和最小复现信息。失败模块、临时代码、checkpoint、数据集、大日志和其他框架的无关代码不得进入。

历史 `MODEL-VX-TEMPLATE-VN`、`framework/vX-template-vN` 和 `model/vX-template-vN` 原地只读保留；只有 `canonical` 能启动新实验，历史 `frozen / legacy_frozen` 只用于回查。它们不再是新框架的默认结构。

`main_runtime_status` 在 canonical 绑定卡中统一为 `inactive`：正式运行代码属于各自冻结的 `framework/vX` commit，不再把治理分支 `main` 伪装成某一个框架的当前运行副本。

### 4.1 历史框架 commit 如何使用当前治理 helper

V1/V2/V3/V5 的正式框架 commit 早于当前 V6 治理规则，因此这些 commit 内自带的旧 helper、schema 和流程文档没有当前命令权。新实验不得在历史 checkout 内直接执行旧 helper，也不得为了取得新流程而把 `main` 的模型代码合进旧框架。

唯一入口是从一份**干净且已经审核的治理 commit**执行当前 helper，并用 `--repo-root` 明确指向准确框架 checkout：

```text
python <governance_checkout>/workflow/gtpj_workflow.py new-experiment \
  --repo-root <framework_checkout> \
  --template-registry-ref <same_governance_commit> \
  --version vX --kind <kind> --exp-id <ID> --slug <slug>
```

机器同时要求：治理 helper checkout 的 `HEAD` 等于 `template_registry_commit` 且工作区干净；目标 checkout 位于预期 `exp/vX/...` 分支、`HEAD` 精确等于 canonical `framework/vX` commit。后续校验和正式运行命令也应由同一治理 helper 通过全局 `--repo-root <framework_checkout>` 执行；此时规则与 schema 读取治理 checkout，模型、配置、账本和 Git 身份读取目标 checkout。这样保留真实旧框架代码，又不会执行过期流程。

旧框架 commit 可能还没有后来建立的 `innovation/INDEX.md`、`framework.yaml` 或 `EXPERIMENTS.md`。`new-experiment` 会先从同一个 `template_registry_commit` 完整预检，再把**所属版本的轻量治理覆盖层**（`framework.yaml`、canonical `TEMPLATE.yaml`、`MODULES.md`、`EXPERIMENTS.md` 和四类 `INDEX.md`）写入目标实验分支；覆盖层本身不复制或覆盖模型、训练入口、所属框架 config、数据或历史运行产物。实验目录仍按正常规则从所属框架 config 生成自己的配置快照。覆盖层缺任一文件、目标实验 ID 已在 registry 中存在，或目标框架 config/中央实验索引缺失时，命令在创建实验目录前失败。

## 5. 候选晋级

### 5.1 继承已有框架

```text
framework/v1
└─ exp/v1/innovation/innovation-xxx-candidate-v2
```

只有 confirmation、质量检查、代码瘦身和 owner 接纳全部通过后：

1. 锁定候选最终 `commit:<sha>`；
2. owner 明确接纳后写入 `OWNER_DECISION.yaml`，绑定候选实验、目标框架和该准确 commit；
3. 创建 `framework/v2` 与冻结标记 `v2`，两者指向同一 commit；
4. 登记 `derived_from_framework: FRAMEWORK-V1`；
5. 登记 `promoted_from_experiment: V1-INNOVATION-xxx` 与 `owner_decision_ref`；
6. 把 `experiments/v2/` 建成四类空账本；
7. 原候选记录保留在 V1 创新账本，后续新实验直接从 V2 开始。

owner 接纳记录的最小格式为：

```yaml
schema_version: gtpj.owner_decision.v1
decision: accepted
framework_id: FRAMEWORK-V2
framework_commit: <候选最终40位SHA>
source_experiment: V1-INNOVATION-xxx
decision_source: owner_task:<稳定的当前任务引用>
```

晋级不复制第二份 V2，不改写提交历史，也不把实验代码合回 V1。

`OWNER_DECISION.yaml` 的缺失、路径越界、重复键或字段绑定不一致会被机器拒绝。机器只能验证记录与 commit/实验的绑定，不能从一段自声明文字中密码学证明“这句话确实来自 owner”；因此接纳真实性仍是人工权限门：只有 owner 在当前任务中明确批准后才允许写入该文件，Agent 自行伪造 `decision_source` 即使格式正确也属于违规。

### 5.2 完全独立框架

完全不继承现有框架时，从 `main` 的准确 commit 开发。owner 确认后登记：

```yaml
derived_from_framework: main
derived_from_commit: <候选实际分叉时的main准确40位SHA>
promoted_from_experiment: owner-confirmed-independent
origin_status: owner_confirmed_independent
owner_decision_ref: experiments/vX/OWNER_DECISION.yaml
```

### 5.3 面向下一版本的候选实验家族

目标版本尚未晋级时，不得提前创建 `experiments/vY/`、`framework/vY` 或 `vY` Tag。
相关尝试仍登记在真实来源框架的 innovation 账本，并在 `EXPERIMENT.yaml` 写：

```yaml
candidate_family: clean_vY
target_framework: FRAMEWORK-VY
candidate_framework_status: attempt_only
```

这三个字段只把分散实验归为同一候选家族，不赋予正式版本身份，也不能绕过
confirmation、质量检查和 `OWNER_DECISION.yaml`。失败实验原地保留并写明停止原因；
后续候选必须从已确认框架或独立公共底座的准确 commit 单独分叉，不能在失败实验代码上继续堆模块。

当前唯一已登记的家族绑定是 `clean_v6 ↔ FRAMEWORK-V5 ↔ FRAMEWORK-V6 ↔ innovation ↔ attempt_only`。helper 对这五项做精确匹配；把 `clean_v6` 挂到 V1、改成 tune，或指向其他目标版本都会失败。新增家族必须先显式修改治理映射并按代码规则重新审核，不能靠自由文本临时造名。

## 6. 四类实验

每个正式框架固定拥有：

```text
experiments/vX/
├─ tune/
├─ ablation/
├─ innovation/
└─ confirmation/
```

每项实验必须读取所属框架的 `TEMPLATE.yaml` 和准确 commit，创建自己的 `EXPERIMENT.yaml`，再从准确框架提交独立分叉。实验代码不得并回正式框架，也不得从另一个实验分支继续叠代码。

| 分支 | 用途 | 生命周期 |
|---|---|---|
| `exp/vX/tune/...` | 调参 | 实验分支 |
| `exp/vX/ablation/...` | 消融 | 实验分支 |
| `exp/vX/innovation/...` | 创新候选 | 实验分支 |
| `exp/vX/confirmation/...` | 确认 | 实验分支 |
| `codex/<task>` | 代码或规则实现 | 临时开发分支 |

实验失败必须如实记录，但不会自动改变正式框架。纯调参、纯消融、纯确认和未接纳创新不能创建新框架编号。

## 7. 正式框架账本

每个 `experiments/vX/framework.yaml` 至少记录：

- `framework_id`、`framework_version`；
- `derived_from_framework`：`main`、`none` 或一个已存在的 `FRAMEWORK-VY`；
- `derived_from_commit`：独立框架必须记录实际分叉时的 `main` commit；
- `promoted_from_experiment`；
- `framework_branch`、`framework_tag`、`framework_commit`；
- `origin_status`、`change_type`；
- 新晋级框架的 `owner_decision_ref`，并由该记录绑定 `accepted`、目标框架、来源实验和准确 commit；
- `modules`、`inherits`、`does_not_inherit`。

每个新模块还必须在 `experiments/vX/MODULES.md` 登记：英文缩写、英文全称、中文含义和一句话作用。第一次向 owner 解释时必须把四项一起说清楚，不能只报缩写；例如不能只写 `PSE`，而要同时说明它的全称、中文含义，以及“用多条类别描述形成或校准类别语义原型”这类直白作用。

对来源论文做出可复核的小改动，可以先登记为“项目创新候选”；但只有相关工作检索、同口径基线、单变量实验和机制 control 支持后，才能写成论文方法贡献。改名、只换缩写或无法由实验隔离的微调不能冒充原创模块。

父框架不存在、继承关系成环、commit/branch/tag 对不上、缺少合规 owner 接纳记录或模板不是最简可运行状态时，机器校验必须失败。owner 是否真实作出该决定仍按上文执行人工权限门，不能把“记录格式通过”误写成“机器证明了 owner 本人授权”。

## 8. 实验与运行

一个实验回答一个问题并拥有一张参数矩阵；每个真实训练对应一行 `RUN-xxx`。实验目录至少包含：

```text
EXPERIMENT.yaml
PARAMETER_MATRIX.csv
PARAMETER_MATRIX.md
result.md
evidence/
```

必须记录准确框架 commit、实验 commit、配置、数据/划分、seed、评估口径和 U/S/H/ZS。debug/smoke 不能作为 promotion 或 confirmation evidence。

## 9. 旧结构

- 现有 V1、V2、V3、V5 的分支、Tag、commit 和实验记录继续用于历史回查。
- `v4` 仍是历史 config-only Tag，不是正式框架。
- 现有 `framework/v5-template-v1/v2` 与 `model/v5-template-v1/v2` 保持原 SHA，不移动、不冒充新标准框架。
- 新标准生效后，不再自动创建双层模板引用；旧资产是否删除必须由 owner 另行明确批准。

## 10. 当前签署

> 自 2026-08-15 起，GTPJ 采用“main 为默认冻结公共起点；框架按真实代码继承关系形成树；正式框架本身就是最简模板；候选只有 owner 确认后才晋级；四类实验从准确框架 commit 独立分叉”的唯一当前结构规范。
