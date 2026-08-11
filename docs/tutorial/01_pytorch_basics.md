# 01 — PyTorch 基础速览

> 只讲 GTPJ 代码中实际用到的概念。如果某个 PyTorch 功能代码里没出现，这里就不讲。

---

## 1. 张量（Tensor）

张量就是多维数组。PyTorch 的张量和 NumPy 的 `ndarray` 几乎一样，但多了两个能力：
- 可以在 GPU 上运行
- 可以记录梯度（自动求导）

```python
import torch

# 创建张量
a = torch.tensor([1.0, 2.0, 3.0])          # 从列表创建，形状 [3]
b = torch.zeros(3, 4)                        # 全零，形状 [3, 4]
c = torch.ones(10)                           # 全一，形状 [10]
d = torch.randn(2, 3, 4)                     # 标准正态分布随机数，形状 [2, 3, 4]

# 关键属性
print(a.shape)    # torch.Size([3])  ← 形状
print(a.dtype)    # torch.float32    ← 数据类型
print(a.device)   # cpu              ← 在哪个设备上

# 数据类型转换
a.float()         # → float32
a.half()          # → float16（半精度，省显存）
a.long()          # → int64（标签用）
```

### GTPJ 代码中的常见形状标记

代码注释里经常看到 `[B, C, D]` 这种标记：

| 字母 | 含义 | CUB 数据集上的值 |
|---|---|---|
| `B` | batch size（批次大小） | 64 |
| `C` | class count（类别总数） | 200 |
| `C_seen` | seen class count（可见类别数） | 150 |
| `C_unseen` | unseen class count（不可见类别数） | 50 |
| `D` / `dim_f` | CLIP 特征维度 | 768 |
| `N` / `K` | patch 数量 | 576 或 32（选择后） |
| `M` | 每个类的句子数 | 7 |

---

## 2. `nn.Module` — 所有模型的基类

你的 GTPJ 模型继承自 `nn.Module`。这是 PyTorch 最核心的类。

```python
import torch.nn as nn

class MyModel(nn.Module):
    def __init__(self):
        super().__init__()           # 必须调用父类 __init__
        self.fc = nn.Linear(10, 5)   # 定义子层

    def forward(self, x):
        return self.fc(x)            # 定义前向传播

model = MyModel()
y = model(x)   # 自动调用 forward()
```

### 关键规则

- 在 `__init__` 里定义所有层
- 在 `forward` 里定义数据如何流过这些层
- **永远不要直接调用 `model.forward(x)`，写 `model(x)` 就行**（PyTorch 会在内部做额外处理）

### `nn.Module` 自动追踪子模块

```python
class Parent(nn.Module):
    def __init__(self):
        super().__init__()
        self.child = nn.Linear(10, 5)   # 自动注册为子模块

parent = Parent()
# parent.parameters() 会自动包含 child 的所有参数
# parent.to('cuda')   会自动把 child 也搬到 GPU
```

如果你把 `nn.Module` 存在 `nn.ModuleList` 或 `nn.ModuleDict` 里，也会被自动追踪：

```python
self.layers = nn.ModuleList([nn.Linear(10, 10) for _ in range(3)])
# 这三个 Linear 层都会被 model.parameters() 找到
```

---

## 3. 可学习参数 vs 不可学习缓冲区

### `nn.Parameter` — 要训练的参数

```python
self.weight = nn.Parameter(torch.randn(768, 768))
# 这个张量会被 optimizer 更新
# 默认 requires_grad=True
```

### `register_buffer` — 不训练但要跟着模型走的数据

```python
self.register_buffer("seenclass", torch.tensor([0, 1, 2, ...]), persistent=False)
# persistent=False → 存 checkpoint 时不保存（GTPJ 里几乎所有 buffer 都设了 False）
# 这个张量不参与梯度更新，但会跟着 model.to('cuda') 一起搬到 GPU
```

**GTPJ 代码里大量使用 `register_buffer` 存储固定数据**，比如类别索引、文本嵌入等——这些是输入数据，不是要训练的参数，但每次 forward 都要用，所以存成 buffer 方便。

---

## 4. 常用层

### `nn.Linear` — 全连接层

```python
layer = nn.Linear(in_features=768, out_features=512, bias=True)
# 数学：y = x @ W.T + b
# W 形状 [512, 768]，b 形状 [512]
# 输入 [B, 768] → 输出 [B, 512]
```

GTPJ 代码中常见的变体：

```python
nn.Linear(768, 768, bias=False)    # 无偏置的投影
nn.Linear(768, 48)                 # 降维瓶颈层（ICSA 里用）
nn.Linear(512, 1)                  # 输出标量（DynamicRoutingGate 里用）
```

