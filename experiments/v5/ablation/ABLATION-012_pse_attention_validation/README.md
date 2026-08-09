# V5-ABLATION-012：PSE 注意力机制验证

这次只回答两个问题，不改 PSE 的其余结构。

1. `PSE-UNIFORM`：把注意力固定成每个句子都是 `1/M`，但保留 V 投影、输出投影、两层残差、LayerNorm 和原有 dropout。它用来判断学出来的 Q/K 是否真的有贡献。
2. `PSE-NO-QK-DECAY`：保持原来的 learned attention，只取消 Adam 对 PSE 中 Q/K 切片的 `weight_decay`。它用来判断 Q/K 清零是不是优化器衰减造成的。

每项使用 seed 5、17，每个 seed 由独立 Python 进程复跑 2 次，共 8 次。当前完整 V5 基线直接复用 `V5-ABLATION-008` 的 `GL-FULL` 四次同种子结果，不重复浪费 GPU。

每个 RUN 必须保存 `training.log`、`result.yaml` 和最佳模型，并记录训练前后的 Q/K/V 范数、注意力熵和最大注意力权重。结果只用于判断 PSE 机制，不作为正式版本确认结果。
