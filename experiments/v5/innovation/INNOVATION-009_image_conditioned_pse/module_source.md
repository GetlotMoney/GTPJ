# 模块来源：图像条件 PSE 句子选择

```yaml
idea_id: IDEA-0011
source_type: user
source_status: local_heuristic
template_family: feature_adapter
attachment_point: model/MyModel.py::GTPJ.forward，PSE输出到global_logits之前
baseline_off: interaction_mode=v5_baseline
```

最小真实问题是 V5 的 ICSA 对同一图片只产生一个向量，并把它加到所有已见类别；它不能表达“这张鸟图更像某个类别的喙描述，而不是尾巴描述”。本实验用 CLS 与每类 8 句做余弦匹配，Softmax 后加权原始 PSE 增强句子。

句权均匀时，`mean(r*PSE(sentence)+(1-r)*sentence)` 与原 PSE 先增强再平均严格一致；加权 value 不逐句重新归一化，避免悄悄改变基线。
