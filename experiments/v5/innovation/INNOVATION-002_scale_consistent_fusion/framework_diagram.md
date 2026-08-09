# 框架图：尺度一致的局部融合

这张图只强调本实验改动的最后一步。图像、文本和局部分支内部结构全部继承自 V5；红色含义由文字中的 `scale_consistent` 路线承担，不把继承模块包装成新模块。

```mermaid
flowchart LR
    A["图像与类别文本"] --> B["V5 冻结母版特征路径"]
    B --> G["global_logits<br/>全局余弦 × logit_scale"]
    B --> L["local_logits<br/>BVSA 局部余弦"]
    C["fusion_mode"] --> F{"选择融合公式"}
    T["logit_scale<br/>clamp(exp(raw), max=100)"] --> F
    G --> F
    L --> F
    F -->|legacy| O1["global + 0.2 × local"]
    F -->|scale_consistent| O2["global + 0.05 × logit_scale × local"]
    O1 --> E["训练：只取 seen 类<br/>评估：保留完整类别"]
    O2 --> E
    E --> M["U / S / H / ZS"]
```

## 读图顺序

1. V5 母版先产生全局分数和局部分数。
2. `fusion_mode` 决定走原公式还是尺度一致公式。
3. 两条路线之外的训练与评估流程完全相同。
4. 最终只比较 U、S、H、ZS 和预先写死的 Stage1 门槛。

同一张图的本地独立页面见 `framework_diagram.html`。
