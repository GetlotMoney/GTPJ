# ARTV 实现说明

## 一句话定义

ARTV 用冻结 CLIP 对同一测试图像的 15 个确定性裁剪重新编码，通过六个类别无关的
鸟体部位锚点形成固定视觉槽，再让 `6 局部 + 1 独特` 描述对 X2 top-2 投票；只有
至少 5/7 票支持第二名时，才交换 X2 的前两项。

## 输入输出契约

设样本、候选类、裁剪、特征维分别为 `B、C、P=15、D=768`：

| 名称 | shape / dtype | 梯度 | 含义 |
|---|---|---|---|
| `sentence_embeds` | `[200,8,D]` / float32 | 冻结 buffer | 6 局部、1 全局、1 独特描述 |
| `x2_prototypes` | `[200,D]` / float32 | 冻结 buffer | X2 最终单位原型，构造器不再归一化 |
| `image_features` | `[B,D]` | 强制 detach | 历史 official CLS，与 X2 基线一致 |
| `crop_features` | `[B,15,D]` | 强制 detach | 原图确定性裁剪的冻结 CLIP CLS |
| `role_anchors` | `[6,D]` | 冻结 buffer | 六个通用鸟体部位文本锚点 |
| `class_ids` | `[C]` / int64 | 无 | 当前竞争类的全局 ID，顺序就是 logits 顺序 |
| `final_logits` | `[B,C]` / float32 | 无 | 仅可能交换 X2 top-1/top-2 的最终分数 |

模块不接收 seen/unseen 身份，没有可训练参数，也没有 loss。

## 固定裁剪视图

每张原图按短边生成 `9 + 5 + 1` 个正方形区域：短边 0.5 的 3×3 网格、短边
0.7 的四角与中心、短边 1.0 的中心区域。每个区域使用 `clip.load` 返回的
ViT-L/14@336px 官方预处理独立编码。该视图不同于历史整图 CLS cache，且顺序固定。
4731 张 official 原图还按 `seen split 顺序 + unseen split 顺序` 对位置、长度和文件内容
计算统一 SHA-256；任一图片被替换或换位都会在加载 CLIP 前硬拒绝。
Runner 把已经校验 SHA-256 的权重绝对路径直接交给 `clip.load(..., jit=False)`，
并锁定 torch/torchvision/Pillow 版本、CLIP 源码与 BPE 词表摘要、六个锚点的最终
token 序列，以及去除进程地址后的预处理签名；确定性算法与 cuBLAS workspace 为强制开启。生成的 seen/unseen crop tensor
也分别写入 SHA-256，避免结果脱离其真实视觉证据。

## 逐步公式

### 1. 冻结 X2 候选对

```text
b(i,c) = scale_X2 · cos(x_i, z_c)
(c1,c2) = top2_c b(i,c)
```

内部候选轴先按全局 class ID 升序规范化；排序规则固定为“分数降序、同分时 class ID
升序”。因此 runner-up 精确同分和候选输入重排不会改变被验证的全局类别。

### 2. 全局描述给裁剪分配前景质量

```text
g_pair = normalize(g_c1 + g_c2)
row_mass_p = softmax_p(cos(v_p, g_pair) / ε)
```

`g_pair` 对两个候选完全对称，因此全局句不能直接偏向其中一类。

### 3. 解剖锚定传输形成六个固定视觉槽

令 `a_r` 为六个类别无关部位锚点，并增加一个 background 列。对
`cos(v_p,a_r)` 做带固定行质量、七列均匀质量的熵正则 Sinkhorn 传输：

```text
T = Sinkhorn(exp(sim(v_p,[a_1..a_6,bg]) / ε), row_mass, 1/7)
s_r = normalize(sum_p T_p,r · v_p / sum_p T_p,r), r=1..6
```

这里是带显式背景列的**平衡传输**，不是可学习检测器，也不声称是真实部位标注。

### 4. 七票证据

六个局部句只读同名视觉槽；独特句读取六槽中的最强匹配。先把冻结的原始文本向量单位化，
再按 200 个类别去掉每个角色的共享均值并重新单位化：

```text
t_c,r = normalize(raw_text_c,r)
mean_r = mean_c t_c,r
local_c,r = normalize(t_c,r - mean_r), r=1..6

u_c = normalize(raw_text_c,unique)
mean_u = mean_c u_c
unique_c = normalize(u_c - mean_u)
```

这里的中心化只使用全部 200 类的冻结文本语义，用来去掉“像鸟”之类跨类别共享方向；不读取图像、
不参与梯度，也不根据 seen/unseen 身份分支。随后，分数在当前候选类集合内标准化，再比较 X2
第二名与第一名：

```text
e_r = zscore_c cos(s_r, local_c,r)[c2] - zscore_c(...)[c1], r=1..6
e_u = zscore_c max_r cos(s_r, unique_c)[c2] - zscore_c(...)[c1]
vote_k = 1[e_k > 0]
certificate = sum_k vote_k >= 5
```

### 5. 有界输出

```text
certificate=false: final_logits = b
certificate=true : 只交换 b(c1) 与 b(c2)，其余 C-2 项逐元素不变
```

因此 ARTV 不会把 X2 top-2 之外的类别抬进第一名。

## 关闭路径与干预

- `artv_enabled=False`：不读取裁剪，直接调用 `base_logits`，逐元素退回冻结 X2。
- `role_description_permutation=[1,2,3,4,5,0]`：视觉槽不动，只错配六个局部描述。
- `unique_swap_with_runner_up=True`：只反转 unique 的 top-2 证据，六个局部证据不变。

## 评估边界

- GZSL：seen 1764 与 unseen 2967 图像都在 200 类联合竞争。
- ZS：同一 2967 unseen 图像只在 50 个 unseen 类竞争。
- 同次一次性报告 X2、ARTV、role-shuffle、unique-swap；不按结果改阈值。
- Owner 已指定直接 official，结果标记 `official-test-guided-development`。

## 最低验证

- ARTV-off 与 X2 bitwise 相同；新参数数目为 0。
- 开启后只允许交换原 top-2，两百类维度、全局类 ID 与 label mapping 不变。
- 候选类重排等变；role-shuffle 只改局部证据；unique-swap 只改 unique 证据。
- 裁剪数量、尺寸、顺序可重复；X2 checkpoint 重建保持旧 Uniform-PSE 语义。
