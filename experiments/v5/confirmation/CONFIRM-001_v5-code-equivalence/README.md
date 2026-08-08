# V5-CONFIRM-001：老 V5 与今天代码等价性确认

## 这次要回答什么

今天的 V5 模板代码能否在相同服务器、相同数据、相同 `seed=5` 和相同历史配置下，重新达到老 V5 的 `H=74.44` 水平；同时把历史动态路由 `DR-095` 的 `H=75.11` 再跑五次，确认它是否还能出现。

## 三组代码

| 组别 | 代码 | 配置 | 次数 | 证据用途 |
|---|---|---|---:|---|
| 老 V5 | `4b259379d99c1a791442ea9e2fac0bb22b2411a9` | `configs/V5-069.yaml` | 5 | 历史代码诊断；不冒充新母版正式结果 |
| 今天模板 | 本实验运行前冻结提交；训练相关文件与 `66302091...` 完全相同 | `configs/CURRENT-V5.yaml` | 5 | 本实验正式确认组 |
| 动态路由 75.11 | `a884fea429a302fecc42ba8cddf9e6e66f5d07c8` | `configs/DR-095.yaml` | 5 | 历史创新候选诊断；不自动晋级框架 |

老代码使用原始配置文件；今天代码使用它能够接受的瘦身配置。`CONFIG_EQUIVALENCE.md` 和自动测试逐项证明：今天配置保留了老配置中所有真正参与当前计算的值，只删除旧别名、显式开关和旧兼容字段。两张 GPU 对每一组都按 3 次和 2 次交叉分配，避免某组只在一张卡上运行。

## 判定规则

- 老 V5 目标：`H >= 74.44`；`74.24 <= H < 74.44` 只算接近，不能写成严格还原。
- 今天模板目标：`H >= 74.44`；是否存在迁移偏差以老 V5 与今天模板五次分布的直接比较为准。
- 动态路由目标：`H >= 75.11`；`74.91 <= H < 75.11` 只算接近。
- Owner 已明确要求三组全部跑完五次，因此本轮不在单次命中后提前停止；这项决定写入 `RUN_PLAN.json`。

## 为什么历史组不写进正式参数表

新规范要求正式实验从 `MODEL-V5-TEMPLATE-V1` 独立开始，不能把旧提交伪装成新母版。于是：

- `PARAMETER_MATRIX.csv` 只登记今天模板的五次正式运行；
- `evidence/DIAGNOSTIC_MATRIX.csv` 登记老 V5 和动态路由十次历史代码诊断；
- 三组仍由同一个服务器控制器统一锁定代码、配置、GPU、日志和收据，最终可以直接比较。

## 固定身份

```text
experiment_id: V5-CONFIRM-001
kind: confirmation
version: v5
base_template_id: MODEL-V5-TEMPLATE-V1
base_template_tag: model/v5-template-v1
base_template_commit: 2f5fa5e631ef82658d4bac587cdfd17f3534cb35
code_branch: exp/v5/confirmation/confirm-001-v5-code-equivalence
workflow_mode: server_frozen_runner
seed: 5
dataset_split: xlsa17 standard CUB GZSL
metric: U / S / H / ZS
evidence_level: pending
result_status: pre_run
```

## 运行与证据位置

- 人看的运行计划：`RUN_PLAN.json`。
- 新旧配置映射：`CONFIG_EQUIVALENCE.md`。
- 正式参数表：`PARAMETER_MATRIX.csv`。
- 历史诊断表：`evidence/DIAGNOSTIC_MATRIX.csv`。
- 数据身份：`DATA_MANIFEST.json`。
- 原始日志、模型和收据：服务器 `GTPJ_Warehouse/runs/v5/confirmation/`。
- Git 只登记结果摘要、路径、SHA-256 和文件大小，不保存原始日志或模型。

## 当前状态

运行前冻结和审核中；尚无新指标，不能提前声称今天代码已还原老 V5。