### `nn.LayerNorm` — 层归一化

```python
ln = nn.LayerNorm(512)
# 对最后一维做归一化，稳定训练
# 输入 [B, 512] → 输出 [B, 512]，均值为 0 方差为 1
```

### `nn.Dropout` — 随机丢弃

```python
drop = nn.Dropout(0.5)
# 训练时随机把 50% 的神经元输出置 0，防止过拟合
# eval 时自动关闭（model.eval() 后不丢）
```

### `nn.MultiheadAttention` — 多头自注意力

```python
attn = nn.MultiheadAttention(
    embed_dim=768,      # 输入/输出维度
    num_heads=4,         # 头数，必须能整除 embed_dim
    dropout=0.5,
    batch_first=True,    # ★ 关键：让输入形状为 [B, N, D] 而非 [N, B, D]
)

# 自注意力：Q、K、V 都来自同一个 x
attn_out, attn_weights = attn(x, x, x, need_weights=False)
# attn_out 形状 [B, N, 768]，和输入一样
```

GTPJ 的 PSE 模块用 `batch_first=True` 的单头/多头自注意力处理句子级文本特征。

### `nn.TransformerDecoderLayer` — Transformer 解码器层

```python
decoder = nn.TransformerDecoderLayer(
    d_model=512,              # 模型维度
    nhead=4,                  # 头数
    dim_feedforward=1024,    # FFN 隐藏层维度（通常是 d_model 的 2-4 倍）
    dropout=0.1,
    batch_first=True,
)

# 交叉注意力：tgt 做 query，memory 做 key/value
output = decoder(tgt=text_features, memory=visual_features)
# tgt [B, C, 512] — 文本特征
# memory [B, K, 512] — 视觉特征
# output [B, C, 512] — 文本特征被视觉信息增强后的结果
```

GTPJ 的 BVSA 模块用两个 `TransformerDecoderLayer`：
- `decoder_v2s`：tgt=文本, memory=视觉（文本去查询视觉）
- `decoder_s2v`：tgt=视觉, memory=文本（视觉去查询文本）

---

## 5. 激活函数

```python
import torch.nn.functional as F

F.relu(x)        # ReLU：max(0, x)
F.gelu(x)        # GELU：比 ReLU 更平滑，Transformer 标配
F.softmax(x, dim=-1)    # Softmax：把最后一维变成概率分布
F.log_softmax(x, dim=-1)  # Log-Softmax：取 log 后再 softmax，数值更稳定
F.sigmoid(x)     # Sigmoid：输出范围 (0, 1)，用作门控
```

GTPJ 代码中常见写法：

```python
# CLIP 式温度缩放
logit_scale = self.logit_scale.exp()    # logit_scale 存的是 log(1/0.07)，exp 后变回 ~14.3

# DynamicRoutingGate 里的门控
gate_value = self.min_value + (self.max_value - self.min_value) * torch.sigmoid(logits)
```

---

## 6. 核心操作

### 张量乘法

```python
# 矩阵乘法（最后两维做乘法）
a @ b                      # 等价于 torch.matmul(a, b)

# 逐元素乘法
a * b                      # 形状必须完全相同或可广播

# Einstein 求和（灵活的多维乘法）
torch.einsum("bnd,bd->bn", patch_n, text_n)
# 含义：对每一对 (batch, patch)，把 patch 向量和 text 向量逐元素乘，然后在 D 维求和
# 结果形状 [B, N]
```

### 归一化

```python
F.normalize(x, dim=-1)     # L2 归一化：x / ||x||
# dim=-1 表示沿最后一维做归一化
# 输入 [B, 768] → 输出 [B, 768]，每行的 L2 范数 = 1
```

### 形状变换

```python
x.view(B, N, D)           # 改变形状，不拷贝数据（要求内存连续）
x.reshape(B, N, D)        # 改变形状，可能拷贝（更安全但更慢）
x.permute(0, 2, 1)        # 交换维度顺序，不拷贝数据
x.unsqueeze(0)            # 在第 0 维前面插一个大小为 1 的维度
x.unsqueeze(-1)            # 在最后面插一个大小为 1 的维度
x.squeeze(-1)             # 删除大小为 1 的最后一维
x.expand(B, -1, -1)      # 广播：不拷贝数据，把大小为 1 的维"假装"变成更大的
                          # -1 表示该维保持不变
```

GTPJ 代码中非常常见的组合：

```python
# 把 [C, 768] 的类文本原型扩展到 batch 维度
all_text.unsqueeze(0).expand(B, -1, -1)
# [C, 768] → unsqueeze(0) → [1, C, 768] → expand(B, -1, -1) → [B, C, 768]

# 把 [B, 768] 扩展到类别维度
vis_n.unsqueeze(1).expand(-1, C, -1)
# [B, 768] → unsqueeze(1) → [B, 1, 768] → expand(-1, C, -1) → [B, C, 768]
```

