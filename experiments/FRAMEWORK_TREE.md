# GTPJ 正式框架同级表与历史来源连线

> 兼容说明：文件名继续保留为 `FRAMEWORK_TREE.md`，但本页不是上下级树。所有正式框架都在同一层，箭头只表示代码和方法的历史来源。

```text
正式框架区——同级节点

├─ FRAMEWORK-V1  [framework/v1, tag v1]
│  来源：none
│
├─ FRAMEWORK-V2  [framework/v2, tag v2]
│  来源：FRAMEWORK-V1，经 V1-INNOVATION-001
│
├─ FRAMEWORK-V3  [framework/v3, tag v3]
│  来源：FRAMEWORK-V2，经 V2-INNOVATION-001
│
└─ FRAMEWORK-V5  [framework/v5, tag v5]
   来源：FRAMEWORK-V3，经 V3-INNOVATION-001
```

## 历史来源指针

```text
FRAMEWORK-V2 ──derived_from──> FRAMEWORK-V1
FRAMEWORK-V3 ──derived_from──> FRAMEWORK-V2
FRAMEWORK-V5 ──derived_from──> FRAMEWORK-V3
```

这里的箭头不表示 V2 在 V1 里面。V1、V2、V3、V5 都是正式、独立、平级并拥有 Tag 的框架。

## 每个同级框架自己的实验

| 正式框架 | 调参 | 消融 | 创新 | 确认 |
|---|---|---|---|---|
| `FRAMEWORK-V1` | 0 | 0 | `V1-INNOVATION-001`，历史确定出 V2 | `V1-CONFIRM-001` |
| `FRAMEWORK-V2` | 0 | 0 | `V2-INNOVATION-001`，历史确定出 V3 | 0 |
| `FRAMEWORK-V3` | `V3-TUNE-001` | 0 | `V3-INNOVATION-001`，历史确定出 V5 | `V3-CONFIRM-001` |
| `FRAMEWORK-V5` | `V5-TUNE-001`，8 个真实动态路由任务 | `V5-ABLATION-001`，FULL/GLOBAL_ONLY 三种子配对已完成，平均 H 差值 `+0.08`，训练后 strict-3 已通过 | `V5-INNOVATION-001`，2 个候选探针 | 0 |

## 当前结论

- 当前模型框架：`MODEL-GTPJ-V5`，局部分支融合权重为 `local_weight=0.2`。
- 更强的已确认配置参考：`V3-CONFIRM-001`，`confirmed_H=74.47`。
- 动态路由最高单次 `H=75.11`，但精确复跑未还原，所以仍是 V5 下面的创新候选，没有获得新框架编号或 Tag。
- 局部分支消融参数表共 16 行：R3 的 6 行失败/取消历史、R4 的 6 行历史记录和 R5 的 4 行补跑记录均保留；FULL 与 GLOBAL_ONLY 各完成 seed 5、17、29 三条有效训练。FULL 平均 H 为 `74.11`，GLOBAL_ONLY 为 `74.03`，平均差值仅 `+0.08`，不能声称局部分支带来稳定 H 增益。

## 查看顺序

1. 本文件看同级正式框架与历史来源连线。
2. 打开 `experiments/vX/EXPERIMENTS.md` 看该框架四类实验。
3. 打开具体实验的 `PARAMETER_MATRIX.md` 看每一行参数和结果。
4. 需要查旧证据时，再跟随 `legacy_ref` 进入旧 Trial/Attempt 或 Warehouse。

机器身份由各框架的 `framework.yaml` 决定；正式框架之间不存在目录嵌套。
