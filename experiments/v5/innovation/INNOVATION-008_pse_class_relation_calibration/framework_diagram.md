# 框架图：对称、限幅的 PSE 类别关系验证

```mermaid
flowchart LR
    A["GPT-5.5 类别句子<br/>200 类 × 7 句"] --> B["类不重叠验证重排<br/>100 pseudo-seen + 50 pseudo-unseen"]
    B --> C1["seen 句子组"]
    B --> C2["unseen 句子组"]
    C1 --> D1["共享旧句子 PSE"]
    C2 --> D2["同一个旧句子 PSE<br/>独立 RNG 上下文"]
    D1 --> E1["seen 基础原型"]
    D2 --> E2["unseen 基础原型"]
    E1 --> F1["共享安全 Class-Relation<br/>分组运行"]
    E2 --> F2["共享安全 Class-Relation<br/>分组运行"]
    F1 --> G["全类别 logits"]
    F2 --> G
    G --> H["训练 CE 只取 seen 列"]
    G --> I["验证 U / S / H / ZS"]
```

## 三组开关

| 组别 | seen 路径 | unseen 路径 | 类别关系 |
|---|---|---|---|
| R0 | 旧句子 PSE | 原始句子均值 | 无 |
| R1 | 旧句子 PSE | 同一个旧句子 PSE | 无 |
| R2 | 旧句子 PSE | 同一个旧句子 PSE | 同一安全模块、两组分别运行 |

## 安全 Class-Relation

```text
base = normalize(PSE(sentences))
relation = MHA(LayerNorm(base))
correction = 0.1 * relation / max(norm(relation), 1)
output = normalize(base + correction)
```

- MHA 输出投影为零初始化，R2 起点与 R1 完全相同。
- 每类修正范数硬限制为 `<=0.1`，对应最大旋转约 `5.75°`。
- seen/unseen 共享权重但不联合注意，训练交叉熵不使用 unseen 标签。
- 选择 R0/R1/R2 时不加载正式测试缓存。

可编辑源文件 `framework_diagram.drawio` 保留第一版历史结构；第二版权威结构以本文件及 `implementation.md` 为准，本地浏览版为 `framework_diagram.html`。
