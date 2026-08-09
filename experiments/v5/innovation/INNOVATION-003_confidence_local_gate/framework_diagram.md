# Framework Diagram：低置信度局部增强

这里的 `Framework Diagram` 是本创新的前向路径图。它只解释新增 gate 如何接在 V5 母版后面，不把实验候选画成新的正式框架。

```mermaid
flowchart LR
    X["577-token CLIP 特征"] --> B["冻结母版 GTPJ.forward"]
    B --> G["global_logits：B×200"]
    B --> L["local_logits：B×200"]
    B --> A["原有辅助损失输入"]
    G --> S{"训练还是评估"}
    S -->|"训练"| ST["只取 seen 类全局分数"]
    S -->|"评估"| EV["取完整 200 类全局分数"]
    ST --> M["top1-top2 margin；detach"]
    EV --> M
    M --> Q["gate=sigmoid(bias-softplus(slope_raw)×margin)"]
    G --> F["final=global+0.05×logit_scale×gate×local"]
    L --> F
    Q --> F
    F --> O["训练：seen 类 logits；评估：200 类 logits"]
    A --> C["母版 compute_loss 原样读取"]
    O --> C
```

## 代码位置

| 路径 | 输入 | 输出 | 不变边界 |
|---|---|---|---|
| `confidence_local_gate.py::_compute_confidence_gate` | 全局分数、训练/评估标志 | gate、已 detach 的 margin | 不读标签，不改类别顺序 |
| `confidence_local_gate.py::forward` | 母版输出 | 新 final/logits/clip_S_pp 与 gate 统计 | 原有辅助张量全部保留 |
| `train.py::_evaluate_with_gate_stats` | 原评估 helper 与模型 | 原 U/S/H/ZS 加 gate 汇总 | 仍调用 `evaluate_cached_v5` |
