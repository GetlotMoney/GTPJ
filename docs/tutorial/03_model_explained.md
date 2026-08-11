# 03 — 模型代码详解 (`model/MyModel.py`)

> 对照 `model/MyModel.py`（共 1358 行），按代码出现顺序逐类讲解。

---

## 文件结构总览

```
行 1-19     文件头注释（接口约定）
行 21-25    导入
行 27-49    工具函数（高斯核、配置读取、门控偏置）
行 52-151   DynamicRoutingGate        ← 动态路由门控（研究前沿用）
行 154-189  fgvd_select_patches       ← FGVD 频域 patch 选择
行 192-207  SemanticPrototypeAdapter  ← PSE 瓶颈适配器（老版本用）
行 210-231  ProgressiveSemanticSelfAttention ← PSE 自注意力（v2+ 用）
行 233-277  BoxRelationalEmbedding    ← 几何位置嵌入
行 279-334  GeometryMultiHeadAttention + GeometryDecoupledEncoderLayer ← 几何解耦编码器
行 337-503  BidirectionalVisualSemanticAlignment ← BVSA 核心模块
行 507-1357 GTPJ                       ← 主模型（__init__ + forward + compute_loss）
```

---

## 第一部分：导入和工具函数（行 1-49）

### 导入

```python
import numpy as np        # 数学运算（clip 等）
import torch              # PyTorch 核心
import torch.nn as nn     # 神经网络层
import torch.nn.functional as F  # 函数式 API（softmax、normalize 等）
```

### `_gaussian_kernel_1d(length, sigma)`（行 27-30）

```python
def _gaussian_kernel_1d(length, sigma):
    x = torch.arange(-length // 2 + 1, length // 2 + 1, dtype=torch.float32)
    # 生成 [-L/2+1, ..., 0, ..., L/2] 的一维坐标
    kernel = torch.exp(-0.5 * (x / sigma) ** 2)
    # 高斯函数: exp(-x² / 2σ²)
    return kernel / torch.max(kernel)
    # 归一化：最大值变成 1
```

**作用**：生成一维高斯平滑核，FGVD 做频域滤波时用。把 patch 特征做 FFT 后在频率维度上加这个高斯权重，相当于低通滤波——平滑高频噪声，保留低频语义。

### `_autocast_disabled(tensor)`（行 33-34）

```python
def _autocast_disabled(tensor):
    return torch.amp.autocast(device_type=tensor.device.type, enabled=False)
```

**作用**：创建一个"强制关闭混合精度"的上下文管理器。FGVD 的 FFT 操作在 float16 下可能溢出，所以强制用 float32 做频域计算。

**用法**：
```python
with _autocast_disabled(patches):   # 这个代码块里强制 float32
    x_freq = torch.fft.fft(patches.float(), dim=-1)
```

### `_config_get(config, key, legacy_key, default)`（行 37-42）

```python
def _config_get(config, key, legacy_key=None, default=None):
    if hasattr(config, key):
        return getattr(config, key)              # 优先用新名字
    if legacy_key is not None and hasattr(config, legacy_key):
        return getattr(config, legacy_key)       # 回退到旧名字
    return default                               # 都没有则默认值
```

**作用**：兼容新旧配置名。GTPJ 经历多次重构，参数名改了但旧 checkpoint 和旧 config 还在用。例如：

```python
# 以下两种写法等价：
_config_get(config, "use_pse_self_attention", "use_clip_a_self", False)
# 先找 config.use_pse_self_attention（新名），找不到找 config.use_clip_a_self（旧名）
```

### `_gate_bias_from_value(value, min_value, max_value)`（行 45-49）

```python
def _gate_bias_from_value(value, min_value=0.0, max_value=1.0):
    span = max(float(max_value) - float(min_value), 1e-8)
    ratio = (float(value) - float(min_value)) / span    # 归一化到 [0, 1]
    ratio = float(np.clip(ratio, 1e-4, 1.0 - 1e-4))    # 防止 log(0)
    return float(np.log(ratio / (1.0 - ratio)))          # logit 变换
```

**作用**：把 [0, 1] 范围内的值转成 logit（log odds），用于初始化 DynamicRoutingGate 的输出层 bias。

**数学**：如果想让 sigmoid 输出是 0.2，最后一层 bias 应该设成 log(0.2/0.8) = log(0.25) ≈ -1.39。

---

## 第二部分：DynamicRoutingGate（行 52-151）

> **注意**：这是研究前沿（IDEA-0003/TRIAL-001）的模块，v5 主线默认不启用。但代码在主模型里，所以也详细讲。

### 设计意图

正常的 GTPJ 用固定系数（`local_weight=0.2`、`icsa_ratio=0.008`）。DynamicRoutingGate 试图让模型**自己学会每个样本应该用多大的系数**。

### `__init__` 参数

```python
def __init__(self, dim_f, hidden, mode, init_value, min_value=0.0, max_value=1.0,
             class_uses_sample=True):
```

| 参数 | 含义 |
|---|---|
| `dim_f` | 输入特征维度（768） |
| `hidden` | 中间隐藏层维度（64） |
| `mode` | `"fixed"`（固定值）、`"sample"`（只看样本）、`"class"`（看样本+类别） |
| `init_value` | 初始输出值（固定模式的锚点值） |
| `class_uses_sample` | `"class"` 模式下是否同时用样本特征 |

### `__init__` 核心逻辑

