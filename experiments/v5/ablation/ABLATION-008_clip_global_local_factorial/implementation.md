# 实现说明

代码提交：`afef64489cf2dfe26be3574b362ec2fa97703995`。

`model/V5ScorePathAblation.py` 提供三个实验专属对象，完整路径直接返回母版 `GTPJ`。G/L 先在 CPU 用同一种子构造 canonical donor，再按名称和形状逐项复制共享状态；最终 G 不保留局部模块，最终 L 不保留 `logit_scale` 或 global logits。

`train_V5_ABLATION_008_CUB.py` 是 import-safe 独立入口。它要求显式 data/output 目录、clean Git 工作树和 CUDA。冻结路径不读取训练 CLS、patch、label，不创建 optimizer、scheduler、backward 或 checkpoint；其四次运行只检查确定性。

L 路径损失为 CE(local)、topology、BMDD、MPP 和 negative；global-local consistency 因没有 global 教师而结构性不计算。未明确改动的母版配置值保持不变。
