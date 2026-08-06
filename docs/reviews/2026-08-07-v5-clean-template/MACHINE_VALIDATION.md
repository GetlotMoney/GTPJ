# 机器验证记录

## 已完成

- 稳定环境：`C:\Users\Administrator\AppData\Local\Programs\Python\Python310\python.exe`，Python 3.10.9，PyTorch 2.10.0+cpu。
- 命令：`python -m unittest tests.test_v5_template_contract tests.test_v5_checkpoint_converter tests.test_fae_memory_jepa -v`。
- 第一轮结果：25 项全部通过，无底层访问异常。
- 历史对齐：从真实 `v5:model/MyModel.py` 建立历史模型，经正式转换函数和干净母版目标清单转换后 `strict=True` 加载；评估/训练的最终、全局、局部分数，7 项损失，以及 PSE、BVSA、ICSA、SGMP 关键梯度在 `rtol=1e-5、atol=1e-6` 下对齐。
- 评估语义：执行真实评估函数，覆盖非连续全局类别编号、seen/unseen 列、unseen-only ZS 和调和平均数 H。
- 输入边界：577-token 正路径通过；576-token、1-token、二维输入和错误特征维度均被拒绝。
- 转换边界：未知后缀、错误形状、缺目标字段、字段冲突、既有输出和重复路径均被拒绝；冲突失败收据存在且输出不存在。
- 静态验证：相关 Python 文件 `py_compile` 通过，`git diff --check` 通过。

## 全工作流验证

- `python -m unittest tests.test_gtpj_workflow -q`：251 项全部通过，用时 175.743 秒。
- `python -m unittest tests.test_reproducibility -v`：3 项全部通过。
- `validate`：通过。
- `validate-framework-templates`：通过。
- `validate-framework-ledgers`：通过。
- `validate-workflow-consistency`：通过。
- `audit-boundary`：通过。
- 四份 V5 配置 SHA-256 完全一致。
- `experiments/module_trials` 在治理起点和当前工作树的 Git 子树均为 `6e858397607f42c6c4b3ac870e24909e2aae14aa`，历史实验未改。
- `pyflakes`：模型、训练、评估和转换器无未使用 import/局部变量报告。

## 第二轮阻断修复后的直接验证

- V5 合同、转换器、数学路径和复现测试合并运行：33 项全部通过。
- 新增连续训练/中断续训测试：同时使用 `torch.randperm`、Dropout、Python `random` 和 NumPy 随机数；恢复后 3 个 step 的 loss 与全部参数逐位一致。
- 新增身份拒绝测试：代码 commit、配置哈希、输入缓存指纹或 seenclasses 改变时均拒绝续训。
- 新增并发替换测试：收据写入失败前用另一份内容替换输出路径，转换器抛错后并发者内容仍原样存在。
- 新增类别边界测试：seen/unseen 重复、重叠或漏类都会被模型拒绝。
- 修复提交 `440cfc0` 上再次运行 `tests.test_gtpj_workflow`：251 项全部通过，用时 177.690 秒。
- 同一提交上再次运行 `validate`、母版、实验账本、工作流一致性和边界检查：5 项全部通过。

## 第三轮边界修复后的直接验证

- 修复提交：`1233ca9cc52df027f130e216cc18e16b1d5c731c`。
- V5 合同、转换器、数学路径和复现测试合并运行：36 项全部通过，用时 1.393 秒。
- 新增输入加载竞态测试：文件在读入内存后被替换时，加载前后指纹核对会拒绝继续。
- 新增最小 xlsa17 划分测试：只读取两个 `.mat` 文件，正确返回 seen/unseen 类别，并在缓存标签顺序错误时停止。
- 中断恢复测试新增学习率调度器状态，并逐 step 比较 loss、全部参数快照和学习率，全部逐位一致。
- Torch CPU/CUDA RNG 状态在恢复前转回 CPU 的源码合同测试通过；当前稳定环境为 CPU 版 PyTorch，尚未执行真实 CUDA 恢复。
- 同一提交运行 `tests.test_gtpj_workflow`：251 项全部通过，用时 176.665 秒。
- 同一提交运行 `validate`、母版、实验账本、工作流一致性和边界检查：5 项全部通过；`py_compile`、`pyflakes` 和 `git diff --check` 通过。

## 尚未完成

- 原三名独立审核人对第三轮边界修复的最终复审。
- 服务器正式 U/S/H/ZS 训练与评估：未获当前授权，不运行。
