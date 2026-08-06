# 框架版本管理

本页服从 `docs/workflow/FRAMEWORK_EXPERIMENT_STANDARD.md`。它只解释代码分支、冻结 Tag、同级正式框架和历史来源指针，不重复定义实验目录。

## 三种对象不要混在一起

| 对象 | 人话解释 | 示例 |
|---|---|---|
| `main` | 总管理分支，放规则、总索引和当前状态 | `main` |
| `framework/vX` | 某个同级正式框架继续做实验时使用的长期代码分支 | `framework/v5` |
| `vX` Tag | 正式框架某个时点的不可变代码快照 | `v5` |

正式框架的人类编号写成 `FRAMEWORK-VX`。已登记长期分支为 `framework/v1`、`framework/v2`、`framework/v3`、`framework/v5`。它们全部同级。

历史 `v4` 只是配置快照，不是独立正式框架，因此不得补造 `framework/v4` 或 `experiments/v4/framework.yaml`。

## 每个正式框架必须有什么

每个正式框架目录 `experiments/vX/` 至少包含：

```text
VERSION.md
framework.yaml
framework_diagram.md
MODULES.md
EXPERIMENTS.md
tune/INDEX.md
ablation/INDEX.md
innovation/INDEX.md
confirmation/INDEX.md
```

`EXPERIMENTS.md` 从四个 `INDEX.md` 生成，不能手工维护第二份事实。

## 同级注册表与来源指针

```text
FRAMEWORK-V1  derived_from: none
FRAMEWORK-V2  derived_from: FRAMEWORK-V1
FRAMEWORK-V3  derived_from: FRAMEWORK-V2
FRAMEWORK-V5  derived_from: FRAMEWORK-V3
```

`derived_from_framework` 只记录代码和方法从哪里演变而来。它不会让 V2 成为 V1 的子目录，也不会让正式框架形成递归嵌套。

旧 `TRIAL / ATTEMPT` 目录继续保存证据，但只通过 `legacy_ref` 映射到正式实验；它们不定义另一棵框架树。

## 新实验从哪里开分支

新实验一律从所属正式框架的长期分支开出：

```text
framework/v5
└─ exp/v5/ablation/ablation-001-local-branch-effect
```

统一格式：

```text
exp/vX/<type>/<experiment-id>-<slug>
```

其中 `<type>` 是 `tune`、`ablation`、`innovation` 或 `confirmation`。`base_code_tag` 记录不可变基线，`code_commit` 记录实际运行代码。

## 创新候选怎样变成同级正式框架

创新候选先留在所属正式框架，例如：

```text
FRAMEWORK-V5 / V5-INNOVATION-001
```

候选阶段不能创建 `framework/vY`、正式编号或 Tag。只有同时满足下列条件，才允许注册新的同级正式框架：

- 改变了框架或代码语义，不只是数值调参；
- 结果、质量检查和确认实验完整；
- `promotion_decision: promote`；
- 证据达到 `confirmation_grade` 或 `baseline_grade`；
- 新正式框架的代码分支、Tag、`framework.yaml` 和四类索引已准备好；
- 通过仓库机器检查和规定轮数的独立审核。

通过后：

1. 从已确认创新的明确 `code_commit` 创建 `framework/vY`；
2. 创建不可变快照 Tag `vY`；
3. 在 `experiments/vY/framework.yaml` 写 `registry_level: formal_peer`、`derived_from_framework` 和 `promoted_from_experiment`；
4. 给新同级正式框架建立四类空账本，不复制来源框架的运行目录；
5. 在来源创新索引的 `Promoted framework` 列登记 `FRAMEWORK-VY`；
6. 更新同级注册表、来源连线和项目状态。

纯调参、纯消融、纯确认不能产生正式框架。创新未确认时也不能提前占用新框架编号或 Tag。

## 提升后的代码与总账

`main` 继续保存全局规则和全部同级框架索引；`framework/vX` 保存该框架继续实验所需的代码线。不得为了基于旧框架实验而把 `main` 回退，也不得把旧工作树整体覆盖到 `main`。

推送 `main`、框架分支或 Tag 到远端仍需要用户当前明确授权。创建本地正式记录不等于自动发布。

## 注册成功标准

指标提高只是必要证据之一。新的同级正式框架还必须满足：

- 单次最高值只写 `best_observed_H`，不能冒充 `confirmed_H`；
- `run_commit` 来自干净状态，配置、命令、seed、数据口径和评估口径可追溯；
- class order、seen/unseen split、logits shape 和指标算法一致；
- 模块关闭后能回到来源框架行为，或明确说明为何不能；
- 外部日志和 checkpoint 只登记 artifact id、URI、hash、size，不复制进 GitHub；
- `framework.yaml`、四类索引、同级注册表和项目状态同步完成。

只提高一次 H、确认失败或证据缺失时，结果保留在所属正式框架的创新实验中，不能注册新正式框架或创建 Tag。