```python
self.register_buffer("anchor", torch.tensor(float(init_value)), persistent=False)
# 注册一个不可训练的锚点值
# persistent=False → 保存 checkpoint 时不存（不需要，config 里就有）

if self.mode == "fixed":
    self.net = None     # ★ 固定模式不需要网络
    return

# 动态模式：构造一个小型 MLP
if self.mode == "class" and self.class_uses_sample:
    input_dim = dim_f * 2   # 拼接样本特征 + 类别文本特征
# ...
self.net = nn.Sequential(
    nn.Linear(input_dim, hidden),   # 768 → 64
    nn.LayerNorm(hidden),           # 归一化
    nn.GELU(),                      # 激活
    nn.Linear(hidden, 1),           # 64 → 1（输出一个标量）
)

# ★ 关键初始化：最后一层 weight=0, bias=对应锚点值的 logit
with torch.no_grad():
    self.net[-1].weight.zero_()
    self.net[-1].bias.fill_(_gate_bias_from_value(init_value, min_value, max_value))
```

**为什么 weight=0？** 这样网络初始输出恒等于 bias 对应的值，相当于从头就输出锚点值（如 0.2），然后慢慢学偏。是一种稳定训练的技巧。

### `_scale(self, logits)`（行 98-99）

```python
def _scale(self, logits):
    return self.min_value + (self.max_value - self.min_value) * torch.sigmoid(logits)
```

把网络输出的任意值映射到 `[min_value, max_value]` 区间。min_value 默认 0，max_value 默认 1，所以输出范围是 [0, 1]。

### `_fixed(self, ...)`（行 101-123）

固定模式下，直接返回锚点值扩展成需要的形状：

```python
value = self.anchor.to(device=device, dtype=dtype)
# 如果同时有 batch_size 和 class_count → 扩展成 [B, C]
return value.view(1, 1).expand(int(batch_size), int(class_count))
```

### `forward(self, ...)`（行 125-151）

```python
def forward(self, sample_feat=None, class_text=None, batch_size=None, class_count=None):
    if self.mode == "fixed":
        return self._fixed(...)
    if self.mode == "sample":
        return self._scale(self.net(sample_feat))       # 只看图像特征
    # mode == "class":
    gate_in = torch.cat([sample_batch, class_batch], dim=-1)
    return self._scale(self.net(gate_in)).squeeze(-1)   # 拼接图像+文本特征
```

---

## 第三部分：fgvd_select_patches（行 154-189）

### 设计意图

CLIP ViT 输出 576 个 patch（24×24 的 grid），很多 patch 是背景或无关节。FGVD 用**频域分析**判断每个 patch 的信息量，选出 K=32 个最重要的。

### 逐行讲解

```python
def fgvd_select_patches(F_p, K=64, sigma=None, largest=True, formula="v2_abs_mean"):
    _, N, D = F_p.shape       # F_p: [B, 576, 768]
    K = max(1, min(int(K), N)) # 防止 K 超过实际 patch 数

    F_p_fp32 = F_p.float()     # ★ 强制转 float32，FFT 操作需要精度

    # 步骤 1: FFT 沿特征维度
    x_freq = torch.fft.fft(F_p_fp32, dim=-1)
    # 对 768 维特征做一维 FFT，得到频域表示
    # FFT 变换：把"每个特征值"变成"频率分量"
    # 低频 = 平滑变化（语义信息），高频 = 剧烈变化（纹理/噪声）

    # 步骤 2: 高斯低通滤波
    if sigma is None:
        sigma = D ** 0.5     # 默认 sigma = sqrt(768) ≈ 27.7
    gs_k = _gaussian_kernel_1d(D, sigma).to(F_p_fp32.device)
    x_freq = torch.fft.fftshift(x_freq, dim=-1)  # 把零频移到中心
    x_freq = x_freq * gs_k                        # 频率加权（中心低频权重大）
    x_freq = torch.fft.ifftshift(x_freq, dim=-1)  # 移回来

    # 步骤 3: 逆 FFT → 得到低通版本
    x_lp = torch.fft.ifft(x_freq, dim=-1).real
    # x_lp 是低通滤波后的特征，保留了语义，去掉了高频噪声

    # 步骤 4: 计算每个 patch 的"信息量分数"
    # v2_abs_mean (默认): 原始特征和低通特征的差异越大 → 信息越多
    diff = F_p_fp32 / (torch.abs(x_lp - F_p_fp32) + 1e-6)
    patch_score = diff.abs().mean(dim=-1)  # [B, 576]

    # 步骤 5: 选 Top-K
    _, topk_indices = torch.topk(patch_score, k=K, dim=1, largest=True)
    # 返回 [B, 32] 的索引
    return topk_indices, patch_score
```

**三种 formula 的区别**：

| formula | 计算方式 | 特点 |
|---|---|---|
| `v2_abs_mean` | 原始/(低通偏差) 的绝对值平均 | 默认选择，实验最优 |
| `v1_strict` | 同上但不取绝对值 | 倾向高频 patch |
| `v3_norm` | 1/(低通偏差的 L2 范数) | 倾向平滑 patch |

---

## 第四部分：SemanticPrototypeAdapter（行 192-207）

```python
class SemanticPrototypeAdapter(nn.Module):
    def __init__(self, c_in, reduction=4):
        super().__init__()
        self.fc = nn.Sequential(
            nn.Linear(c_in, c_in // reduction, bias=False),  # 768 → 192（瓶颈）
            nn.ReLU(inplace=True),                            # 非线性
            nn.Linear(c_in // reduction, c_in, bias=False),  # 192 → 768（恢复）
        )
    def forward(self, x):
        return self.fc(x)
```

**作用**：瓶颈式文本原型适配器。压缩到 1/4 再恢复——强制模型学习紧凑的文本表示。**v1 使用这个，v2+ 被 ProgressiveSemanticSelfAttention 替代。**

