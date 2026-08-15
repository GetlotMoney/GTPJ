# GTPJ GitHub 管理规范

本页只说明 GitHub 上的分支、Tag、框架继承和发布边界。实验科学规则见 `docs/workflow/FRAMEWORK_EXPERIMENT_STANDARD.md`。

## 1. 一句话结构

`main` 是默认冻结的公共底座；一个候选只有在 owner 明确确认后，才在候选最终 commit 上成为 `framework/vX`，并用 `vX` 固定同一 commit。

```text
main -> FRAMEWORK-VX             # 完全独立的新框架
FRAMEWORK-V1 -> FRAMEWORK-V2     # V2 真实继承 V1
```

GitHub 的分支列表会把 `framework/v1`、`framework/v2` 显示为可直接选择的入口；Git 提交图仍保留 V1→V2 的真实父子血缘。这两件事不冲突。

## 2. main

`main` 保存公共底座、治理规则和总账，默认不移动。当前 `main` 仍携带历史 V5 运行文件；首次把它用于完全独立框架前，必须另行确认一个已经清理好的公共底座 commit，不能把现状假装成已完成清理。只有确属所有框架共用的修复，才先在 `codex/<task>` 上实现、验证和审核，再由 owner 明确决定是否合入。

框架创建后不会随 `main` 自动变化。把候选晋级为框架也不会移动 `main`。

## 3. 正式框架

每个新标准框架只有一个代码身份：

```text
framework/vX -> <framework-commit>
vX           -> <same-framework-commit>
```

正式框架本身就是最简模板。`experiments/vX/TEMPLATE.yaml` 只登记 `FRAMEWORK-VX`、分支、Tag 和准确 commit，不再另建一条新模板代码线。

`experiments/vX/framework.yaml` 必须记录：

```yaml
framework_id: FRAMEWORK-VX
derived_from_framework: main | FRAMEWORK-VY | none
derived_from_commit: <main直接来源时必填>
promoted_from_experiment: owner-confirmed-independent | VY-INNOVATION-xxx | initial
framework_branch: framework/vX
framework_tag: vX
framework_commit: <准确40位SHA>
owner_decision_ref: experiments/vX/OWNER_DECISION.yaml  # 新晋级框架必填
```

机器校验必须确认 branch、Tag、commit 完全一致，并确认 `derived_from_framework` 与真实 Git 祖先关系一致。

## 4. 实验分支

四类实验都从所属正式框架的准确 commit 独立分叉：

```text
exp/vX/tune/...
exp/vX/ablation/...
exp/vX/innovation/...
exp/vX/confirmation/...
```

每项实验有自己的 `EXPERIMENT.yaml` 和 `PARAMETER_MATRIX.csv`。实验之间不能接着叠代码，实验代码不能合回正式框架；结果、配置和轻量证据索引可以回填治理账本。

## 5. 候选怎样晋级

继承已有框架：

```text
framework/v1
└─ exp/v1/innovation/innovation-xxx-candidate-v2
   └─ owner 确认后：framework/v2 = v2 = 候选最终 commit
```

完全独立：

```text
main@<base-sha>
└─ 独立候选
   └─ owner 确认后：framework/vX = vX = 候选最终 commit
```

前者写 `derived_from_framework: FRAMEWORK-V1`；后者写 `derived_from_framework: main` 与准确 `derived_from_commit`。两者都必须用 `owner_decision_ref` 绑定明确接纳记录及候选最终 commit；候选未获确认前不得预占正式编号、框架分支或 Tag。

## 6. GitHub 保存什么

进入 GitHub：源代码、轻量配置、参数矩阵、结果摘要、哈希、证据索引和治理文档。

不进入 GitHub：数据集、checkpoint、原始 cache、密钥、完整大日志和生成型大文件。它们留在本地或 Warehouse，GitHub 只登记位置、SHA-256 和大小。

## 7. 历史兼容

旧 `MODEL-VX-TEMPLATE-VN`、`framework/vX-template-vN`、`model/vX-template-vN`、Trial 和 Attempt 保持原 SHA，只读回查。新工作不再沿用双层模板。任何删除、改名或迁移必须由 owner 另行明确批准。

## 8. 发布边界

本地完成、提交或创建 Tag 都不等于发布。push、创建远端 Tag、删除远端引用、强制推送、改写历史和切换远端默认分支，必须有 owner 当前明确授权。

日常状态查看与本地校验可以直接执行；任何远端变更都先停下来确认准确目标。