### 索引操作

```python
# 整数索引
all_text[self.seenclass]         # 从 [200, 768] 中选出 seenclass 对应的行

# gather：按索引从指定维度取元素
torch.gather(patches, dim=1, index=idx_exp)
# 在 dim=1 上，按照 idx_exp 里的索引值取出对应元素

# scatter_：按索引往张量里写值（原地操作，带下划线）
mask.scatter_(1, masked_idx, True)
# 在 dim=1 上，把 masked_idx 指定的位置设为 True

# topk：取前 K 大（或前 K 小）的值和索引
_, topk_indices = torch.topk(patch_score, k=32, dim=1, largest=True)
```

### 拼接

```python
torch.cat([a, b], dim=-1)    # 沿最后一维拼接
# a [B, 768], b [B, 768] → [B, 1536]
```

### 设备转移

```python
x.to('cuda')              # 移到 GPU
x.to(device='cuda:0', dtype=torch.float32)  # 同时改设备和类型
x.cpu()                   # 移到 CPU
x.detach()                # 切断梯度图（不再追踪此张量的梯度）
```

---

## 7. 训练相关

### `model.train()` vs `model.eval()`

```python
model.train()   # 训练模式：Dropout 生效，BatchNorm 更新统计量
model.eval()    # 评估模式：Dropout 关闭，BatchNorm 用固定统计量
```

### `torch.no_grad()`

```python
with torch.no_grad():
    y = model(x)   # 这个上下文里的所有操作都不记录梯度，省显存
```

### `optimizer.zero_grad()` / `loss.backward()` / `optimizer.step()`

```python
# 每个训练 step 的标准三步：
optimizer.zero_grad()    # 1. 清零上次的梯度
loss.backward()          # 2. 反向传播，计算所有参数的梯度
optimizer.step()         # 3. 用梯度更新参数
```

### `F.cross_entropy`

```python
loss = F.cross_entropy(logits, labels)
# logits [B, n_class] — 原始分数（不需要 softmax，CE 内部会做）
# labels [B] — 每个样本的正确类别索引（不是 one-hot）
```

### `F.kl_div`

```python
loss = F.kl_div(log_p_student, p_teacher.detach(), reduction="batchmean")
# KL 散度：衡量两个概率分布的差异
# log_p_student — 学生的 log-softmax 输出
# p_teacher — 教师的 softmax 输出（.detach() 表示不传梯度给教师）
# reduction="batchmean" — 对 batch 取平均
```

### `F.cosine_similarity`

```python
sim = F.cosine_similarity(a, b, dim=-1)
# 余弦相似度：a·b / (|a| × |b|)
# 输出范围 [-1, 1]，1 表示完全相同
```

---

## 8. Python 特性

### `@property` 装饰器

```python
class GTPJ(nn.Module):
    @property
    def bvsa(self):
        return self.cross_tf
```

这样写 `model.bvsa` 和 `model.cross_tf` 是同一个对象。作用是给复杂名字（`cross_tf`）起一个语义化别名（`bvsa`），代码可读性更好。

### `@staticmethod` 和 `@classmethod`

```python
@staticmethod
def helper(x):          # 不需要访问 self
    return x + 1

@classmethod
def validate(cls, config):  # 可以访问类本身（cls），但不能访问实例
    ...
```

### `getattr` / `hasattr`

```python
hasattr(config, 'use_icsa')        # 检查对象有没有这个属性
getattr(config, 'use_icsa', False) # 获取属性，不存在时返回默认值 False
```

### 解包

```python
_, topk_indices = torch.topk(...)
# _ 表示"我不关心这个返回值"
# 等价于 result = torch.topk(...); topk_indices = result[1]
```

---

## 你已经学会

- [ ] 张量的 shape/dtype/device 三个核心属性
- [ ] `nn.Module` 的 `__init__` + `forward` 模式
- [ ] `nn.Parameter` vs `register_buffer` 的区别
- [ ] `nn.Linear`、`nn.MultiheadAttention`、`nn.TransformerDecoderLayer` 的用法
- [ ] `F.normalize`、`F.cross_entropy`、`F.kl_div` 的语义
- [ ] `unsqueeze` + `expand` 的形状广播技巧
- [ ] `model.train()` vs `model.eval()` + `torch.no_grad()`
- [ ] 训练三步曲：`zero_grad` → `backward` → `step`

准备好后 → 进入 [02 — 框架全景图](02_framework_overview.md)