**inplace=True**：`ReLU(inplace=True)` 表示直接在原张量上修改，省一点显存（不创建新张量）。

---

## 第五部分：ProgressiveSemanticSelfAttention（行 210-231）

### 这是 PSE 的核心——v2+ 版本

```python
class ProgressiveSemanticSelfAttention(nn.Module):
    def __init__(self, dim, heads=1, dropout=0.5, inner_ratio=0.5):
        super().__init__()
        self.inner_ratio = float(inner_ratio)       # 残差混合比例：0.35

        self.attn = nn.MultiheadAttention(
            embed_dim=dim,        # 768
            num_heads=int(heads), # 4 (v5) 或 1 (v2)
            dropout=float(dropout),  # 0.5
            batch_first=True,     # ★ 输入形状 [B, M, 768]
        )
        self.proj = nn.Linear(dim, dim)             # 输出投影
        self.dropout = nn.Dropout(float(dropout))
        self.layer_norm = nn.LayerNorm(dim)

    def forward(self, x):
        # x 形状: [C, M, 768]（每类 M 个句子，C 个类）

        # 步骤 1: 自注意力——M 个句子互相"看"对方
        attn_out, _ = self.attn(x, x, x, need_weights=False)
        # attn_out 形状: [C, M, 768]

        # 步骤 2: 投影 + Dropout
        attn_out = self.dropout(self.proj(attn_out))

        # 步骤 3: ★ 残差混合
        mixed = self.inner_ratio * attn_out + (1.0 - self.inner_ratio) * x
        # 0.35 × 增强后 + 0.65 × 原始输入
        # 平衡"增强"和"保持原始语义"

        # 步骤 4: LayerNorm 并放大 2 倍（独特设计）
        return self.layer_norm(2.0 * mixed)
```

### 完整 PSE 流程（在 GTPJ 类中体现）

```
句子嵌入 [C, M, 768]
    │
    ├─► mean(dim=1) → base        [C, 768]   （原始平均，不做增强）
    │
    └─► SelfAttention → mean(dim=1) → attn   [C, 768]   （自注意力增强后平均）
              │
              └─► all_text = 0.65 × attn + 0.35 × base   （outer blend）
                       │
                       └─► F.normalize(dim=1)            （L2 归一化）
```

注意：PSE 里有两层残差混合——
- **inner_ratio=0.35**：自注意力内部，增强后 vs 原始句子
- **outer_ratio=0.65**：最终融合，自注意力输出 vs 原始平均

---

## 第六部分：BoxRelationalEmbedding（行 233-277）

### 设计意图

24×24 个 patch 之间有两两相对位置关系。BoxRelationalEmbedding 预计算所有 patch 对之间的 4 维相对几何特征 (Δx, Δy, Δw, Δh)，然后用正弦/余弦位置编码扩展到 64 维。

### 逐行讲解

```python
def _compute_embedding(self):
    H, W = self.grid_size   # (24, 24)
    seq_len = H * W          # 576

    # 每个 patch 的中心坐标 (cx, cy) 和宽高 (w, h)
    # 24×24 grid, 每个 patch 宽高为 1
    cx = (px_min + px_max) * 0.5   # [576]
    cy = (py_min + py_max) * 0.5

    # 四维相对特征：两两 patch 之间
    delta_x = log(|cx_i - cx_j| / w_i)   # [576, 576]
    delta_y = log(|cy_i - cy_j| / h_i)
    delta_w = log(w_i / w_j)
    delta_h = log(h_i / h_j)

    pos_mat = torch.stack([delta_x, delta_y, delta_w, delta_h], dim=-1)  # [576, 576, 4]

    # 傅里叶位置编码：把 4 维几何特征扩展到 64 维
    feat_range = torch.arange(8).float()      # [0..7], dim_g/8 = 64/8 = 8
    dim_mat = 1.0 / (1000.0 ** (feat_range / 8))  # 波长：1000^(0/8) 到 1000^(7/8)

    # pos_mat 乘 100 放大，再乘 dim_mat 得到不同频率
    mul_mat = (pos_mat * dim_mat).view(seq_len, seq_len, -1)  # [576, 576, 32]

    # sin + cos 拼接 → 64 维
    embedding = torch.cat([mul_mat.sin(), mul_mat.cos()], dim=-1)
    return embedding.half()  # ★ 转 float16 省显存
```

**产生的几何嵌入**：`[576, 576, 64]`，表示每对 patch 之间的 64 维几何关系向量。

### `forward(self, batch_size)`

```python
def forward(self, batch_size):
    return self.geometry_embedding.unsqueeze(0).expand(batch_size, -1, -1, -1)
# [576, 576, 64] → [B, 576, 576, 64]
```

---

## 第七部分：GeometryMultiHeadAttention + GeometryDecoupledEncoderLayer（行 279-334）

### GeometryMultiHeadAttention（行 279-312）

```python
class GeometryMultiHeadAttention(nn.Module):
    def __init__(self, dim_com, heads, dim_g=64, dropout=0.1):
        # 标准多头注意力的 Q/K/V/O 投影
        self.fc_q = nn.Linear(dim_com, dim_com)
        self.fc_k = nn.Linear(dim_com, dim_com)
        self.fc_v = nn.Linear(dim_com, dim_com)
        self.fc_o = nn.Linear(dim_com, dim_com)

        # ★ 核心创新：每个头一个几何权重映射器
        self.WGs = nn.ModuleList([nn.Linear(64, 1, bias=True) for _ in range(heads)])
        # 把 64 维几何嵌入 → 1 个标量（几何偏置）
```

### forward 逐行讲解

