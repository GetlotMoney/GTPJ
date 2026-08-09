# Framework Diagram：图像条件 PSE

本图说明实验 A 的张量流和隔离边界。可直接打开的本地版本是 `framework_diagram.html`。

```mermaid
flowchart TB
  S["固定8句 [C,8,D]"] --> P["PSE逐句增强 [C,8,D]"]
  P --> AVG["均匀原型 [C,D]"]
  CLS["全局CLS [B,D]"] --> MATCH["余弦×CLIP尺度 [B,C,8]"]
  P --> MATCH --> SW["Softmax句权 [B,C,8]"] --> CP["条件原型 [B,C,D]"]
  CLS --> GL["global logits [B,C]"]
  CP --> GL
  PATCH["局部块 [B,576,D]"] --> TOPK["FGVD Top-K [B,32,D]"] --> BVSA["原BVSA"] --> LL["local logits [B,C]"]
  AVG --> BVSA
  GL --> FINAL["final = global + 0.2×local"]
  LL --> FINAL --> LOSS["原V5损失与U/S/H/ZS"]
  BASE["母版拓扑输入<br/>seen=PSE均值，unseen=原始均值"] --> TOPO["原静态拓扑损失"]
```

## 关键不变量

- `B` 始终是图片数，`C` 始终按全局类别顺序；训练时只切 seen 列。
- seen/unseen 都用同一个 PSE；没有未见图像或标签进入训练。
- 条件原型不进入 BVSA，防止实验问题从“全局选句”漂移成“全局和局部共同选句”。
- 拓扑损失继续读取母版的 seen-PSE/unseen-raw 静态原型，不读取全类条件原型或全类均匀 PSE 原型。
- PSE、Top-K、训练日程和损失权重与实验 B 相同。
