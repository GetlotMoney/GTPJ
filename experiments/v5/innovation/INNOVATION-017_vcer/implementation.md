# VCER 实现说明

## 一句话定义

VCER 冻结 PSE-X2 的全局类别原型；对每个图像—候选类选择其当前最强混淆类，
由独特描述决定六种局部差异的重要性，由全局描述判断 patch 是否像主体，最后用
同一 patch 上的候选—混淆类余弦差形成有界修正。

## 接口与张量

设 batch、候选类、patch、特征维分别为 `B`、`C`、`P`、`D`：

| 名称 | shape / dtype / device | 梯度 | 含义 |
|---|---|---|---|
| `sentence_embeds` | `[C_all, 8, D]` / float32 / module device | buffer，冻结 | 六局部、全局、独特描述证据 |
| `x2_prototypes` | `[C_all, D]` / float32 / module device | buffer，冻结 | PSE-X2 输出的类别原型 |
| `image_features` | `[B, D]` / 可转 float32 / 与 module 同 device | 强制 detach | CLIP CLS |
| `patch_features` | `[B, P, D]` / 可转 float32 / 与 module 同 device | 强制 detach | CLIP patch token |
| `class_ids` | `[C]` / int64 / module device | 无 | 本次竞争类的全局类别编号，顺序即 logits 顺序 |
| `final_logits` | `[B, C]` / float32 / module device | 有 | 保持原类别顺序的 VCER logits |

模块不接收 seen/unseen 标记。训练时调用方只能传训练 seen 类和 seen 图像；推理时
同一接口可以传 pseudo 的联合候选集或 official 的 200 类联合候选集。

`x2_prototypes` 必须是 X2 已经生成的最终 float32 单位原型。构造器只验证范数并
逐元素保存原值，禁止再次归一化；这是 `VCER-off` 与历史 X2 bitwise 等价的必要条件。

## 唯一新增参数

文本句子与 patch 共用一个低秩残差投影：

```text
f(x) = normalize(x + W_up GELU(W_down x))
W_down ∈ R^(r×D), W_up ∈ R^(D×r)
```

`W_up` 精确零初始化，所以初始 `f(x)=normalize(x)`。没有类别、角色、seen 或 unseen
专属参数。新增的**可训练参数键**只有 `down.weight` 与 `up.weight`；冻结句子、原型、
尺度和角色索引会作为 persistent buffers 一起进入 state dict。

## 逐步公式

### 1. 冻结 X2 底分与动态混淆类

```text
b(i,c) = cos(x_i, z_c)
q(i,c) = argmax_{j != c} b(i,j)
```

`z_c` 是冻结 X2 原型。每个候选都有自己的最强“其他类”作为反事实对象。

### 2. 独特描述路由六个局部角色

对局部角色 `r∈{0..5}`：

```text
d_local  = normalize(l_c,r - l_q,r)
d_unique = normalize(u_c - u_q)
a_r      = (1 - cos(l_c,r, l_q,r)) / 2
g_r      = (1 + cos(d_local, d_unique)) / 2
w_r      = normalize_over_roles(a_r * (1 + g_r))
```

若所有原始权重都为零，退回六角色均匀权重。unique 只负责“路由哪种局部差异”，
不直接作为第七个局部分类分支。

### 3. 同 patch 反事实边际

```text
m(i,c,p,r) = [cos(f(p_i,p), f(l_c,r))
              - cos(f(p_i,p), f(l_q,r))] / 2
```

相减发生在同一个 patch 上，避免把候选的最佳区域与混淆类的另一块区域做不公平比较。

### 4. 全局描述估计前景与可见性

```text
fg(i,c,p) = 1/2 + [cos(f(p),f(g_c)) + cos(f(p),f(g_q))] / 4
e(i,c,p,r) = fg(i,c,p) * |m(i,c,p,r)|
alpha_p = softmax_p(x2_scale * e)
v_r = max_p e
E_r = v_r * sum_p(alpha_p * m)
```

`fg`、`e` 与 `v` 均在 `[0,1]`。全局描述只判断候选和混淆类共同相关的主体区域，
不额外制造一个全局分类头。

### 5. 有界合成

```text
E(i,c) = sum_r w_r * E_r
s(i,c) = x2_scale * [b(i,c) + E(i,c)] / 2
```

`b` 与 `E` 都在 `[-1,1]`，固定等权平均，不引入 gamma 或可搜索融合系数。

## Loss

训练总损失为：

```text
L = CE(s, y)
  + lambda_unique * mean ReLU(m_unique - E_true + E_true_unique-swapped)
  + lambda_preserve * mean[1 - cos(f(t), t)]
```

默认 `m_unique=0.1`、`lambda_unique=1.0`、`lambda_preserve=0.05`。任一新增 loss
权重为零时对应项精确不进入总损失。unique-swap 把候选 unique 替换为其
动态混淆类 unique，但不改 X2 底分、rival、局部 margin 或前景项；它要求正确 unique
确实比错误 unique 更能支持真类证据。unseen 文本可以作为冻结语义参与保持约束，
unseen 图像不得进入梯度或 checkpoint 选择。

## 关闭等价与干预接口

- `logits(image_features, class_ids, *, patch_features=...)`：保留 X2 的前两个位置参数；
  patch 是 keyword-only，防止旧式调用把类别编号误当 patch。
- `evidence_enabled=False`：不读取 patch，逐元素调用冻结 `base_logits`，精确退回 X2；
  `training_loss` 同时只返回冻结底分的 CE，新增损失均为精确零。
- `unique_swap_with_rival=True`：只破坏 unique 路由，用于因果约束和消融。
- `local_source_ids`：只替换候选局部文本来源，底分与 rival 保持不变，用于跨类局部替换检查。
- `role_evidence_permutation`：保留 unique 产生的角色权重，单独重排它所接收的六路
  `role_evidence`，从而打破“角色语义—视觉证据”对应关系。把局部文本、权重和证据
  一起重排只是在重命名坐标，不是有效 role-shuffle。

## 当前未做

核心模块已接入 trial-local Runner 与冻结配置；训练启动前仍须通过 Runner 机器测试、
两轮顺序只读审核和 clean pre-run freeze。当前尚未读取 official test。
