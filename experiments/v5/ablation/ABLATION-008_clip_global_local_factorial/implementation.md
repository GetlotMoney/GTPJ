# 实现说明

最后修改可执行代码的提交（PARAMETER_MATRIX 的 `code_ref`）：`403ddaa2238672ef87f6ce34945df90b568d907e`。

`model/V5ScorePathAblation.py` 提供三个实验专属对象，完整路径直接返回母版 `GTPJ`。G/L 先在 CPU 用同一种子构造 canonical donor，再按名称和形状逐项复制共享状态；最终 G 不保留局部模块，最终 L 不保留 `logit_scale` 或 global logits。

`train_V5_ABLATION_008_CUB.py` 是 import-safe 独立入口。它要求显式 `--data-root`、`--data-manifest`、`--output-dir`、`--expected-run-commit`，并固定从入口所在仓库检查 clean Git 工作树和准确 HEAD；不允许静默回退 CPU。运行时的实际 HEAD 记为 `run_commit`，它与上面的 `code_ref` 分工不同，不要求相同。指标文件还记录入口与专属模型源码 SHA256、清单 SHA256、逐文件指纹和 seen/unseen 类别编号。

冻结路径只核对并读取 xlsa17、gpt55、测试 seen/unseen CLS 与标签，不读取或哈希训练缓存和测试 patch；它不创建 optimizer、scheduler、backward 或 checkpoint，四次运行只检查确定性。G 路径只核对、加载和传输训练/测试 CLS 与标签，不读取或哈希 patch；L/GL 才核对并读取真实 patch。数据清单由同一次 bytes 读取同时解析和计算 SHA256。所有路径在 argmax 前拒绝 NaN/Inf logits；最终日志写出 workflow 可解析的 Best Results 区块，指标与 best model 采用临时文件加原子替换，避免留下半文件。

L 路径损失为 CE(local)、topology、BMDD、MPP 和 negative；global-local consistency 因没有 global 教师而结构性不计算。未明确改动的母版配置值保持不变。