```python
def forward(self, x, geometry_emb):
    B, N, D = x.shape    # [B, K, 512]，K=32（选择的 patch 数）

    # 步骤 1: 标准多头 Q/K/V
    q = self.fc_q(x).view(B, N, self.heads, self.d_k).permute(0, 2, 1, 3)
    # q: [B, heads, N, d_k]

    # 步骤 2: 注意力分数
    att = torch.matmul(q, k.transpose(-2, -1)) / (self.d_k ** 0.5)
    # att: [B, heads, N, N] — 标准的缩放点积注意力

    # 步骤 3: ★ 几何偏置（核心创新）
    geo_flat = geometry_emb.float().reshape(-1, 64)  # [B*N*N, 64]
    geo_per_head = [
        layer(geo_flat).view(B, N, N, 1).permute(0, 3, 1, 2)
        for layer in self.WGs
    ]  # 每个头输出 [B, 1, N, N]
    geo_weights = F.relu(torch.cat(geo_per_head, dim=1))  # [B, heads, N, N]

    # ★ 关键操作：用几何权重"减"注意力分数
    att = F.softmax(att - geo_weights, dim=-1)
    # 两个 patch 几何距离越远 → geo_weights 越大 → 注意力越低
    # 这就是"几何解耦"：让模型不要因为位置近就给高注意力

    # 步骤 4: 标准输出
    out = torch.matmul(att, v).permute(0, 2, 1, 3).contiguous().view(B, N, D)
    return self.ln(x + self.fc_o(out))   # 残差 + LayerNorm
```

**为什么是"减"而不是"加"？** 几何距离近的 patch 对，几何偏置小（接近 0），注意力不受影响；几何距离远的 patch 对，几何偏置大（正数），从注意力分数中减去，降低其权重。这个设计来自 TransZero 论文。

### GeometryDecoupledEncoderLayer（行 315-334）

标准 Transformer 编码器层，只是把自注意力换成了上面的几何解耦注意力：

```python
class GeometryDecoupledEncoderLayer(nn.Module):
    def __init__(self, dim_com, heads, dropout=0.1, dim_g=64):
        self.attn = GeometryMultiHeadAttention(dim_com, heads, dim_g, dropout)
        self.ffn = nn.Sequential(
            nn.Linear(512, 1024),         # 扩展 2 倍
            nn.ReLU(inplace=True),
            nn.Linear(1024, 512),         # 恢复
        )
        self.ln = nn.LayerNorm(512)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x, geometry_emb):
        x = self.attn(x, geometry_emb)          # 几何解耦自注意力
        return self.ln(x + self.dropout(self.ffn(x)))  # FFN + 残差
```

---

## 第八部分：BidirectionalVisualSemanticAlignment（行 337-503）

### 这是 BVSA——框架里最大的单个模块

`__init__` 参数：
```python
def __init__(self, dim_f=768, dim_com=512, heads=4, dropout=0.1,
             weight_s2v=0.5, grid_size=(24,24), dim_g=64,
             use_fgvd_geometry=True):
```

### 子模块一览

```python
# 1. 投影层：768 → 512（CLIP 空间 → Transformer 空间）
self.embed_cv = nn.Linear(768, 512)     # 视觉嵌入
self.embed_text = nn.Linear(768, 512)   # 文本嵌入

# 2. 可选：几何编码器（如果 use_fgvd_geometry=True）
if self.use_fgvd_geometry:
    self.box_emb = BoxRelationalEmbedding(grid_size=(24,24), dim_g=64)
    self.fae = GeometryDecoupledEncoderLayer(512, heads, dropout)

# 3. 两个 Transformer 解码器层（★ 核心）
self.decoder_v2s = nn.TransformerDecoderLayer(
    d_model=512, nhead=heads, dim_feedforward=1024, dropout=dropout,
    batch_first=True,
)
self.decoder_s2v = nn.TransformerDecoderLayer(
    d_model=512, nhead=heads, dim_feedforward=1024, dropout=dropout,
    batch_first=True,
)

# 4. 兼容性投影（v1 遗留，当前不用但保留以保证随机种子一致）
self.proj_visual = nn.Linear(512, 768)   # 不被 active 代码读取
self.proj_text = nn.Linear(512, 768)
```

### forward 逐行讲解

