# PSE 关闭方式

- 关闭模块：PSE（渐进语义增强）。
- 代码入口：`train_GTPJ_CUB.py` 读取 `ablation_disable_pse=true`，`model/MyModel.py` 据此设置 `pse_enabled=false`。
- 旁路后的数据流：不创建也不调用 PSE；seen 类文本直接取句子向量平均后归一化。
- 依赖损失：关闭 PSE 后，topology 只读取 `requires_grad=False` 的固定文本，因此设置 `lambda_topo_pearson=0`，不把无训练梯度的常数计入总损失。
- 保持不变：ICSA、FGVD、BVSA、SGMP、局部融合、CE、consistency、BMDD、MPP、negative、数据划分、类别顺序、训练轮数和评估公式。
- 验收测试：`tests/test_v5_pse_ablation.py` 检查 PSE 参数不存在、topology loss 为 0、ICSA/BVSA/SGMP 仍有非零梯度，并核对两种子双重复的四份配置。
