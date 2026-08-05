# GTPJ 正式框架树

```text
FRAMEWORK-V1  [framework/v1, tag v1]
├─ 调参 0
├─ 消融 0
├─ 确认 V1-CONFIRM-001
└─ 创新 V1-INNOVATION-001
   └─ FRAMEWORK-V2  [历史 owner 接纳，未按新规确认]
      └─ 创新 V2-INNOVATION-001
         └─ FRAMEWORK-V3  [历史 owner 接纳，未按新规确认]
            ├─ 调参 V3-TUNE-001
            │  └─ v4 历史 config-only 标签（不是框架）
            ├─ 确认 V3-CONFIRM-001
            └─ 创新 V3-INNOVATION-001
               └─ FRAMEWORK-V5  [历史 owner 激活]
                  ├─ 调参 V5-TUNE-001：动态路由，已恢复 8 个真实任务
                  ├─ 消融 V5-ABLATION-001：局部分支效果，planned
                  └─ 创新 V5-INNOVATION-001：动态路由，candidate
```

## 当前结论

- 当前模型框架：`MODEL-GTPJ-V5`，局部分支融合权重为 `local_weight=0.2`。
- 更强的已确认配置参考：`V3-CONFIRM-001`，`confirmed_H=74.47`。
- 动态路由最高单次 `H=75.11`，但精确复跑未还原，所以没有创建子框架。现已精确恢复 `ATTEMPT-006` 的 2 个创新探针和 8 个调参任务；其余批次只保留摘要映射，不猜参数。
- 局部分支消融已登记 15 个 `RUN`，当前全部未运行。

## 查看顺序

1. 本文件看父子关系。
2. 打开 `experiments/vX/EXPERIMENTS.md` 看该框架四类实验。
3. 打开具体实验的 `PARAMETER_MATRIX.md` 看每一行参数和结果。
4. 需要查旧证据时，再跟随 `legacy_ref` 进入旧 Trial/Attempt 或 Warehouse。

机器身份由各框架的 `framework.yaml` 决定；本页是人类总览。

上面的父子边保留真实历史沿革，不等于补签“已确认晋级”。今后新子框架必须由已确认、质量检查通过且状态为 `promoted` 的创新产生。