```python
def forward(self, patches, text, cls_token=None,
            fgvd_select_k=0, fgvd_select_sigma=0.0, ...):
    B = patches.size(0)

    # ═══ 阶段 A: FGVD patch 选择 ═══
    if fgvd_select_k > 0 and fgvd_select_k < patches.size(1):
        # 频域选 K 个 patch
        topk_indices, _ = fgvd_select_patches(patches.float(), K=fgvd_select_k, ...)

        # 用 gather 按索引取出选中的 patch
        idx_exp = topk_indices.unsqueeze(-1).expand(-1, -1, patches.size(-1))
        # idx_exp: [B, 32, 768]，每个位置是要取的索引
        patches = torch.gather(patches, dim=1, index=idx_exp)
        # gather: patches[i][idx_exp[i][j][k]][k] 语义上正确
        # 结果: [B, 32, 768]

    # ═══ 阶段 B: 视觉编码 = 投影 + 几何增强 ═══
    vis = self.embed_cv(patches)  # [B, 32, 512]

    if self.use_fgvd_geometry:
        geometry_emb = self.geometry_for_indices(B, topk_indices, seq_len=patches.size(1))
        # geometry_emb: [B, 32, 32, 64] — 32 个选中 patch 之间的几何关系
        if geometry_emb is not None:
            memory = self.fae(vis, geometry_emb)  # 几何解耦编码
        else:
            memory = vis
    else:
        memory = vis
    # memory: [B, 32, 512] — 这就是 FGVD 记忆

    # ═══ 阶段 C: 文本处理 ═══
    txt_com = self.embed_text(text)  # text 是 [C, 768] 或 [B, C, 768]

    if txt_com.dim() == 2:
        # 共享文本模式 (v3 及之前): [C, 512] → [B, C, 512]
        txt_batch = txt_com.unsqueeze(0).expand(B, -1, -1)
    elif txt_com.dim() == 3:
        # 条件文本模式 (v5): [B, C, 512] — 每张图有自己的文本原型
        txt_batch = txt_com

    # ═══ 阶段 D: 双向跨模态解码 ═══
    # V2S: 文本查询视觉记忆
    F_p_v2s = self.decoder_v2s(tgt=txt_batch, memory=memory)
    # tgt(目标)=文本 [B,C,512], memory(上下文)=视觉 [B,32,512]
    # 输出: [B, C, 512] — 被视觉信息增强的文本特征

    # S2V: 视觉查询文本记忆
    F_p_s2v = self.decoder_s2v(tgt=memory, memory=txt_batch)
    # tgt=视觉 [B,32,512], memory=文本 [B,C,512]
    # 输出: [B, 32, 512] — 被文本信息增强的视觉特征

    # ═══ 阶段 E: 计算分类分数 ═══
    # V2S 分数：增强后的文本特征 × 原始文本嵌入 → 余弦相似度
    v2s_n = F.normalize(F_p_v2s, dim=-1)       # [B, C, 512]
    txt_batch_n = F.normalize(txt_batch, dim=-1)
    score_v2s = (v2s_n * txt_batch_n).sum(dim=-1)  # [B, C]

    # S2V 分数：pool 视觉特征 → 和文本原型做内积
    s2v_pooled = F_p_s2v.mean(dim=1)            # [B, 512]（对 32 个 patch 取平均）
    s2v_n = F.normalize(s2v_pooled, dim=-1)
    txt_single = F.normalize(txt_com, dim=-1)
    score_s2v = s2v_n @ txt_single.T             # [B, C]

    # ═══ 阶段 F: 融合两个方向 ═══
    local_score = 0.5 * score_s2v + 0.5 * score_v2s  # weight_s2v=0.5
```

### V2S vs S2V 的直观理解

| 方向 | 含义 | 类比 |
|---|---|---|
| V2S (visual→semantic) | 视觉内容"翻译"成语义，然后和文本原型比对 | "我看到的东西，用文字描述后，最像哪个类别？" |
| S2V (semantic→visual) | 文本原型"翻译"成视觉，然后和图像特征比对 | "这个类别的文字描述，画出来应该长什么样？" |

两个方向互补：V2S 适合文本描述精确的类别，S2V 适合视觉特征突出的类别。

---

## 第九部分：GTPJ 主类（行 507-1357）

### __init__ 参数（行 510-521）

```python
def __init__(self, config, seenclass, unseenclass,
             seen_text_embeds, unseen_text_embeds,
             class_attr=None, attr_text_embeds=None,
             seen_sentence_embeds=None, unseen_sentence_embeds=None):
```

| 参数 | 形状 | 来源 |
|---|---|---|
| `config` | SimpleNamespace | YAML 配置文件 |
| `seenclass` | [150] | 数据集分割，150 个 seen 类全局编号 |
| `unseenclass` | [50] | 50 个 unseen 类全局编号 |
| `seen_text_embeds` | [150, 768] | GPT 描述的 CLIP 编码（训练时用） |
| `unseen_text_embeds` | [50, 768] | GPT 描述的 CLIP 编码（评估时用） |
| `seen_sentence_embeds` | [150, M, 768] | 句子级嵌入（PSE 自注意力用） |

### __init__ 结构分解

我把 `__init__` 按功能拆成 7 个部分：

#### 第 1 部分：注册固定数据（行 528-540）

```python
# 类别索引 — 不可训练，但要跟着模型上 GPU
self.register_buffer("seenclass", torch.as_tensor(seenclass, dtype=torch.long),
                     persistent=False)
self.register_buffer("unseenclass", torch.as_tensor(unseenclass, dtype=torch.long),
                     persistent=False)

# 原始文本嵌入 — 不可训练（CLIP 提取的，冻结）
self.seen_text_embeds = nn.Parameter(
    F.normalize(seen_text_embeds, dim=1),   # 归一化
    requires_grad=False                      # ★ 不参与训练
)
```

**为什么文本嵌入用 `nn.Parameter(requires_grad=False)` 而不是 `register_buffer`？**
因为存成 Parameter 才能被识别为"模型参数"的一部分，checkpoint 加载时更容易匹配。`requires_grad=False` 保证不会被 optimizer 更新。

#### 第 2 部分：PSE 配置（行 542-581）

```python
self.adapter_ratio = 0.2         # 瓶颈适配器用（v1）
self.use_clip_a_self = True      # v2+: 用自注意力
self.pse_outer_ratio = 0.65      # 增强文本和原始文本的混合比例

if self.use_clip_a_self:
    # 句子级嵌入 [150, M, 768]，不可训练
    self.seen_sentence_embeds = nn.Parameter(
        F.normalize(seen_sentence_embeds, dim=-1),
        requires_grad=False
    )
    # 自注意力模块
    self.clip_a_self_adapter = ProgressiveSemanticSelfAttention(
        dim=768, heads=4, dropout=0.5, inner_ratio=0.35
    )
else:
    # 回退：瓶颈适配器（v1 模式）
    self.text_adapter = SemanticPrototypeAdapter(768, reduction=4)
```

#### 第 3 部分：BVSA 配置（行 583-601）

