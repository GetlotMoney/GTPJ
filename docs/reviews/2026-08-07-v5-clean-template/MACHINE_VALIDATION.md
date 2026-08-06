# V5 干净母版机器验证

稳定环境：`C:\Users\Administrator\AppData\Local\Programs\Python\Python310\python.exe`，Python 3.10.9，PyTorch 2.10.0+cpu。

| 验证 | 结果 |
|---|---|
| V5 合同、转换、数学与复现测试 | 36 项全部通过 |
| 总工作流回归 | 251 项全部通过，母版代码主执行用时 176.665 秒 |
| `validate` | 通过 |
| `validate-framework-templates` | 通过 |
| `validate-framework-ledgers` | 通过 |
| `validate-workflow-consistency` | 通过 |
| `audit-boundary` | 通过 |
| `py_compile`、`pyflakes`、`git diff --check` | 通过 |

历史对齐覆盖：真实 `v5:model/MyModel.py` 权重经独立转换工具严格载入新母版；评估/训练的最终、全局、局部分数，7 项损失和 PSE、BVSA、ICSA、SGMP 关键梯度在 `rtol=1e-5、atol=1e-6` 下对齐。受控 logits 验证了非连续全局类别编号下的 U/S/H/ZS 含义。

复现边界覆盖：输入加载前后双指纹、类别划分逐标签核对、代码/配置/缓存/类别身份拒绝、Python/NumPy/Torch RNG 恢复，以及中断后逐 step loss、全部参数和学习率零差异。

母版分支 `framework/v5-template-v1` 与 Tag `model/v5-template-v1` 均解析到 `2f5fa5e631ef82658d4bac587cdfd17f3534cb35`；旧 `v5` Tag 仍解析到 `08e5ecb1a5db6c6d589527cda35d8d4f7f437e07`。

写入 `MODEL-V5-TEMPLATE-V1 / frozen` 登记后，治理工作树再次运行 251 项工作流测试，全部通过，用时 159.340 秒；5 个结构与边界检查全部通过。

重新绑定 `V5-ABLATION-001` 并重算 15 行计划后，再次运行 251 项工作流测试，全部通过，用时 160.753 秒；参数矩阵解析、查重和 JSON 字段检查无错误，5 个结构与边界检查全部通过。

登记内容进入独立实验分支后，36 项 V5 专项测试全部通过，用时 1.272 秒；251 项工作流测试全部通过，用时 160.451 秒；`validate-experiment-base` 明确确认当前分支名、母版 Tag/commit、registry 提交和实验绑定一致。实验分支本地 `TEMPLATE.yaml` 保持母版提交原样，不把总管理登记反写进实验分支。

当前本地环境没有正式 CUB 服务器缓存和可用 CUDA；这些验证不等同于服务器精度复跑或真实多 GPU checkpoint 恢复。
