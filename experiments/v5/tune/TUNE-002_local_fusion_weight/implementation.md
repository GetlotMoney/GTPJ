# 实现说明

## 本次只改什么

1. `model/MyModel.py` 从配置读取有限且位于 `[0,1]` 的 `local_weight`。
2. 最终分数使用 `global_logits + local_weight * local_logits`。
3. 正式训练入口只接受 `0.05、0.10、0.30、0.40`，并继续要求 `score_mode=add`。
4. 类别身份张量固定在 CPU 构造，避免母版已有的 CUDA 构造问题。

## 明确不改什么

forward 的其他计算、全部 loss、模型模块、数据划分、类别顺序、评估口径和训练循环均不改变。`local_weight=0.2` 时，专项测试会从母版提交独立加载模型，逐项比较 forward、loss 和梯度。

实现代码固定为 `3af9bfa8247b7aa6bc4ba4b5aa6c69f35277cd28`。当前审核状态为 `strict-3 / review_pending`，尚未形成正式运行许可或性能结论。