```python
self.cross_tf = BidirectionalVisualSemanticAlignment(
    dim_f=768,       # CLIP 特征维度
    dim_com=512,     # Transformer 内部维度
    heads=4,         # 注意力头数
    dropout=0.1,
    weight_s2v=0.5, # S2V 和 V2S 各占一半
    grid_size=(24, 24),
    dim_g=64,        # 几何嵌入维度
    use_fgvd_geometry=True,
)
```

注意：`self.cross_tf` = `self.bvsa`（通过 `@property` 别名）。

#### 第 4 部分：SGMP 配置（行 603-637）

```python
self.use_sgmp = True
self.sgmp_context_mode = "fgvd_main_memory"  # 从哪里取上下文
self.sgmp_topk = 8                            # 掩码几个 patch
self.sgmp_neg_margin = 0.2                    # 负样本 margin

if self.use_sgmp:
    self.jepa_predictor = nn.Sequential(
        nn.Linear(1024, 512),  # 512(视觉上下文) + 512(文本) = 1024 → 512
        nn.LayerNorm(512),
        nn.GELU(),
        nn.Linear(512, 512),  # 预测被掩码的 patch 特征
    )
```

#### 第 5 部分：logit_scale（行 639）

```python
self.logit_scale = nn.Parameter(torch.ones([]) * np.log(1 / 0.07))
# 对标 CLIP：初始化 logit_scale = log(1/0.07) ≈ log(14.3) ≈ 2.66
# 在 forward 里：logit_scale = self.logit_scale.exp() ≈ 14.3
# 效果：S_final 乘以 ~14.3 的放大系数，让 softmax 更尖锐
```

#### 第 6 部分：FGVD 选择 + ICSA 配置（行 645-704）

```python
self.fgvd_select_k = 32              # 选几个 patch
self.fgvd_select_formula = "v2_abs_mean"

self.use_conditional_text = True     # 开启 ICSA
self.icsa_ratio = 0.008              # 注入比例（极小！）

if self.use_conditional_text:
    self.meta_net = nn.Sequential(
        nn.Linear(768, 48),     # ★ 768 → 48（极小瓶颈！）
        nn.LayerNorm(48),
        nn.GELU(),
        nn.Linear(48, 768),     # 恢复
    )
    # ★ 关键初始化：最后一层 weight=0, bias=0
    # 训练开始时 ICSA 输出为零，模型先学会用原始文本，再慢慢加入条件化
    with torch.no_grad():
        self.meta_net[-1].weight.zero_()
        self.meta_net[-1].bias.zero_()

self.bvsa_text_mode = "conditional"  # v5: BVSA 也用条件文本
self.sgmp_text_mode = "conditional"  # SGMP 也用条件文本
```

**为什么 ICSA 瓶颈是 48？** 三个原因：
1. 刻意限制表达能力，防止对 seen classes 过拟合（条件化太多会伤害 unseen 泛化）
2. 配合 `icsa_ratio=0.008`，ICSA 的总贡献 = 很小的网络 × 很小的比例 = 极小
3. 初始化 weight=0, bias=0 → 开始时为零注入，模型自然学到"少注入比多注入好"

#### 第 7 部分：DynamicRouting（行 706-745）

默认 `use_dynamic_routing=False`，所以这些 gate 不会被创建。只有当 config 里开启时才构造。

---

### GTPJ 的核心方法

#### `get_adapted_seen_text()`（行 850-885）

```python
def get_adapted_seen_text(self, return_gate=False):
    if self.use_clip_a_self:
        sentence_embeds = self.seen_sentence_embeds    # [150, M, 768]

        base = sentence_embeds.mean(dim=1)              # [150, 768] 原始平均
        # 自注意力在第 1 维（句子维）上操作
        attn = self.semantic_prototype_self_attention(sentence_embeds)
        attn = attn.mean(dim=1)                         # [150, 768] 增强后平均

        # ★ 残差混合
        adapted = 0.65 * attn + 0.35 * base
        return F.normalize(adapted, dim=1)
    else:
        # 回退：瓶颈适配器
        x = self.seen_text_embeds
        adapted = 0.2 * adapter(x) + 0.8 * x
        return F.normalize(adapted, dim=1)
```

#### `get_adapted_unseen_text()`（行 887-898）

```python
def get_adapted_unseen_text(self):
    # 默认不对 unseen 类做 PSE 增强
    # 原因：PSE 只在 seen 类上训练，扩展到 unseen 可能导致 unseen 泄漏
    return self.unseen_text_embeds
```

#### `_make_all_text()`（行 900-910）

```python
def _make_all_text(self, device, dtype, return_pse_gate=False):
    seen_text, pse_gate = self.get_adapted_seen_text(return_gate=True)
    unseen_text = self.get_adapted_unseen_text()

    # ★ 拼接成完整的 [200, 768] 张量
    all_text = torch.zeros(200, 768, device=device, dtype=dtype)
    all_text[self.seenclass] = seen_text     # 把 seen 文本放到正确位置
    all_text[self.unseenclass] = unseen_text
    # 注意：unseen 文本没有经过 PSE 增强，保持原始 CLIP 文本
    return all_text
```

---

### `GTPJ.forward()` — 完整前向传播（行 1093-1236）

这是框架的心脏。我逐段拆解：

