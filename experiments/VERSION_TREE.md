# Version Tree

## 当前正式框架血缘（DATA-FRAMEWORK-TREE-V3）

```text
main（公共底座）
└─ FRAMEWORK-V1  [framework/v1, tag v1]
   └─ FRAMEWORK-V2  [framework/v2, tag v2]
      └─ FRAMEWORK-V3  [framework/v3, tag v3]
         └─ FRAMEWORK-V5  [framework/v5, tag v5]
```

这是一棵真实继承树：V2 的正式 commit 继承 V1，V3 继承 V2，V5 继承 V3。每个已经确认的框架又都是 GitHub 分支列表中的直接入口，可以独立作为新实验起点。

## 当前登记

| 正式框架 | 直接来源 | 正式 Tag | 来源实验或历史记录 | 变化类型 | 说明 |
|---|---|---|---|---|---|
| `FRAMEWORK-V1` | `none` | `v1` | initial | initial | 第一套历史正式框架。 |
| `FRAMEWORK-V2` | `FRAMEWORK-V1` | `v2` | `V1-INNOVATION-001` | add_module | CLIP-A-self 文本原型适配；历史接纳。 |
| `FRAMEWORK-V3` | `FRAMEWORK-V2` | `v3` | `V2-INNOVATION-001` | add_module | 严格条件 FAE-memory JEPA；历史接纳。 |
| `FRAMEWORK-V5` | `FRAMEWORK-V3` | `v5` | `V3-INNOVATION-001` | combo | 条件 BVSA 文本框架；历史 owner 激活。 |

`v4` 是历史 config-only Tag，不是正式框架，继续保留用于复现。

## 新节点怎样接入

继承现有框架：

```text
FRAMEWORK-V2 -> 候选实验 -> owner 确认 -> FRAMEWORK-V6
```

新 `framework/v6` 与 `v6` 指向候选最终 commit；`derived_from_framework` 记录 `FRAMEWORK-V2`。以后从 V6 开的新实验直接从 `framework/v6` 分叉，不再回到 V2 下面继续叠。

完全独立：

```text
main -> 独立候选 -> owner 确认 -> FRAMEWORK-VX
```

此时登记 `derived_from_framework: main` 和实际 `derived_from_commit`。候选阶段不能预占正式编号、分支或 Tag。

## 登记时同步

- `experiments/vX/framework.yaml`
- `experiments/vX/TEMPLATE.yaml`
- `experiments/vX/VERSION.md`
- `experiments/vX/EXPERIMENTS.md`
- tune、ablation、innovation、confirmation 四张索引
- `experiments/EXPERIMENT_REGISTRY.md`
- `docs/PROJECT_STATUS.md`

详细规则见 `docs/workflow/FRAMEWORK_EXPERIMENT_STANDARD.md`。
