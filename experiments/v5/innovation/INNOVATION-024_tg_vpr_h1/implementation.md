# 实现说明

- 输入文本：`[200, 8, 768]`。
- 物理槽位：前六个局部、第7个整体、第8个独特。
- 逻辑顺序：`local / unique / global`。
- Value路径：1 head，完整768维；无Q/K。
- 内层残差：`0.35 × context + 0.65 × group`。
- 外层残差：`0.35 × base + 0.65 × transformed groups`。
- 训练：7,057张seen图像、固定50 epoch、CE加0.1 topology。
- 推理：U/S/H在200类竞争，ZS在50个unseen类竞争。
