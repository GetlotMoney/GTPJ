# ICSA 关闭方式

- 关闭模块：ICSA（图像条件语义调整）。
- 代码入口：`train_GTPJ_CUB.py` 读取 `ablation_disable_icsa=true`，`model/MyModel.py` 据此设置 `icsa_enabled=false`。
- 旁路后的数据流：不创建也不调用 ICSA；类别文本不再加入由图像 CLS 生成的偏移，直接进入全局与局部打分。
- 保持不变：PSE、FGVD、BVSA、SGMP、局部融合、损失、数据划分、类别顺序、训练轮数和评估公式。
- 验收测试：`tests/test_v5_icsa_ablation.py` 检查 ICSA 参数不存在、条件文本不被改写、训练入口接受开关，并核对两种子双重复的四份配置。
