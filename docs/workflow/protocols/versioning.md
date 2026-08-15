# 框架版本与继承规则

本页服从 `docs/workflow/FRAMEWORK_EXPERIMENT_STANDARD.md`。

## 三个 Git 对象

| 对象 | 含义 | 规则 |
|---|---|---|
| `commit:<sha>` | 整个仓库的一张固定快照 | 永不移动 |
| `framework/vX` | 一个已确认框架的直接入口 | 固定在正式框架 commit |
| `vX` | 同一框架 commit 的冻结标记 | 永不移动 |

正式框架本身就是最简模板。`TEMPLATE.yaml` 只把 `FRAMEWORK-VX`、`framework/vX`、`vX` 和准确 commit 绑定起来，不再创造第二个代码对象。

## 真实继承

```text
main
├─ framework/v1
│  └─ framework/v2
└─ framework/vx-independent
```

- V2 基于 V1：V1 正式 commit 必须是 V2 正式 commit 的 Git 祖先，账本写 `derived_from_framework: FRAMEWORK-V1`。
- VX 完全独立：从 `main` 的准确 commit 分叉，账本写 `derived_from_framework: main` 和 `derived_from_commit: <sha>`。
- 每个已确认节点都可直接开新实验；直接可选不等于抹除父子血缘。
- 版本号只标身份，不能用 V2/V3 的数字大小猜继承关系。

## 实验分支

每项实验先读 `TEMPLATE.yaml`，再创建 `EXPERIMENT.yaml`，统一命名：

```text
exp/vX/tune/<experiment-id>-<slug>
exp/vX/ablation/<experiment-id>-<slug>
exp/vX/innovation/<experiment-id>-<slug>
exp/vX/confirmation/<experiment-id>-<slug>
```

分支 `HEAD` 必须从准确框架提交独立分叉。实验代码不得并回正式框架，也不得拿一项实验作为另一项实验的代码起点。

## 候选晋级

候选阶段没有正式编号、`framework/vY` 或 `vY`。只有确认、质量检查、瘦身和 owner 明确接纳全部通过后，才在候选最终 commit 同时创建：

```text
framework/vY -> <candidate-final-commit>
vY           -> <candidate-final-commit>
```

若候选来自 `framework/vX`，新框架保留 X→Y 的真实 Git 血缘；若完全独立，则记录实际 `main` 起点。晋级不会移动 `main`，也不会自动激活新框架。

## 历史兼容

历史 `MODEL-VX-TEMPLATE-VN`、`framework/vX-template-vN` 和 `model/vX-template-vN` 保持原 SHA，只读回查。只有 `canonical` 能启动新实验，历史 `frozen / legacy_frozen` 不能启动。旧分支或 Tag 不移动、不改名、不删除，除非 owner 另行明确批准。

## GitHub 边界

本地登记不等于发布。push、创建远端 Tag、删除远端引用、强推或改写历史都必须获得 owner 当前明确授权。
