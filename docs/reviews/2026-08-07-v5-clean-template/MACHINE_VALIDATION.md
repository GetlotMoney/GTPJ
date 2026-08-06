# V5 干净母版机器验证

稳定环境：`C:\Users\Administrator\AppData\Local\Programs\Python\Python310\python.exe`，Python 3.10.9，PyTorch 2.10.0+cpu。

| 验证 | 结果 |
|---|---|
| V5 合同、转换、数学与复现测试 | 36 项全部通过 |
| 总工作流回归 | 251 项全部通过，主执行用时 176.665 秒 |
| `validate` | 通过 |
| `validate-framework-templates` | 通过 |
| `validate-framework-ledgers` | 通过 |
| `validate-workflow-consistency` | 通过 |
| `audit-boundary` | 通过 |
| `py_compile`、`pyflakes`、`git diff --check` | 通过 |

额外核对：母版分支 `framework/v5-template-v1` 与 Tag `model/v5-template-v1` 均解析到 `2f5fa5e631ef82658d4bac587cdfd17f3534cb35`；旧 `v5` Tag 仍解析到 `08e5ecb1a5db6c6d589527cda35d8d4f7f437e07`。

写入 `MODEL-V5-TEMPLATE-V1 / frozen` 登记后，治理工作树再次运行 251 项工作流测试，全部通过，用时 159.340 秒；随后 5 个结构与边界检查全部通过。

这些验证证明本地代码与治理边界通过，不等同于服务器精度复跑。
