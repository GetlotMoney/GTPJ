# VCER 框架图

八句话不是八个对称分支，而是一个具有三种职责的证据路由器：六个局部描述产生
可检验的区域差异，全局描述判断区域是否属于主体，独特描述决定哪些局部差异值得信任。

```mermaid
flowchart LR
    X["冻结 CLIP CLS x"] --> B["冻结 PSE-X2 全局底分 b"]
    Z["冻结 X2 原型 z"] --> B
    B --> Q["每个候选的最强混淆类 q"]

    U["1 个独特描述 u"] --> R["六局部差异的角色路由 w"]
    L["6 个局部描述 l"] --> R
    L --> M["同 patch 候选-混淆类边际 m"]
    Q --> R
    Q --> M

    P["冻结 CLIP patch p"] --> M
    P --> F["主体/前景可见性 fg"]
    G["1 个全局描述 g"] --> F
    Q --> F

    M --> E["可见反事实证据 E"]
    F --> E
    R --> E
    B --> S["固定等权有界合成"]
    E --> S
    S --> O["B×C logits"]

    SW["unique-swap 因果约束"] -.只破坏路由.-> R
```

## 边界

- 文本底座仍是 PSE-X2；VCER 不把 PSE-X2 改名为原创。
- 只有共享低秩投影可学习；没有类别或 split 专属参数。
- `VCER-off` 保留 `logits(image_features, class_ids)` 位置接口，直接走冻结 X2，不读 patch；训练损失只剩底分 CE。
- role-shuffle 只错配“unique 路由权重—六路视觉证据”，不能把二者一起重排后把坐标重命名冒充干预。
- 当前图只描述 VCER；未叠加 HSTB、VEC、CHORM 或其他候选模块。
