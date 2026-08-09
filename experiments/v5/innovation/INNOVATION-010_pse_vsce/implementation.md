# 实现约定

状态：`implemented_pending_run`。代码与目标测试已落地，尚未产生服务器正式训练结果。

## 最小改动范围

1. 训练入口加载 `gpt56_8sent`，并硬检查文本缓存为 `[200,8,768]`。
2. PSE 返回每类 8 个增强句子，不在进入 VSCE 前求均值。
3. 保留 V5 频域 Top-K，继续读取 `fgvd_select_k=32`。
4. 用 VSCE 替换 ICSA 和独立 BVSA 的交互职责。
5. 输出 global/local/final 三组 logits，并把 V5 现有损失所需的同义张量接回原损失函数。
6. 不增加新控制器，不修改评估口径，不增加额外全局或局部 CE。

句子缓存进入模型时先沿特征维逐句归一化，与母版一致；`enhanced = r × PSE(sentence) + (1-r) × sentence` 后不再逐句归一化，只有均匀或加权汇聚成类别原型后才归一化。这样统一权重严格退化到母版 PSE 原型。

## 张量契约

| 名称 | 形状 | 含义 |
|---|---|---|
| `text_sentence` | `[C,8,768]` | PSE 后的 8 个类别句子 |
| `global_visual` | `[B,768]` | CLIP 全局图像特征 |
| `local_regions` | `[B,32,768]` | 频域 Top-K 局部区域 |
| `match_table` | `[B,C,8,33]` | 8 个句子与 1+32 个视觉位置的 CLIP 尺度匹配 |
| `sentence_weight` | `[B,C,8]` | 每幅图像、每个候选类别的句子权重 |
| `region_weight` | `[B,C,32]` | 每幅图像、每个候选类别的局部区域权重 |
| `prototype` | `[B,C,768]` | 图像条件类别原型 |
| `local_visual` | `[B,C,768]` | 类别相关局部视觉特征 |
| 三组 logits | `[B,C]` | 全局、局部和最终分数 |

前向始终计算 `C=200` 个候选类别；训练主 CE、consistency 和 BMDD 只按母版方式切 seen 列，评估保留全部 200 列。这样 seen/unseen 共用完全相同的 VSCE 公式，并与实验 A 的计算范围一致。

## 固定公式

```text
M = CLIP_scale × cosine(text_sentence, concat(global_visual, local_regions))
sentence_weight = softmax_sentence(logsumexp_visual(M))
region_weight = softmax_local_region(logsumexp_sentence(M[..., local_regions]))
prototype = weighted_sum(sentence_weight, text_sentence)
local_visual = weighted_sum(region_weight, local_regions)
global_logits = CLIP_scale × cosine(global_visual, prototype)
local_logits = cosine(local_visual, prototype)
final_logits = global_logits + 0.2 × local_logits
```

`logsumexp`、匹配表与全局 logits 使用的 CLIP 尺度、8 句话和 Top-K 32 都是本实验定义，不做参数搜索。局部 logits 有意不乘 `logit_scale`，从而保持实验 A/V5 的原始余弦量级。

配置只比 V5 多出 `interaction_mode=pse_vsce`，并把 `text_source` 改为 `gpt56_8sent`。为保持 A/B 配置字段一致而保留的 ICSA 字段，在本路径中不得参与计算。

## 损失接口

沿用 V5 实际代码中的：

```text
CE(final_logits)
+ consistency(global_logits.detach(), local_logits)
+ topology 原公式
+ BMDD 原公式
+ MPP 原公式
+ negative semantic 原公式
```

不得新增 `CE(global_logits)` 或 `CE(local_logits)`。BMDD 的两路 `[B,C]` 输入由未乘 `logit_scale` 的原始余弦匹配表分别沿句子方向和区域方向加权汇聚，数值保持在 `[-1,1]`，避免放大辅助损失；不能通过设权重为零回避接口问题。拓扑损失单独沿用母版静态输入：seen 为 PSE 均值，unseen 为原始句子均值，VSCE 条件原型不进入拓扑。

## 诊断接口

前向输出或受控诊断钩子至少能取得：

- 句子权重、区域权重及其熵；
- 匹配表的有限值与集中度摘要；
- 受控真实类别样例的 Top-1 句子槽位、Top-1 原始 patch 编号及其 `24×24` 行列坐标；
- global/local/final logits；
- 运行时间、峰值显存、参数量和最佳模型大小。

最终 JSON 将最佳指标、最佳 checkpoint 和 `diagnostics` 锁定到同一个最佳 epoch；最后一轮只另存为 `last_epoch_diagnostics`，避免把两轮证据混在一起。

默认训练日志只写汇总，不保存每个 batch 的完整 `[B,C,8,33]` 张量。

## 失败即停止

- 文本缓存不是 8 句话；
- Top-K 不是 32；
- 权重或 logits 出现 NaN/Inf；
- 句子权重不能随图像或类别变化；
- seen/unseen 使用不同公式；
- V5 原有任一损失被静默跳过；
- 输出目录已存在并可能覆盖旧结果。

## 实现后验证

- 单元测试覆盖 shape、归一化、有限值、类别条件差异和 seen/unseen 同路径；
- 固定小张量手算核对两次 `logsumexp + softmax`；
- 验证 `final = global + 0.2 × local`；
- 验证关闭或删除 ICSA/BVSA 后没有残留调用；
- 运行一次最小 CUDA smoke 后，再启动 `RUN-001`。
