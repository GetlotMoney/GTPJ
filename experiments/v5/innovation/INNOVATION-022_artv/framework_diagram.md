# ARTV 框架图

```mermaid
flowchart LR
    X["冻结 official CLS"] --> B["冻结 PSE-X2 200类底分"]
    B --> T2["只取 top-1 / top-2"]

    I["原始 CUB 图像"] --> C["确定性 15-crop"]
    C --> V["冻结 CLIP crop CLS"]
    A["6 个类别无关部位锚点"] --> OT["带背景列的平衡 Sinkhorn 传输"]
    V --> OT
    G["1 个全局描述\ntop-2 对称前景质量"] --> OT
    OT --> S["6 个固定视觉角色槽"]

    L["6 个局部描述"] --> E6["同名槽的 6 票"]
    S --> E6
    U["1 个独特描述"] --> EU["跨六槽的第 7 票"]
    S --> EU
    E6 --> Q["至少 5 / 7 支持第二名"]
    EU --> Q
    T2 --> Q
    Q --> O["通过：只交换 top-2\n未通过：逐元素保持 X2"]
```

本地可直接打开的同图版本见 `framework_diagram.html`。

## 方法边界

- 八句话是 `6 局部 + 1 全局 + 1 独特`，不是八个对称分支。
- PSE-X2 只负责冻结全局原型；ARTV 是其后的无训练验证器。
- ARTV 不修改 X2 top-2 之外的分数，不使用类别/split 参数和 gamma。
- role-shuffle 固定视觉槽，仅打乱六个局部描述；unique-swap 只破坏第七票。
