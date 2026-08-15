# GTPJ 正式框架树

```text
main（公共底座，默认冻结）
└─ FRAMEWORK-V1  [framework/v1 = tag v1]
   └─ FRAMEWORK-V2  [framework/v2 = tag v2]
      └─ FRAMEWORK-V3  [framework/v3 = tag v3]
         └─ FRAMEWORK-V5  [framework/v5 = tag v5]
```

树的位置回答“代码从哪里继承”；正式框架名回答“以后能从哪里直接开实验”。因此 V2 虽然继承 V1，但晋级后就是一个直接入口，后续实验从 `framework/v2` 开，不需要再经过 V1。

## 每个框架固定四类实验

| 正式框架 | 调参 | 消融 | 创新 | 确认 |
|---|---|---|---|---|
| `FRAMEWORK-V1` | 0 | 0 | `V1-INNOVATION-001`，历史形成 V2 | `V1-CONFIRM-001` |
| `FRAMEWORK-V2` | 0 | 0 | `V2-INNOVATION-001`，历史形成 V3 | 0 |
| `FRAMEWORK-V3` | `V3-TUNE-001` | 0 | `V3-INNOVATION-001`，历史形成 V5 | `V3-CONFIRM-001` |
| `FRAMEWORK-V5` | `V5-TUNE-001` | `V5-ABLATION-001` | `V5-INNOVATION-001` | 0 |

## 晋级示例

```text
framework/v1
└─ exp/v1/innovation/innovation-xxx-candidate-v2
   └─ owner 确认后，在候选最终 commit 建 framework/v2 与 v2
```

原候选仍留在 V1 的 innovation 账本作为来源证据；新实验改从 V2 开。晋级不复制代码、不改写历史，也不把候选合回 V1。

## 查看顺序

1. 本文件看真实框架血缘。
2. 打开 `experiments/vX/EXPERIMENTS.md` 看该框架四类实验。
3. 打开 `experiments/vX/TEMPLATE.yaml` 确认唯一框架 commit。
4. 打开具体实验的 `PARAMETER_MATRIX.md` 看每一行参数和结果。
5. 需要旧证据时，再跟随 `legacy_ref` 进入旧 Trial/Attempt 或 Warehouse。

机器身份由各框架的 `framework.yaml` 决定；Git 提交祖先关系必须与 `derived_from_framework` 一致。
