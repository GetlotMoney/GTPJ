# PSE 与 ICSA 联合关闭方式

- 关闭模块：PSE、ICSA，以及 PSE 关闭后失去梯度作用的 topology 损失。
- 入口：配置同时设置 `ablation_disable_pse=true` 与 `ablation_disable_icsa=true`，训练入口拒绝其他组合。
- 旁路：不创建、不调用两个模块；seen 文本改用句向量均值归一化，类别文本不再加入图像条件偏移。
- topology 边界：`lambda_topo_pearson=0.0`；它原本只比较 PSE 适配前后的文本，PSE 关闭后不再对参数产生梯度，本实验不发明新的作用对象。
- 不变项：FGVD、BVSA、SGMP、局部融合、CE、consistency、BMDD、MPP、negative semantic、数据划分、类别顺序、训练轮数和评估公式。
- 验收：`tests/test_v5_pse_icsa_interaction.py` 检查模块参数、文本旁路、topology 为零、BVSA/SGMP 梯度、输出字段、类别轴及四次运行账本。
