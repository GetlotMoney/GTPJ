# V5-INNOVATION-011 结果

状态：`RUN-001` 单次有效运行完成；继续修改干净框架，不晋级 V6。

## 结果

| RUN | seed | best epoch | U | S | H | ZS | 决定 |
|---|---:|---:|---:|---:|---:|---:|---|
| `RUN-001` | 5 | 1 | 48.543394 | 82.624918 | 61.156447 | 76.156127 | `continue_clean_framework` |

`H=61.156447` 比 009/010 的判断线 `59.4058` 高 `1.7506`。这只说明当前准确实现的干净候选单次分数更高、值得继续修改；由于 011 与 009/010 不是只改变一个变量的严格配对消融，不能把差异单独归因于删除旧模块。它仍比 V5 重复均值 `74.44` 低 `13.2836`，也没有达到更强参考 `74.47`，因此不能直接晋级 V6。

## 运行身份

- 代码：`688f564fea25cc54912fc728d139eba9e98dcdd6`
- 配置 SHA-256：`3981ac12e40d9d33b8d65a5bcf8f95740a3563b8e09e092f423ab9dfc33980fc`
- 数据清单 SHA-256：`7b172e9a239aa494b0c7d7c9384b2274ed8c3ab6b79e3f47dbfc63530f34175a`
- Warehouse：`/data/lby/projects/cv_project/GTPJ_Warehouse/runs/v5/innovation/V5-INNOVATION-011/RUN-001`
- 日志 SHA-256：`142b213907c833971968d0c8e6455bba00d088c89f6b9111006700fa4b48c5da`
- 最佳模型 SHA-256：`cdca8e7769f405e588a5da954012d7a849ddb83ad2b4bcda64f0a385beb02b6f`
- 完整 checkpoint SHA-256：`ee8bb85d99cb716f3b7622bc874c586317b5ba5f58403350e024ff8cb17fc5db`
- 最终指标 SHA-256：`c5dcecae780b4c6aeed6987f9fcf07c8a86da90796cff6bd7b0fa1e5729dc393`

## 证据边界

本次训练满足当前五步短流程固定的科学边界：准确提交、配置、数据/划分、seed、评估口径、完整 U/S/H/ZS 和不覆盖历史。训练启动时没有调用旧 helper 生成开跑前收据；`evidence/RUN-001_POST_RUN_EXECUTION.json` 是训练后核对记录，不冒充启动收据。本结果是 `valid_single_run`，同时保持 `not_confirmation_evidence: true`，不能用于 baseline、confirmation、promotion 或 V6 晋级。
