# 实现记录

## 母版和改动边界

- 母版：`MODEL-V5-TEMPLATE-V1`；
- 母版提交：`2f5fa5e631ef82658d4bac587cdfd17f3534cb35`；
- 实验分支：`exp/v5/ablation/ablation-001-local-branch-effect`；
- 冻结母版工作区未修改；所有实验代码只存在于独立实验分支。

## 删除内容

新增的 `model/V5GlobalOnly.py` 不定义或实例化 FGVD、BVSA、SGMP；前向计算不生成局部分数，最终分数就是全局分数。它的 `compute_loss` 不计算 consistency、BMDD、MPP 和 negative semantic 损失。

新增的 `train_V5_ABLATION_001_CUB.py` 只导入这个专属模型。没有增加 `use_xxx` 开关，也没有让第二个实验继续修改第一个实验。母版的 `model/MyModel.py`、`train_GTPJ_CUB.py` 和四份正式 V5 配置与冻结 Tag 逐字一致。

## 保留内容

- PSE 的实现、层数和参数量保持母版一致；
- ICSA 的实现和参数量保持母版一致；
- 全局 `logit_scale`、类别顺序、seen/unseen 映射和输出维度保持一致；
- CE 与 topology 损失保持一致；
- 训练仍加载同一份 CLS 和局部块缓存，无局部模型只读取 CLS，避免换数据入口带来干扰。

## 参数量

| 版本 | 总参数 | 可训练参数 | PSE | ICSA |
|---|---:|---:|---:|---:|
| 完整 V5 | 13,400,981 | 13,016,981 | 2,954,496 | 74,640 |
| 干净无局部 | 3,413,137 | 3,029,137 | 2,954,496 | 74,640 |

减少可训练参数 9,987,844，即 76.73%。减少量对应完整 V5 中 BVSA/FGVD 与 SGMP 的参数，不包含 PSE 和 ICSA。

## 已知随机性边界

同一 seed 能锁定每个版本自己的初始化和采样，但删除大量模块后，PyTorch 随机数的消耗顺序必然变化，因此不能假设两组每一层初始权重逐元素相同。三个配对 seed 用来降低这种训练噪声；若最终差值很小，会把“差值低于随机波动”作为结论边界，而不是强行说局部分支有效或无效。
