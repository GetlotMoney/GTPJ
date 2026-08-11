# V5-INNOVATION-011 实现说明

状态：planned，尚未实现。

## 计划中的代码边界

如果后续开始实现，只允许从 `model/v5-template-v1` 独立分叉，不允许让本实验继承 009 或 010 的代码。

计划最小代码路径：

```text
输入图像
-> CLIP visual encoder
-> 全局图像特征 + 常规 patch/region 特征

8句话
-> CLIP text encoder
-> PSE 句间增强
-> 8个增强句子

增强句子 × 图像区域
-> 句子权重与区域权重
-> 类别条件视觉/语义表示
-> 最终分类分数
-> 主分类损失
```

## 明确不做

- 不接入频域 Top-K；
- 不接入旧 BVSA；
- 不接入 ICSA；
- 不接入 SGMP、BMDD、拓扑损失；
- 不新增全局/局部辅助分类损失；
- 不提前创建正式 V6 framework/tag。