```python
def forward(self, clip_features, is_train=False):

    # ══════════════════════════════════════════════════
    # 段 1: 拆出 CLS token 和 patch tokens
    # ══════════════════════════════════════════════════
    if clip_features.dim() == 3 and clip_features.size(1) == 577:
        cls_token = clip_features[:, 0, :]      # [B, 768]  ← 全局特征
        patches = clip_features[:, 1:, :]       # [B, 576, 768] ← 局部特征
    else:
        patches = self._prepare_patches(clip_features)  # 兼容不同形状
        cls_token = None  # 没有 CLS token

    # ══════════════════════════════════════════════════
    # 段 2: 准备文本原型 (PSE → all_text)
    # ══════════════════════════════════════════════════
    logit_scale = torch.clamp(self.logit_scale.exp(), max=100.0)
    # logit_scale ≈ 14.3，clamp 防止过大

    all_text, pse_gate = self._make_all_text(patches.device, patches.dtype,
                                              return_pse_gate=True)
    # all_text: [200, 768] — 完整的文本原型（seen 部分已 PSE 增强）

    # ══════════════════════════════════════════════════
    # 段 3: 计算图像全局特征
    # ══════════════════════════════════════════════════
    if cls_token is not None:
        vis_n = F.normalize(cls_token, dim=1)          # [B, 768] L2 归一化
    else:
        vis_n = F.normalize(patches.mean(dim=1), dim=1) # 没有 CLS 则用 patch 平均

    # ══════════════════════════════════════════════════
    # 段 4: ICSA → 图像条件文本 (all_text_cond)
    # ══════════════════════════════════════════════════
    if self.use_conditional_text and cls_token is not None and self.cond_text_ratio > 0:

        # 4a: ICSA 产生逐样本偏移向量
        pi_x = F.normalize(self.meta_net(cls_token), dim=-1)  # [B, 768]

        # 4b: 复制 all_text 到 batch 维度
        all_text_cond = all_text.unsqueeze(0).expand(B, -1, -1).clone()
        # [200, 768] → [B, 200, 768]

        # 4c: 只对 seen 类注入条件，unseen 类保持原样
        seen_idx = self.seenclass.to(patches.device)
        all_text_cond[:, seen_idx, :] = (
            all_text[seen_idx].unsqueeze(0)           # [1, 150, 768]
            + icsa_gate.unsqueeze(-1) * pi_x.unsqueeze(1)  # [B, 1, 768]
        )
        # 数学: all_text_cond[s] = all_text[s] + icsa_ratio × ICSA(cls_token)
        # icsa_ratio = 0.008，贡献极小

        # 4d: 归一化条件文本
        text_n_cond = F.normalize(all_text_cond, dim=-1)

        # 4e: 全局分数 = CLS_token · 条件文本 × 温度缩放
        s_global = (vis_n.unsqueeze(1) * text_n_cond).sum(dim=-1) * logit_scale
        # [B, 1, 768] × [B, 200, 768] → sum → [B, 200] × 14.3
    else:
        # 无 ICSA：直接用 all_text
        text_n = F.normalize(all_text, dim=1)
        s_global = vis_n @ text_n.T * logit_scale
        # [B, 768] × [768, 200] → [B, 200]

    # ══════════════════════════════════════════════════
    # 段 5: BVSA 局部分数
    # ══════════════════════════════════════════════════
    bvsa_text = all_text
    if self.bvsa_text_mode == "conditional":
        bvsa_text = all_text_cond  # ★ v5 关键：BVSA 用条件文本

    bvsa_out = self.bvsa(patches, bvsa_text, cls_token,
                         fgvd_select_k=32, ...)
    # 内部做了 FGVD 选择 + 几何编码 + V2S/S2V 解码

    s_local = bvsa_out["local_score"]  # [B, 200]

    # ══════════════════════════════════════════════════
    # 段 6: 分数融合
    # ══════════════════════════════════════════════════
    s_final = s_global + 0.2 * s_local
    # 固定加法：全局占主导 (0.2 的局部分数)

    # ══════════════════════════════════════════════════
    # 段 7: 输出（训练时切片 seen）
    # ══════════════════════════════════════════════════
    if is_train:
        logits = s_final[:, self.seenclass]    # 从 [B,200] 取 seen 列 → [B,150]
    else:
        logits = s_final                        # 保留全 200 类
```

---

### `GTPJ.compute_loss()` — 损失计算（行 1251-1357）

```python
def compute_loss(self, in_package):
    logits = in_package["logits"]         # [B, 150] 训练时
    labels = in_package["batch_label"]    # [B]
    seen_labels = self._global_to_seen_labels(labels)  # 全局类别号 → seen 内部编号

    # ── 主损失 ──
    loss_CE = F.cross_entropy(logits, seen_labels)
    loss = loss_CE

    # ── 一致性损失 (λ=0.05) ──
    # S_global(教师) 和 S_local(学生) 的分布应该一致
    base_p = F.softmax(S_global_seen / T, dim=-1).detach()  # 教师
    local_logp = F.log_softmax(S_local_seen / T, dim=-1)    # 学生
    loss_consist = F.kl_div(local_logp, base_p, reduction="batchmean") * (T*T)
    loss += 0.05 * loss_consist

    # ── 拓扑损失 (λ=0.1) ──
    # PSE 增强后的文本原型和原始文本原型的类间关系应保持
    loss_topo = self._topology_pearson_loss()
    loss += 0.1 * loss_topo

    # ── SGMP 损失 (λ_mpp=0.05, λ_neg=0.01) ──
    if self.use_sgmp:
        loss_mpp, loss_neg = self._semantic_guided_masked_prediction_loss(...)
        loss += 0.05 * loss_mpp + 0.01 * loss_neg

    # ── BMDD 损失 (λ=0.05) ──
    # S2V 和 V2S 两个方向互相蒸馏
    loss_bmdd = (T²/2) * (KL(V2S→S2V) + KL(S2V→V2S))
    loss += 0.05 * loss_bmdd
```

