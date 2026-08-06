# Version Registry

## 正式框架同级注册表（DATA-FRAMEWORK-LEDGER-V2）

```text
FRAMEWORK-V1  [tag v1]  derived_from: none
FRAMEWORK-V2  [tag v2]  derived_from: FRAMEWORK-V1
FRAMEWORK-V3  [tag v3]  derived_from: FRAMEWORK-V2
FRAMEWORK-V5  [tag v5]  derived_from: FRAMEWORK-V3
```

以上四个框架全部同级。`derived_from` 是历史来源指针，不是父子层级。

正式框架的人类实验全貌以各自 `EXPERIMENTS.md` 为准。普通调参、消融、确认和未晋级创新不进入本注册表，也不能创建正式 Tag。

## 历史来源表

| 正式框架 | 来源框架 | 正式 Tag | 来源实验或历史记录 | 变化类型 | 说明 |
|---|---|---|---|---|---|
| `FRAMEWORK-V1` | none | `v1` | initial | initial | 第一套正式框架。 |
| `FRAMEWORK-V2` | `FRAMEWORK-V1` | `v2` | `V1-INNOVATION-001` | add_module | CLIP-A-self 文本原型适配；历史接纳，未按新规范补签确认。 |
| `FRAMEWORK-V3` | `FRAMEWORK-V2` | `v3` | `V2-INNOVATION-001` | add_module | 严格条件 FAE-memory JEPA；历史接纳，未按新规范补签确认。 |
| `FRAMEWORK-V5` | `FRAMEWORK-V3` | `v5` | `V3-INNOVATION-001` | combo | 条件 BVSA 文本正式框架；历史 owner 激活。 |

## 历史特例

`v4` Tag 来自 V3 的纯调参确认，是历史误分类，不是正式框架。它继续保留用于复现，但不进入上面的正式框架注册表。

## 新正式框架登记模板

```text
| `FRAMEWORK-VX` | `FRAMEWORK-VSOURCE` | `vX` | `VSOURCE-INNOVATION-xxx` | add_module / replace_module / architecture_change / combo | short note |
```

同时更新：

- `experiments/vX/framework.yaml`
- `experiments/vX/VERSION.md`
- `experiments/vX/EXPERIMENTS.md`
- `experiments/EXPERIMENT_REGISTRY.md`
- `config/versions/vX.yaml`
- `docs/PROJECT_STATUS.md`
