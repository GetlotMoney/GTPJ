# V5-INNOVATION-010：PSE + VSCE 双向交互

```yaml
experiment_id: V5-INNOVATION-010
idea_id: IDEA-0012
framework: FRAMEWORK-V5
status: planned
branch: exp/v5/innovation/innovation-010-pse-vsce
base_template: MODEL-V5-TEMPLATE-V1
base_template_tag: model/v5-template-v1
base_template_commit: 2f5fa5e631ef82658d4bac587cdfd17f3534cb35
parameter_matrix: PARAMETER_MATRIX.md
planned_run: RUN-001
```

## 先说结论

本实验只回答一个问题：用同一张“8 个句子 × 33 个视觉位置”的匹配表，同时选择句子和局部区域，是否比实验 A 只用全局图像选择句子更能提高 GZSL 的调和平均指标 `H`。

这里的 33 个视觉位置是 `1` 个全局特征加 `32` 个频域 Top-K 局部区域。实验 B 从 V5 干净母版独立开始，不继承实验 A 的实现。

## 公平比较边界

| 项目 | 固定设置 |
|---|---|
| 母版 | `MODEL-V5-TEMPLATE-V1@2f5fa5e631ef82658d4bac587cdfd17f3534cb35` |
| 数据与划分 | CUB，沿用 V5 seen/unseen 划分、类别顺序和标签映射 |
| 文本 | 每类固定 8 句话，`text_source=gpt56_8sent` |
| 局部区域 | 沿用频域筛选，`fgvd_select_k=32` |
| 训练 | seed=5，batch size=64，50 epoch，沿用 V5 三段学习率 |
| 融合 | `final_logits = global_logits + 0.2 × local_logits` |
| 损失 | 沿用 V5 的 CE、consistency、topology、BMDD、MPP 和 negative semantic loss；不新增全局或局部 CE |
| 运行数 | 仅 `RUN-001`，与实验 A 相同 |

## 8 句话

1. 喙
2. 头部特征
3. 身体羽毛
4. 翅膀
5. 尾巴
6. 腿部
7. 整体外观
8. 独特判别特征

加载时必须验证缓存形状为 `[200, 8, 768]`，不能静默接受 7 句话或临时补齐句子。

## 方法

### 1. PSE 保留 8 个增强句子

每类的 8 个 CLIP 文本向量先进入 PSE 做句间自注意力。PSE 输出仍是 8 个句子特征 `T[c,m]`，其中 `m=1..8`；不能在 VSCE 前直接求平均。

### 2. 建立统一匹配表

CLIP 视觉编码得到全局特征 `G[b]`，局部特征经过频域 Top-K 得到 `R[b,n]`，其中 `n=1..32`。把全局特征作为第 0 个视觉位置，得到：

```text
M[b,c,m,n] = CLIP_scale × cosine(T[c,m], V[b,n])
V[b,0] = G[b]
V[b,1..32] = R[b,1..32]
```

`M` 的形状是 `[B, C, 8, 33]`。训练和评估都令 `C=200`，保证 seen/unseen 走完全相同的 VSCE 计算；训练时只在进入母版现有损失时切 seen 列，实验 A 也使用同一计算范围。

### 3. 同一张表产生两个方向的权重

句子方向先对 33 个视觉位置做 `logsumexp`，再在 8 个句子上做 Softmax：

```text
sentence_evidence[b,c,m] = logsumexp_n M[b,c,m,n]
sentence_weight[b,c,m] = softmax_m(sentence_evidence)
prototype[b,c] = Σ_m sentence_weight[b,c,m] × T[c,m]
```

区域方向先对 8 个句子做 `logsumexp`，再只在 32 个局部区域上做 Softmax：

```text
region_evidence[b,c,n] = logsumexp_m M[b,c,m,n], n=1..32
region_weight[b,c,n] = softmax_n(region_evidence)
local_visual[b,c] = Σ_n region_weight[b,c,n] × R[b,n]
```

这里不增加可调温度；匹配尺度沿用 CLIP 的现有尺度。`logsumexp` 是本实验代码身份的一部分，不放进配置搜索。

### 4. 分类与融合

```text
global_logits[b,c] = CLIP_scale × cosine(G[b], prototype[b,c])
local_logits[b,c]  = cosine(local_visual[b,c], prototype[b,c])
final_logits       = global_logits + 0.2 × local_logits
```

匹配权重证据和全局 logits 使用 CLIP 的 `logit_scale`；局部 logits 有意保持原始余弦、不乘尺度，以匹配实验 A/V5 的局部分数量级。实验 B 删除当前 ICSA 的独立类别偏移，也不再单独运行 BVSA；VSCE 同时承担句子选择和局部区域选择。PSE、频域 Top-K 和 V5 其余训练语义保持不变。

为保证 A/B 配置字段尽量一致，`config.yaml` 仍保留 V5 原有 `icsa_ratio`、`icsa_hidden` 等字段；当 `interaction_mode=pse_vsce` 时，代码不得读取 ICSA 字段来生成偏移。

## 损失边界

本实验不借机重做损失：

- 主 CE 仍只作用于 `final_logits`；
- consistency loss 继续比较原有 global/local 分数语义；
- topology loss 沿用 V5 的公式、输入和 `lambda_topo_pearson=0.1`；
- topology 的静态输入仍是 seen 的 PSE 均值加 unseen 的原始均值，VSCE 条件原型不进入拓扑；
- BMDD 的双向输入保持未缩放余弦量级，MPP 和 negative semantic loss 继续读取同 shape 的语义/FGVD 张量；公式与权重不改；
- 不新增 `global_logits` CE，也不新增 `local_logits` CE。

如果替换交互模块后无法提供 V5 现有损失所需的同义输入，必须停止并修正接口，不能静默把损失关掉。

## 必须记录的诊断

- `sentence_weight [B,C,8]`，以及相对均匀权重 `1/8` 的熵和偏差；
- `region_weight [B,C,32]`，以及集中度、Top-1 原 patch 编号、`24×24` 坐标和非有限值检查；
- 受控真实类别样例的 Top-1 句子槽位，并将最佳轮诊断与最佳 checkpoint 锁定到同一 epoch；
- VSCE 匹配在合理句子与区域上的可解释样例；
- `global_logits`、`local_logits`、`final_logits`；
- 完整 `U/S/H/ZS`、最佳 epoch、训练墙钟时间；
- 峰值 GPU 显存、参数量、最佳模型文件大小；
- 相比实验 A 增加的时间和显存。

权重明细只保存受控诊断样本或汇总，不能把全部训练张量长期堆进 Git。

## 判断规则

- 先检查 `RUN-001` 是否完整、有限、可追溯，再比较 H。
- 同时报告相对 V5 和实验 A 的 `ΔU/ΔS/ΔH/ΔZS`，不能只挑 H。
- 只有一次运行时，结论只能写“首轮有效或无效信号”，不能声称提升已经超过重复训练波动。
- 若 B 的 H 没有超过 A，或额外时间/显存明显上升而收益很小，优先保留更简单的 A。

## Code Flow Diagram

代码输入、关键张量和损失出口见 [framework_diagram.md](framework_diagram.md)；本地可直接打开的自包含视图见 `framework_diagram.html`。