---

### `_topology_pearson_loss()`（行 912-955）

```python
def _topology_pearson_loss(self, enh_text=None):
    # 构建原始文本和增强文本的相似度矩阵
    base_text = [200, 768]  # 原始 CLIP 文本
    enh_text = [200, 768]   # PSE 增强后

    base_sim = base_text @ base_text.T   # [200, 200] 原始类间相似度
    enh_sim = enh_text @ enh_text.T      # [200, 200] 增强后类间相似度

    # 取非对角线（类间关系，不关心自己和自己的相似度）
    off_diag = ~torch.eye(200, dtype=torch.bool)
    base_vec = base_sim[off_diag]   # [200×199] 展开成一维
    enh_vec = enh_sim[off_diag]

    # Pearson 相关系数
    # r = Cov(X,Y) / (σ_X × σ_Y)
    enh_centered = enh_vec - enh_vec.mean()
    base_centered = base_vec - base_vec.mean()
    numerator = (enh_centered * base_centered).sum()
    denominator = sqrt((enh_centered²).sum()) * sqrt((base_centered²).sum())
    pearson_r = numerator / denominator

    return 1.0 - pearson_r  # 损失 = 1 - 相关性（最大化相关性 → 最小化损失）
```

**直观理解**：如果原始文本里"蓝鸦"和"蓝雀"很相似（都是蓝色），PSE 增强后它们也应该保持相似。如果拓扑损失低，说明增强没有破坏原始语义结构。

---

### `_semantic_guided_masked_prediction_loss()`（行 957-1043）

这是 SGMP 的核心，最复杂的单个函数：

```python
def _semantic_guided_masked_prediction_loss(self, patches, all_text, labels, ...):
    # 步骤 1: 选要掩码的 patch
    # 用类别文本去找哪几个 patch 和类别最相关（这些 patch 最有信息量）
    patch_n = F.normalize(patches, dim=-1)        # [B, N, 768]
    text_n = F.normalize(class_text, dim=-1)      # [B, 768]
    patch_score = einsum("bnd,bd->bn", patch_n, text_n)
    # 每个 patch 和当前类别文本的余弦相似度

    _, masked_idx = torch.topk(patch_score, k=8, dim=1, largest=True)
    # 选最相关的 8 个 patch → 掩码它们（预测它们最难，因为和信息最多）

    mask = torch.zeros(B, N, dtype=torch.bool)
    mask.scatter_(1, masked_idx, True)   # 被掩码 = True
    keep = ~mask                         # 保留 = False

    # 步骤 2: 用保留的 patch 构造上下文
    if sgmp_context_mode == "fgvd_main_memory":
        # 用主路径的 FGVD memory 作为上下文（已被几何编码器增强过）
        keep_f = keep.unsqueeze(-1).to(selected_memory.dtype)
        context = (selected_memory * keep_f).sum(dim=1) / keep_f.sum(dim=1).clamp_min(1.0)
        # 加权平均：只保留 unmasked token 的 memory

    # 步骤 3: 取被掩码 patch 的 patch_z 作为"真值"
    target = patch_z[mask].view(B, k, -1).mean(dim=1).detach()
    # 8 个掩码 patch 的平均特征 — 这是预测目标

    # 步骤 4: 用上下文 + 文本预测被掩码的内容
    text_z = self.bvsa.embed_text(class_text)       # [B, 512]
    pred = self.jepa_predictor(torch.cat([context, text_z], dim=-1))
    # 输入: [context(512) + text(512)] = [B, 1024]
    # 输出: [B, 512] — 预测被掩码 patch 的 512 维特征

    # 步骤 5: 正样本损失
    pos_sim = F.cosine_similarity(pred, target, dim=-1)
    loss_mpp = (1.0 - pos_sim).mean()   # 最大化余弦相似度

    # 步骤 6: 负样本损失
    neg_labels = (local_labels + 1) % 150  # 简单地取"下一个"类别作为负样本
    neg_pred = self.jepa_predictor(torch.cat([context.detach(), neg_text_z], dim=-1))
    neg_sim = F.cosine_similarity(neg_pred, target, dim=-1)
    loss_neg = F.relu(neg_sim - pos_sim.detach() + 0.2).mean()
    # 负样本的预测相似度应该比正样本低至少 0.2，否则惩罚
```

**直观理解**：如果你告诉模型"这是一只冠蓝鸦"（文本），并给它看图像中除了 8 个关键 patch 以外的其他部分（上下文），模型能不能"脑补"出这 8 个 patch 应该长什么样？能 → 模型学会了语义-视觉对齐。不能 → 惩罚。

---

## 你已经学会

- [ ] 整个 MyModel.py 的 1358 行代码，逐类、逐函数的作用
- [ ] `DynamicRoutingGate` 的 fixed/sample/class 三种模式
- [ ] `fgvd_select_patches` 的 FFT 频域分析原理
- [ ] `ProgressiveSemanticSelfAttention` 的双层残差混合（inner + outer）
- [ ] `BoxRelationalEmbedding` 的 4 维几何特征 → 64 维位置编码
- [ ] `GeometryMultiHeadAttention` 的"减几何偏置"操作
- [ ] BVSA 的 V2S 和 S2V 两个方向的区别
- [ ] GTPJ.forward 的 7 个阶段：拆特征 → 文本 → 全局 → ICSA → BVSA → 融合 → 输出
- [ ] 6 个损失函数各自的公式和作用
- [ ] `icsa_ratio=0.008` 为什么这么小
- [ ] ICSA `meta_net` 的权重零初始化技巧

准备好后 → 进入 [04 — 训练代码详解](04_training_explained.md)
