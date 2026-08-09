# 老框架与最新代码差异

## 先说结论

新旧框架真正用于预测的主公式没有变，都是：

final = global + 0.2 × local

已有的 V5 等价性测试也证明，历史权重转换到最新模型后，评估分数、训练分数、损失和代表性梯度能在数值容差内对齐。因此，当前 0.07 到 0.13 H 的差异不像是“最新代码把模型公式改坏了”。

目前最值得怀疑的是随机数轨迹：老代码会先初始化几组后来没有参与前向计算的参数，这些参数虽然不直接预测，却会消耗随机数，使后面真正使用的层从不同随机初值开始，也会影响训练时 randperm 产生的批次顺序。

## 具体差异

| 对比项 | 老框架 | 最新代码 | 对这次结果的含义 |
|---|---|---|---|
| 最终融合 | s_global + local_weight × s_local，local_weight=0.2 | global_logits + 0.2 × local_logits | 有效公式相同，不是主要差异 |
| 核心配置 | PSE outer=0.65，local weight=0.2，ICSA=0.008，三段共 50 epoch | 完整基线使用相同核心值；新增局部损失都固定为 0 | 核心超参数相同 |
| 多余参数 | 包含 proj_visual、proj_text、gate_alpha、gate_tau，但不参与当前前向 | 已删除 | 会改变同 seed 后续随机初始化和批次随机数 |
| 参数规模 | 总参数 15,033,751；可训练 13,804,951 | 总参数 13,976,981；可训练 13,016,981 | 老代码多 787,970 个可训练参数，主要是未使用投影层 |
| 数据加载 | 旧 CUBDataLoader 支持多条兜底路线 | 直接核验固定 cache，缺输入就停止 | 本次旧运行实际读到完整 CLS+patch，兜底路线不是这次差异来源 |
| 结果保存 | 旧式日志和 pth，没有数据清单与输出防覆盖 | 有数据身份清单、原子写入和不覆盖检查 | 影响可复现证据和安全性，不改变模型数学 |
| 确定性 | strict_determinism=false | strict_determinism=false | 同 seed 不是逐位相同，GPU 小波动仍会放大 |

## 已直接看到的随机初始化差异

用同一 seed 构造新旧小模型并转换同名权重时，旧代码独有的 proj_visual、proj_text、gate_alpha、gate_tau 被丢弃；同时真正参与训练的以下六个张量已经不同：

- sgmp_predictor.0.weight / bias
- sgmp_predictor.3.weight / bias
- icsa_module.0.weight / bias

这证明“seed 数字相同”不等于“真实初始模型相同”。它是目前最合理的解释，但仍只是待验证原因，不能直接写成已经证明的因果结论。

## 已完成的机器核对

- 历史提交 4b259379 与正式 v5 Tag 在 model/MyModel.py、train_GTPJ_CUB.py、tools/dataset.py、tools/reproducibility.py 上零差异。
- 目标测试 tests.test_v5_template_contract 共 7 项通过，其中包含历史权重转换后的 clean-path 数值等价检查。
- 老模型到最新模型的源码清理规模很大：model/MyModel.py 约 902 行变化，训练入口约 1431 行变化；大部分是删除旧分支和加入安全检查，不能只看行数判断模型变了。

## 推荐的最小下一步

保留最新入口的数据核验、评估和不覆盖能力，只对齐老框架的初始化与训练随机数轨迹。这样只改变一个变量，能直接回答分数差异是不是来自随机初值；不要同时再调 local weight、loss 或学习率。
