# IDEA-0015：解剖锚定角色传输验证器（ARTV）

```text
idea_id: IDEA-0015
title: 解剖锚定角色传输验证器（ARTV）
status: developing
source_type: hybrid
source_ref: owner-codex:2026-08-17:ARTV_crop_grounded_top2_verifier
source_status: local_heuristic
global_score: 84.0
idea_dir: idea_tree/ideas/IDEA-0015_artv/
```

## 来源

Owner 要求保留 PSE-X2 的强文本原型，并让 `6 个局部 + 1 个全局 + 1 个独特`
描述真正产生可干预的视觉角色差异。只读 X2 top-k 诊断进一步发现，很多 official
错误的真实类别已位于第二名，因此把任务收窄为“验证 X2 top-2，而非重学分类器”。

## 基于什么

- base version：`v5`
- base code：`PSE-X2@a0ac9d8f82fef6022da5e823049b00760cd1fa2e`
- based on modules：冻结 PSE-X2、冻结 CLIP ViT-L/14@336px
- template family：`sampler_or_data_view + bounded verifier`

## 目标组件

冻结 X2 logits 之后的 crop-grounded top-2 验证：六个通用部位锚点形成固定视觉槽，
全局描述只给候选对提供对称前景质量，六个局部描述与一个独特描述组成七票证书。

## 假设

若 X2 的主要剩余问题是前两名次序错误，局部裁剪证据应能在不影响另外 198 类的前提
下救回一部分样本；若角色对应真实有效，打乱六个描述与固定视觉槽的对应关系应退化。

## 实现范围

- 新增 `INNOVATION-022_artv/artv.py` 与 training-free `evaluate.py`。
- 使用原始 official 测试图像的确定性 15-crop 冻结 CLIP CLS，不使用旧 patch cache。
- 0 个可训练参数、0 个新增 loss；证书固定为 5/7，不搜索 gamma 或阈值。
- 关闭时 bitwise 退回 X2；开启时只允许交换 X2 top-1/top-2。

## 版本评分

| 版本 | 分数 | 适用性 | 理由 |
|---|---:|---|---|
| `v5` | 84.0 | direct | X2 top-2 oracle 有明显空间，ARTV 保留 X2 且把八句分工转为可干预裁剪证据。 |

## 迁移说明

后续框架只要提供同维度的冻结类别原型、八句描述和原始图像即可复用；部位锚点应按
数据集对象重写，不能把 CUB 的鸟体锚点直接迁到非鸟类数据集。

## 风险

- 通用部位文本锚点不是真实检测框，可能错误分配背景裁剪。
- 5/7 证书可能过严或过松，但本轮固定不搜索，失败即停止。
- 直接 official 属于开发反馈，结果不能冒充 confirmation。

## 阻塞点

正式运行仅等待同一最终代码两轮审核与空闲 GPU。

## 决策规则

- 同次报告 X2、ARTV、role-shuffle、unique-swap 的 U/S/H/ZS。
- 主目标 `H>=75`；最低保留门为相对 X2 `ΔH>=+0.5`，且 role-shuffle 应明显退化。
- 不达门就停止 ARTV，不调证书阈值、不叠加失败模块。
