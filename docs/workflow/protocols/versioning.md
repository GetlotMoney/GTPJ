# 框架版本管理

本页服从 `docs/workflow/FRAMEWORK_EXPERIMENT_STANDARD.md`。它只解释代码分支、冻结 tag 和框架继承，
不重复定义实验目录。

## 三种对象不要混在一起

| 对象 | 人话解释 | 示例 |
|---|---|---|
| `main` | 总管理分支，放规则、总索引和当前状态 | `main` |
| `framework/vX` | 某个正式框架继续做实验时使用的长期代码分支 | `framework/v5` |
| `vX` tag | 某个时点不可变的代码快照，用于准确复现 | `v5` |

正式框架的人类编号写成 `FRAMEWORK-VX`。已登记长期分支为 `framework/v1`、`framework/v2`、
`framework/v3`、`framework/v5`。历史 `v4` 只是配置快照，不是独立正式框架，因此不得补造
`framework/v4` 或 `experiments/v4/framework.yaml`。

## 每个框架必须有什么

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

`EXPERIMENTS.md` 是从四个 `INDEX.md` 生成的人类总览，不能手工维护第二份事实。

## 框架树

框架可以分叉，不要求严格线性继承。父子关系以 `framework.yaml`、
`experiments/FRAMEWORK_TREE.md` 和 `experiments/VERSION_TREE.md` 为准，不能只靠 Git commit 的父节点猜。

```text
FRAMEWORK-V1
├─ INNOVATION-001 -> FRAMEWORK-V2
└─ 其他已确认创新 -> 另一条子框架

FRAMEWORK-V2
└─ INNOVATION-001 -> FRAMEWORK-V3

FRAMEWORK-V3
└─ INNOVATION-001 -> FRAMEWORK-V5
```

旧 `TRIAL / ATTEMPT` 目录继续保存证据，但只通过 `legacy_ref` 映射到正式实验；它们不再定义一棵
与框架树并列的新树。

## 新实验从哪里开分支

新实验一律从目标框架长期分支开出：

```text
framework/v5
└─ exp/v5/ablation/ablation-001-local-branch-effect
```

统一格式：

```text
exp/vX/<type>/<experiment-id>-<slug>
```

其中 `<type>` 是 `tune`、`ablation`、`innovation` 或 `confirmation`。`base_code_tag` 记录不可变
快照，`code_commit` 记录这次实际运行的代码；tag 不再作为新实验分支的日常起点。

## 创新怎样变成子框架

创新先留在父框架，例如：

```text
FRAMEWORK-V5 / V5-INNOVATION-001
```

只有同时满足下列条件，才创建子框架：

- 改变了框架或代码语义，不只是数值调参；
- 结果、质量检查和确认实验完整；
- `promotion_decision: promote`；
- 证据达到 `confirmation_grade` 或 `baseline_grade`；
- 新框架的代码分支、tag、`framework.yaml` 和四类索引已准备好；
- 通过仓库机器检查和规定轮数的独立审核。

通过后：

1. 从已确认创新的明确 `code_commit` 创建 `framework/vY`。
2. 创建不可变快照 tag `vY`。
3. 在 `experiments/vY/framework.yaml` 写明 `parent_framework` 和 `source_experiment`。
4. 给子框架建立四类空账本；不要把父框架的运行目录复制进去。
5. 更新框架树、总索引和项目状态。

纯调参、纯消融和纯确认不能产生新框架。创新未确认时也不能提前占用新框架编号。

## 提升后的代码与总账

`main` 继续保存全局规则和全部框架索引；`framework/vX` 保存该框架继续实验所需的代码线。
不得为了基于旧框架实验而把 `main` 回退，也不得把旧工作树整体覆盖到 `main`。

推送 `main`、框架分支或 tag 到远端仍需要用户当前明确授权。创建本地正式记录不等于自动发布。

## 提升成功标准

指标提高只是必要证据之一。正式子框架还必须满足：

- 单次最高值只写 `best_observed_H`，不能冒充 `confirmed_H`；
- `run_commit` 来自干净状态，配置、命令、seed、数据口径和评估口径可追溯；
- class order、seen/unseen split、logits shape 和指标算法一致；
- 模块关闭后能回到父框架行为，或明确说明为何不能；
- 外部日志和 checkpoint 只登记 artifact id、URI、hash、size，不复制进 GitHub；
- `framework.yaml`、四类索引、框架树、总注册表和项目状态同步完成。

只提高一次 H、确认失败或证据缺失时，保留为父框架下的实验结果，不能创建子框架。
