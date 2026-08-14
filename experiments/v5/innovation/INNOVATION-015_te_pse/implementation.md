# TE-PSE 实现合同

## 1. 输入与符号

- `t[c,r]`：类别 c、角色 r 的冻结并归一化 CLIP 文本向量。
- `x`：冻结并归一化 CLIP 图像 CLS。
- 八个文本角色按配置固定；证据角色集合 E 只包含 0..5、7，即六个局部角色与 unique。
- 类别集合包含 150 seen 与 50 unseen；全部类别文本在 GZSL 中是已知语义，不使用 unseen 图像或标签训练。

## 2. 冻结全局 anchor

```text
b_c = normalize(mean_r t[c,r])
base_logit(x,c) = cosine(x,b_c) / T
```

这精确对应 GPT-5.6 八句纯 CLIP 等权基线。M1 内不更换文本、anchor 或 temperature。

## 3. 同角色 rival 与区分度

每个 c、r 只在同一角色中寻找其他类别：

```text
j*(c,r) = argmax_{j != c} cosine(t[c,r], t[j,r])
d(c,r)  = (1 - cosine(t[c,r], t[j*,r])) / 2
w(c,r)  = d(c,r) / sum_{k in E} d(c,k)
```

d 位于 0 到 1。如果一个极端退化输入使七个 d 全为 0，则回退为七角色等权。rival 与权重完全由冻结文本确定，不接收图像梯度。

## 4. 有界证据向量与静态一致度

每个角色的冻结向量为：

```text
e(c,r) = 0.5 * w(c,r) * (t[c,r] - t[j*(c,r),r])
e(c)   = sum_r e(c,r)
q(c)   = ||e(c)||_2
```

因为归一化向量之差的范数不超过 2，且角色权重和为 1，所以 q(c) 不超过 1。角色方向互相冲突时会在 e(c) 中抵消；方向一致且能区别 rival 时保留更大的向量范数。

q 是由冻结文本得到的类别静态证据一致度，不是图像动态置信度，也不是额外学习的 gate；论文陈述不得把它写成 confidence-aware inference。

## 5. 唯一可训练参数与最终分数

```text
alpha = alpha_cap * sigmoid(a)
0 < alpha < 0.5

contribution(x,c,r) = alpha * dot(x,e(c,r)) / T
final_logit(x,c) = base_logit(x,c) + sum_r contribution(x,c,r)
```

只有标量 a 可训练；它由 seen 训练样本 CE 学习，再原样应用到所有 seen/unseen 类别。等价的未归一化类别向量为 b_c + alpha*e(c)，其最大偏移受 alpha*q(c) 约束。

删除某一角色且不重归一化时，final logit 的变化严格等于该角色报告的 contribution。代码与测试要求最大重构误差不超过 `1e-6`。

## 6. 与 CLIP-A-self/PSE 的结构边界

TE-PSE 明确不包含：

- Q/K/V 或任何句间 self-attention；
- attention token 求平均；
- learned sentence pooling 或 role MLP；
- attention prototype 与 raw prototype 的论文式 residual blend；
- seen 类专属 prototype 参数；
- unseen raw、seen adapted 的双空间路由。

它的核心计算发生在“同角色跨类别竞争证据到最终 score 精确加法”，而不是“同类别句间 attention 到新 prototype”。共同使用 GPT 视觉描述和冻结 CLIP 不是可声称的新点。

## 7. 训练与评估边界

1. 按 seed 对每个 seen 类的训练样本做固定 90/10 划分。
2. 只在 90% seen 训练样本上优化一个标量 a。
3. 只按 10% seen validation CE 选择 checkpoint；不按 official U/S/H/ZS 选 epoch。
4. preflight 只核对 official cache 的文件哈希；checkpoint 冻结后才反序列化 official seen/unseen tensor，并在同一次评估中计算预注册的 B0 与 TE-PSE。
5. 不在结果出来后改变 cap、init、role 集合、rival 规则或 temperature。
