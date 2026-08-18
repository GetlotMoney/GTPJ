# GTPJ-v5 Modules

```text
version: v5
registry_level: formal_peer
derived_from_framework: FRAMEWORK-V3
framework_diagram: framework_diagram.md
config: experiments/v5/config.yaml
trial_framework_source: experiments/module_trials/IDEA-0002_fae_memory_jepa/TRIAL-003_conditional_bvsa_text/framework_diagram.md
```

## Module Table

| Module | Purpose | Input | Output | Config switch | Baseline-off behavior |
|---|---|---|---|---|---|
| Frozen CLIP ViT-L/14@336px | Fixed visual feature extractor. | image batch | `clip_features [B,577,768]` | external backbone setup | not switchable in GTPJ config |
| PSE / CLIP-A-self text adapter | Adapt seen-class GPT text prototypes before image conditioning. | class text features | `all_text [C,768]` | `use_pse_self_attention`, `pse_inner_ratio`, `pse_outer_ratio`; legacy `use_clip_a_self`, `clip_a_self_*` | disabling self-attention or using zero residual returns the raw/shared text path |
| ICSA conditional text adaptation | Inject image-conditioned semantic residuals into class prototypes. | CLS token and `all_text` | `all_text_cond [B,C,768]` | `use_icsa`, `icsa_ratio`, `icsa_hidden`; legacy `use_conditional_text`, `conditional_text_ratio`, `meta_net_hidden` | disabled or ratio 0 returns `all_text` |
| FGVD patch selection | Select local patches for the visual memory branch. | CLIP patch tokens | selected patches `[B,K,768]` | `fgvd_select_k=32`, `fgvd_select_formula=v2_abs_mean`; legacy `lastvit_select_*` | falls back to the parent local patch-selection behavior |
| FGVD geometry-aware visual memory | Encode selected patches into local memory. | selected patches | local memory `[B,K,512]` | `use_fgvd_geometry`; legacy `use_fae` | disabled returns non-geometry local memory path |
| BVSA bidirectional visual-semantic alignment | Produce local class scores through V2S and S2V decoders. | FGVD memory and text input | `S_local [B,C]` plus branch scores | `bvsa_text_mode=conditional`, `weight_s2v`, transformer config | `bvsa_text_mode=adapted` sends shared `all_text [C,768]` into BVSA, matching the older path |
| Local/global fusion | Combine global and local scores. | `S_global [B,C]`, `S_local [B,C]` | `S_final [B,C]` | `local_weight=0.2` | `local_weight=0` removes local branch contribution |
| Consistency / BMDD legacy loss | Keep global/local score behavior aligned. | global and local scores | scalar auxiliary loss | `lambda_consist`, `lambda_bmdd`; legacy `lambda_msdn` | lambda 0 removes the auxiliary loss |
| SGMP / AG-JEPA auxiliary training | Use FGVD memory and conditional text for semantic masked prediction and negative suppression. | FGVD memory, patch targets, conditional text | `L_mpp`, `L_neg` | `use_sgmp`, `sgmp_context_mode=fgvd_main_memory`, `sgmp_text_mode=conditional`, `lambda_mpp`, `lambda_neg`; legacy `use_ag_jepa`, `jepa_*` | disabled or lambda 0 removes auxiliary contribution |

## Config Switches

| Switch | Meaning |
|---|---|
| `bvsa_text_mode=conditional` | Main v5 route: BVSA consumes `all_text_cond [B,C,768]`. |
| `pse_outer_ratio=0.65` | Stronger text prototype residual than the v3/v4 confirmed config. |
| `icsa_ratio=0.008` | Conditional semantic injection strength. |
| `local_weight=0.2` | BVSA local score weight in final logits. |
| `sgmp_text_mode=conditional` | SGMP reads conditional text rather than shared class text. |

## Version Delta

Compared with `v3`, `v5` activates the TRIAL-003 conditional BVSA text path and freezes the `trial003-main100-069` source config. It is owner-activated for future tuning. Its repeat mean does not beat the stronger confirmed `v3/CONFIRM-001 local-v3-054` reference, so v5 must not be described as a stronger confirmed baseline.

## 2026-08-16 本地模块筛选清单

```text
evidence_level: local_debug_not_formal_evidence
seed: 5
purpose: 保留每次尝试的成功、失败和停止原因，防止跨对话丢失或重复实验
formal_use: 禁止用于 confirmation、promotion 或论文最终结论
```

本节记录当天所有实际产出指标的模块尝试，包括失败和技术性无效运行。除特别说明外，checkpoint 只由 seen 训练集内部验证或固定的 100/50 类不重叠 pseudo-GZSL 选择，official test 在选择后读取；但这些方案此前已有 test 暴露，且均为单 seed 本地调试，所以不是正式证据。

当前干净零号底座 `B0` 是冻结 CLIP CLS 与 GPT-5.5-derived 八角色文本的等权平均：旧 GPT-5.5 七句加本任务新生成的 `unique_discriminative_features`，不是历史原生 GPT-5.5 八句。其结果为 `U=66.8941 / S=66.3929 / H=66.6426 / ZS=81.5347`。

### 有意义的完整结果

| 尝试 | 主要结果 U / S / H / ZS | 同口径变化 | 结论 | 本地证据 |
|---|---|---|---|---|
| GPT-5.5 七句 RCE | 66.3257 / 67.0103 / 66.6663 / 82.2050 | 相对七句 Mean7 `ΔH=+0.5856` | 有数值信号；但 wrong-role control 仍较强，只作早期诊断 | `.runtime/rce_pse_debug_x1_20260816.json` |
| GPT-5.5-derived 八句 Mean8 | 66.8941 / 66.3929 / 66.6426 / 81.5347 | 相对七句 Mean7 `ΔH=+0.5619` | 固定为本批 B0；新增第八句没有拉低基线 | `.runtime/gpt55_8_e0_rce_20260816_v2.json` |
| GPT-5.5-derived 八句 RCE | 67.2046 / 68.8373 / 68.0111 / 82.8882 | 相对 B0 `ΔH=+1.3686` | 数值保留；wrong-role 只低 `0.0186 H`，角色对齐机制未被 control 支持 | `.runtime/gpt55_8_e0_rce_20260816_v2.json` |
| GPT-5.5-derived 八句 SharedPSE | 66.5120 / 75.2606 / 70.6163 / 82.6018 | 相对 B0 `ΔH=+3.9738` | 强参考基线，不算自有创新；role scorer 约 `99.82%` 集中于 head，解释性塌缩 | `.runtime/gpt55_8_shared_pse_metrics_20260816.json` |
| 旧 ABLATION-011 + TransZero 风格 patch margin | 68.8885 / 76.7650 / 72.6138 / 79.0953 | 相对旧 global-only `H=74.1118`，`ΔH=-1.4980` | **失败，停止**；直接视觉 patch 残差同时损害 U/H/ZS | `.runtime/transzero_visual_debug_20260816.json` |
| 旧 PSE + 视觉分支联合训练 | 71.3740 / 76.6811 / 73.9324 / 81.2669 | 相对 matched J0 `ΔH=-0.1630` | **失败，停止**；联合训练没有带来增益 | `.runtime/transzero_joint_local_20260816/metrics.json` |
| ICRP，图像条件竞争角色原型 | 63.4205 / 78.2277 / 70.0502 / 80.5921 | 相对 matched J0 `ΔH=+0.0221` | **无实质增益，停止**；复杂度不值得约 0.02 H | `.runtime/icrp_full_20260816/metrics.json` |
| CRTP，反事实角色迁移原型，100 epoch | 58.7654 / 85.3066 / 69.5913 / 79.5756 | 相对 matched B0 `ΔH=+0.3519` | 弱正信号但 seen-heavy，未达到强模块门槛，暂停 | `.runtime/crtp_full100_20260816/metrics.json` |
| RCG，角色组合竞争图 | 67.5688 / 67.2816 / 67.4249 / 82.2746 | 相对 B0 `ΔH=+0.7823` | **保留调试候选**；U/S/ZS 同时提高，仍需正式化与多 seed | `.runtime/rcg_full_20260816/metrics.json` |
| RCG + SPV，空间持续验证 | 63.0602 / 63.4423 / 63.2507 / 79.7322 | 相对 RCG `ΔH=-4.1742` | **失败，停止**；patch 空间证据未迁移 | `.runtime/spv_full_20260816/metrics.json` |
| RCG + RSMR，角色语义流形重构 | 61.1166 / 64.5505 / 62.7867 / 79.0766 | 相对 RCG `ΔH=-4.6383` | **失败，停止**；视觉重构严重破坏迁移 | `.runtime/rsmr_full_20260816/metrics.json` |
| RCG + CSRT，类别特定球面角色迁移 | 68.1592 / 67.4532 / 67.8044 / 82.3148 | 相对 RCG `ΔH=+0.3795`；相对 B0 `+1.1618` | **保留调试候选**；U/S 同升，但权重约 `72.42%` 集中 overall，需机制验证 | `.runtime/csrt_full_20260816/metrics.json` |
| RTA-PSE，seen-CE 强训练 | RTA：57.8365 / 75.4406 / 65.4759 / 81.5347；加 RCG 后 H=67.1105 | RTA 相对 B0 `ΔH=-1.1667`；加 RCG仍比 RCG低 `0.3144 H` | **失败，停止强训练路线**；注意力能学，但造成严重 seen bias | `.runtime/rta_pse_full_v2_20260816/metrics.json` |
| RTA-PSE，100/50 类不重叠选择 | RTA：67.0330 / 68.1011 / 67.5628 / 81.5347；加 RCG 后 H=68.1356 | 加 RCG相对 RCG `ΔH=+0.7107` | 数值诊断保留；角色注意力近均匀，不能证明 attention 选择机制 | `.runtime/rta_pse_class_disjoint_20260816/metrics.json` |
| RTA-PSE + 文本区分度先验 | RTA：64.3623 / 68.1682 / 66.2106 / 81.5347；加 RCG 后 H=67.5155 | RTA 相对 B0 `ΔH=-0.4320`；加 RCG仅比 RCG高 `0.0906 H` | **失败，停止**；让注意力有语义偏好后反而降低迁移 | `.runtime/rta_pse_class_disjoint_v2_20260816/metrics.json` |
| RICA-v0，固定图像—竞争角色交叉注意力 | 66.9581 / 67.5741 / 67.2646 / 82.7402 | 相对 B0 `ΔH=+0.6221`；相对均匀 margin `ΔH=-0.0406` | **机制失败，停止 v0**；attention entropy 为均匀上限的 `98.3%`，动态注意力没有优于均匀证据 | `.runtime/rica_identity_20260816/metrics.json` |
| CRGT，类别关系图球面原型迁移 | 44.9582 / 86.9047 / 59.2597 / 70.4803 | 相对 B0：`ΔU=-21.9360 / ΔS=+20.5118 / ΔH=-7.3829 / ΔZS=-11.0544` | **失败，停止**；seen CE 把原型强烈拉向 seen，base/prototype cosine 降至 `0.6340`，跨类关系正则未阻止迁移崩溃 | `.runtime/crgt_full100_20260816/metrics.json` |
| DATA-PSE，双锚迁移注意力 | DATA：67.1029 / 68.0926 / 67.5941 / 81.5347；加 RCG：67.7767 / 69.0065 / 68.3861 / 82.2746 | 加 RCG相对 RCG `ΔH=+0.9612`；相对 B0 `+1.7435` | 数值诊断保留，但 attention entropy=`2.07944≈ln(8)`，近均匀；**不能作为注意力创新证据** | `.runtime/data_pse_dual_anchor_20260816/metrics.json` |

### Smoke、修复性重跑和技术失败

这些运行不能冒充独立科学结论，但必须保留，避免以后把技术失败误认为模块失败，或重复运行同一无效设置。

| 尝试 | 结果 | 处理 |
|---|---|---|
| TransZero 联合训练 1 epoch smoke | `H=74.1775`，相对 J0 `+0.0151` | 仅证明入口可跑；后续 11 epoch 同口径转为 `-0.1630`，按完整结果停止 |
| ICRP smoke-1 | `U/S/H=NaN` | **技术失败**；指标输出无效，不用于判断模型，随后修复并重跑 |
| ICRP smoke-2 | `H=66.6343`，相对 J0 `-0.0280` | 修复后入口有效，继续完成 30 epoch |
| CRTP 1 epoch smoke | `H=66.9786`，相对 B0 `-0.3171` | 仅入口检查；继续完成 50/100 epoch |
| CRTP 50 epoch | `H=69.2102`，相对 B0 `+0.3502` | 中间完整运行；100 epoch 增益仍约 `+0.35`，未继续扩张 |
| RCG 2 epoch smoke | `H=66.7440`，相对 B0 `+0.1014` | 入口和梯度有效，随后完成 200 epoch |
| RTA-PSE 初版 | 与 B0 完全相同，effective angle=`0` | **技术失败**；零输出初始化切断有效学习，不作为科学反例；修正后结果见强训练路线 |

### 当前收口决定

- 保留：RCG、RCG+CSRT 的正增益信号；CRTP 只保留为弱信号，不优先扩张。
- 只作参考：SharedPSE 的 `H=70.6163`，因为其骨架来自 CLIP-A-self/PSE，且角色权重塌缩，不能冒充自有创新。
- 明确停止：TransZero 风格 patch margin、联合视觉分支、ICRP、SPV、RSMR、RTA 强训练、带文本先验的 RTA、RICA-v0 固定交叉注意力、CRGT 类别关系图迁移。
- DATA-PSE 与 class-disjoint RTA 的数值可以保留，但近均匀注意力否定了“学会哪句话重要”的机制主张；后续不得只凭 H 重新包装为注意力创新。
- 上述所有结果均为本地 debug；在代码冻结、两轮审核、正式参数表和多 seed 完成前，不晋级为正式实验事实。

### 本地证据 SHA256

```text
85fcbc23a20e2350b5ada76aa8467e616bc495de4c947422985ffc66961ce368  .runtime/rce_pse_debug_x1_20260816.json
e2a1f8c85d9d901941f6a9f6e698d3439ff6e8aee409efcebba53df0f6d4c4e0  .runtime/gpt55_8_e0_rce_20260816_v2.json
4e1b76a8d58a2d111f37ad1aba8412c83af8edf8fc00a5db6302cd2415976eff  .runtime/gpt55_8_shared_pse_metrics_20260816.json
ef8851f50b3f5b56cb9952d2067eeae087276f23f2e9e04614178655ac3fa7bf  .runtime/transzero_visual_debug_20260816.json
40077d04f53f8f5373ab612f34d86f376a1f91b3ee20897e79adb80650fe7d9f  .runtime/transzero_joint_smoke_20260816/metrics.json
6ee6759245678252cfe95062d9404bafd8558af565b70064654642f3339a9882  .runtime/transzero_joint_local_20260816/metrics.json
6dbda9382e613e9b8c321dc077009fe61149b0f48d28af65fd7ed9e47c486fe1  .runtime/icrp_smoke_20260816/metrics.json
e7ddf6a521465b3c6d0a3ba8f6dca1edd1f1f33843881ada7b57a0027687784f  .runtime/icrp_smoke2_20260816/metrics.json
eaddcfc38c222f9402724d36df49d91c233149daf2cd5ba7c33592c00e0e8a39  .runtime/icrp_full_20260816/metrics.json
9fa21330f371fd9f49d1d1ef75b773a4ec3d77f2bf00bb64d9e6e81a963e7f57  .runtime/crtp_smoke_20260816/metrics.json
80386e66f7c55f1561f7c04068abaacc1d855e65f60777cb611087c78d9e4d77  .runtime/crtp_full_20260816/metrics.json
31e5c37bdef8de80234a1ece291f0f95130da35a89603a4269466231f0c4477f  .runtime/crtp_full100_20260816/metrics.json
b983817b717be7d102af8be889f1eaf61cf5abd271725ae2070d0ec98921fd2e  .runtime/rcg_smoke_20260816/metrics.json
15df1bc2521177a9f18e7456c83066d499ecba6b87aef85245e152991ff5b22c  .runtime/rcg_full_20260816/metrics.json
dec0fc6de378e189b865c9de440a0d713bed409d400dff6d37eb8a4a4990f10b  .runtime/spv_full_20260816/metrics.json
b7b47b9bc73c1f648e421d8962e355901683d9baf669ca3fb23d3c96fdca75c3  .runtime/rsmr_full_20260816/metrics.json
29a245914682d150eb5babaa0c574c4287e65697a76357985f66d22a8a4089f6  .runtime/csrt_full_20260816/metrics.json
1a9ea13f09b8646a052a36c4cb4ed832df1aab35d9b40dac8031085d6b88e877  .runtime/rta_pse_full_20260816/metrics.json
dd3e7afc74a138c1541b801416b6cd23979419e3418e1eaf452ed8645e81d3bc  .runtime/rta_pse_full_v2_20260816/metrics.json
f437061cc743f5145a5534d0d0a4cbc900fe95cf928bad40e7653b397bfab195  .runtime/rta_pse_class_disjoint_20260816/metrics.json
2e3cfd67621092c814230a19091d194e2e2d0e83ba81468b1ed8ff492535158f  .runtime/rta_pse_class_disjoint_v2_20260816/metrics.json
8dd132e9cc6c171562d54eb31bd2ef865b2aab1c8f61959081c7512321152e07  .runtime/rica_identity_20260816/metrics.json
3eb8fd8f56984644ed8e432a4354bb77563c4f09722a23fa1d0e997df913298c  .runtime/crgt_full100_20260816/metrics.json
9cee18a7165c4611cf7b115f3050c4058e9f80ae66103e2ac52cb1c582186d19  .runtime/data_pse_dual_anchor_20260816/metrics.json
```

以后每次实际运行都必须在本节追加一行：即使是 `NaN`、无增益、代码错误或被停止，也要写清“和谁比较、完整指标、失败属于技术问题还是科学问题、证据路径”。不得只记录成功结果。

## 创意框架效果总账规则

本文件同时承担 V5 创意框架效果清单。每次提出或实际运行一个创意框架，都必须保留一条记录；不能只记录成功实验，也不能用“效果很好”“达到 76+”代替完整指标。

每条记录至少包含：

1. 创意名称、解决的问题和核心结构；
2. 唯一变化与直接比较基线；
3. 完整 `U / S / H / ZS` 及 `Delta H`；
4. checkpoint 与参数如何选择，official test 是否参与选择；
5. 证据路径或正式实验 ID；
6. `保留 / 停止 / 技术失败 / 待验证` 结论和原因；
7. 下一步只允许的一个最小动作。

尚未运行的创意也必须登记，但效果统一写 `pending`，不得预填预期增益。技术失败与科学无增益分开记录，修复性重跑不得冒充新的创意结果。

### 本地优先与 GitHub 同步边界

当前采用“本地筛选，候选晋级后一次性同步 GitHub”的方式：

1. **本地探索阶段**：允许快速实现和运行，不为每个小尝试创建正式 GitHub 实验；但每次运行都必须在本清单记录创意、唯一变化、配置/命令、数据与划分、代码身份或快照、完整指标、比较基线、证据路径、失败类型和下一步。
2. **本地停止阶段**：无增益、机制控制失败或技术路线被否定时，如实保留结果与停止原因，不为它继续扩展，也不要求单独同步 GitHub。
3. **候选晋级阶段**：只有原始 `H` 有明确正增益、`U/ZS` 未发生不可接受退化、机制控制支持核心主张的候选，才从准确本地代码快照建立正式实验，补齐参数矩阵并按相同语义复跑。
4. **GitHub 同步阶段**：候选正式结果完成后，一次性提交轻量代码、配置、参数矩阵、结果摘要和证据索引；原始数据、checkpoint、大日志仍留在本地或 Warehouse。
5. **不得挑选性隐瞒**：晋级候选所依赖的负控制、失败消融和边界结果必须随正式候选一起同步；“只同步效果好的候选”不等于删除或隐藏反例。

本地 debug 数字不能仅通过复制到正式账本就升级为论文证据；必须绑定可恢复的代码/配置身份，并按冻结后的相同实验语义完成正式复跑。普通本地试验不触发代码审核；只有候选晋级并修改正式代码或评估语义时，才进入项目规定的两轮审核。

### 已完成的正式创意实验补录

| 创意 / 实验 | 核心结构 | U | S | H | ZS | 相对基线 | 证据等级与结论 |
|---|---|---:|---:|---:|---:|---|---|
| `V5-INNOVATION-017` RPR | 八角色低秩分离残差 | 45.918182 | 59.510756 | 51.838248 | 66.249114 | 相对 Mean8 `Delta H=-14.804328` | 正式 seed-5；原型位移破坏分类几何，`stop_no_gain` |
| `V5-INNOVATION-018` DPEF | seen 强原型与 shared 原型双专家融合 | 73.206306 | 79.987937 | 76.447016 | 82.601786 | 相对 SharedPSE `Delta H=+5.830668` | official-test 341 点 score search；只证明已披露 test 上限，`not_confirmation_evidence` |
| `V5-INNOVATION-019` RCDP | 角色对比位移原型 | 64.528239 | 68.248612 | 66.336303 | 82.041609 | 相对 Mean8 `Delta H=-0.306272` | 100/50 validation 选 epoch、test 一次；`stop_no_gain` |
| `V5-INNOVATION-020` RACE | 同角色竞争证据加数 | 66.967028 | 66.120547 | 66.541096 | 81.270540 | 相对 Mean8 `Delta H=-0.101480` | no-contrast 反而更高、wrong-role 几乎不变；机制不成立，停止 |
| `V5-INNOVATION-021` FRPE | 忠实角色 patch 证据 | 66.766822 | 67.184049 | 66.974786 | 81.540906 | 相对 Mean8 `Delta H=+0.332210` | 100/50 validation 选强度、test 一次；低于 `+0.50 H` 保留门，停止 |

对应正式证据分别位于 `warehouse://runs/v5/innovation/V5-INNOVATION-017..021/` 及各实验分支的 `result.md`。DPEF 的 `76.447016` 不得写成无 test 调参的最终成绩。

### 当前下一批创意与最小验证顺序

| 顺序 | 创意 / 条件 | 唯一变化 | 当前效果 | 进入或停止条件 |
|---|---|---|---|---|
| `PSE-A` | GPT-5.5-derived 八句旧强 Uniform-PSE | 无 ICSA、无局部、无 gamma；保留旧 V/O 投影、LayerNorm、强残差与 `topology=0.1` | `completed_anchor_below_target` | `H=69.758734`，形成干净锚点，但没有恢复历史约 74 |
| `PSE-B` | topology 单变量消融 | 相对 PSE-A 只改 `topology: 0.1 -> 0` | `completed_keep_as_control` | `H=71.032353`；topology 相对本条件使 H 降低 `1.273620` |
| `PSE-C` | DCRA-PSE 强可解释角色原型增强 | 相对 PSE-A 仅把固定均匀角色聚合替换为有界同角色竞争权重；seen-only 原型边界、topology 和训练制度不变 | `stop_no_gain` | `H=69.748157`，比 PSE-A 低 `0.010577`；不启动机制控制 |
| `PSE-X1` | 简化 Uniform-PSE + 旧训练协议 | 相对 PSE-A 改为全量 7057 seen、旧随机抽样、固定 epoch 50 | `completed_protocol_diagnostic` | `H=71.432564`；完整训练协议相对 PSE-A 为 `+1.673831 H` |
| `PSE-X2` | 精确旧 Uniform-MHA + 同一训练协议 | 相对 X1 只恢复旧 MHA 初始化、attention-weight dropout 和逐句训练路径 | `completed_strong_mother_baseline` | `H=73.523304`；相对 X1 为 `+2.090740 H`，基本恢复旧强能力 |
| `PSE-RBD` | RBD-PSE 角色均衡偏移增强 | 相对 X2 只在 Value context 中加入八个零初始化、跨类别共享的中心化角色偏移门；其余完全不变 | `stop_no_gain` | `H=73.454085`，相对 X2 为 `-0.069220 H`；不启动控制或融合 |
| `PSE-BRVM` | BRVM-PSE 有界角色关系混合 | 回到 X2，以零初始化、行归一且正值有界的 `8x8` 矩阵学习“目标角色←来源角色”Value 传递 | `stop_no_gain` | `H=73.523304`，与 X2 完全相同；矩阵变化未改变最终准确率 |
| `PSE-RC-GDT` | 邻域一致性球面位移迁移 | 从 X2 提取 seen 球面位移，经共享重建权重、平行运输和一致性门迁给 unseen；100/50 validation 只选一个 `lambda` | `stop_no_official_gain` | validation `+5.655250 H`，但 official test 仅 `+0.009078 H`；停止，不启动机制控制 |
| `PSE-D` | validation-selected 双原型融合 | 在 pseudo-GZSL 上选择 X2/SharedPSE 的 seen/unseen 原型融合，不使用 gamma | `stop_no_official_gain` | validation 选出退化边界 `a=0,b=1`；official `H=73.673362`，相对 X2 仅 `+0.150057` |
| `PSE-E` | CF-Role 同角色反事实约束 | 只交换易混淆类别的同一角色，要求正确类分数下降 | `not_started_blocked_by_main_module` | 主模块未成立，不为凑第三模块启动 |

执行顺序固定为 `PSE-A -> PSE-B -> PSE-C -> PSE-X1 -> PSE-X2 -> PSE-RBD -> PSE-BRVM -> PSE-RC-GDT -> PSE-D`；每个失败候选都回到 X2，不在失败模块上继续堆叠。`PSE-E` 仅在主模块已经有效后验证解释机制。

### 2026-08-16 PSE-A/B/C 本地筛选结果

三组在同一冻结提交、配置、seed、GPT-5.5-derived 八句、seen 内部 90/10 validation 和 official test 一次的协议下完成。`PSE-C` 的公式在读取 A/B official test 前已冻结；三组都没有 ICSA、局部分支、gamma 或 test 选模。

| 条件 | U | S | H | ZS | best epoch | 相对 Mean8 | 直接结论 |
|---|---:|---:|---:|---:|---:|---:|---|
| Mean8 | 66.894132 | 66.392905 | 66.642576 | 81.534684 | - | - | 同次冻结基线 |
| PSE-A：Uniform + topology 0.1 | 59.232157 | 84.835458 | 69.758734 | 81.534684 | 50 | `+3.116158 H` | topology 将模型进一步推向 seen，未恢复历史约 74 |
| PSE-B：Uniform + topology 0 | 61.954880 | 83.226490 | 71.032353 | 81.534684 | 38 | `+4.389778 H` | 本轮最佳；说明强 V/O/LN/残差有效，但 topology 在当前协议下有害 |
| PSE-C：DCRA + topology 0.1 | 59.231591 | 84.805340 | 69.748157 | 81.534684 | 50 | `+3.105581 H` | 相对 PSE-A `-0.010577 H`，角色竞争权重没有贡献，停止 |

随后完成旧强能力缺口诊断。X1/X2 使用同一个独立 CPU batch generator，保证 50 epoch 的每一批训练样本相同；两组都使用全量 seen、旧式每 step 随机抽样、固定 epoch 50、`topology=0.1`，不使用 validation 或 test 选模。

| 条件 | U | S | H | ZS | 相对 Mean8 | 直接结论 |
|---|---:|---:|---:|---:|---:|---|
| PSE-X1：简化 Uniform + 旧训练协议 | 62.081873 | 84.099525 | 71.432564 | 81.534684 | `+4.789989 H` | 相对 PSE-A `+1.673831 H`，完整训练协议解释一部分差距 |
| PSE-X2：精确旧 Uniform-MHA + 同一协议 | 73.395479 | 73.651576 | 73.523304 | 81.534684 | `+6.880729 H` | 相对 X1 `+2.090740 H`；旧训练算子是主要缺失项 |
| PSE-RBD：X2 + 中心化角色偏移门 | 73.294330 | 73.614538 | 73.454085 | 81.534684 | `+6.811509 H` | 相对 X2 `-0.069220 H`；U/S 同时小降，未过 `+0.30 H` 门，停止 |
| PSE-BRVM：X2 + 有界 `8x8` 角色关系矩阵 | 73.395479 | 73.651576 | 73.523304 | 81.534684 | `+6.880729 H` | 与 X2 完全相同；关系矩阵没有改变最终准确率，停止 |

PSE-X2 的 seen 原型与 Mean8 的平均 cosine 为 `0.504602`，几乎复现历史旧 PSE 的约 `0.506`；X1 为 `0.679438`。因此旧强能力的本质已经得到直接证据：不是 topology、ICSA 或句子 Q/K 选择，而是完整 MHA Value/Output 初始化、attention-weight dropout、逐句 projection/dropout、LayerNorm 与强 residual 共同形成的大幅原型重参数化。PSE-X2 仍属于旧 PSE/CLIP-A-self 路线，只能作为后续自有注意力方法的强母体，不能直接冒充项目原创模块。

运行身份：PSE-A/B/C 为 `commit:15d39f363c04a0762780c8f4bf738fe913a57c0e`、配置 SHA-256 `5ee0e9796e69949b0e33802e407310db766b9ca213ba92b7d883d74dcbb6f708`；PSE-X1/X2 为 `commit:a0ac9d8f82fef6022da5e823049b00760cd1fa2e`、配置 SHA-256 `4d7a0c1ffc4fbdd592fbf63e41506e66cd0d3037381c2e8dc8c10130986a59d6`；PSE-RBD 为 `commit:8e611ce210814f6ab88b7f0e017ab5958437bcbf`、配置 SHA-256 `170d0da8a3cb4b2a1f1b63a728b7e3aab8e34b2a44147d77839aa5be1a9482bd`；PSE-BRVM 为 `commit:22e0f31655a19127c6e6b78aa9e0ca55e4d67d72`、配置 SHA-256 `1bbeb61393deafe7d895d223e1daa92f660977e7871ebfb85335c2c9aa0691bf`；seed 均为 `5`。证据位于 `warehouse://runs/v5/local_trials/DCRA-PSE-20260816/RUN-001..007/`；每个目录保留 `training.log`、`metrics.json` 和 `model_best.pth`。RUN-006 的日志、指标和 checkpoint SHA-256 分别为 `30d29c141a4ca9e0c2a48db2c8039996adf6a78efdb74e2bcc68ae5e1b8937af`、`846129352ec9e474ec036624a34304849a7cb4cf5f0438819bafa28ea10ddce7`、`ba7fc067e87dbef591449dc59db1ce4fc2c71d5871757dac49c716130b0bbdf0`；RUN-007 对应为 `4ebb7f28768edf663f4e617f91fc627cb6c396a1618b4ef0d10934b09714fabf`、`bf6452e683b2a0301e4cb2aace7010765376dc6c3b263e98b246bacf99518e66`、`21387dfef4d96a8d1ac2db5beb566ad8d94eb8c5b73d0fc933a5379f759a7e59`。本轮为完整本地筛选证据，`formal_evidence=false`，尚未同步 GitHub 正式实验账本。

## 旧强 PSE 到自有新 PSE 主线

本节是当前 PSE 路线的权威汇总。目标不是继续修补较弱的 SharedPSE，而是先复原旧 PSE 的强原型重写能力，再只替换其无效或不可解释的部分，最终形成两个主模块：

1. **主模块一尚未成立**。RBD-PSE 相对 X2 下降 `0.069220 H`；BRVM-PSE 与 X2 完全相同。两者均已拒绝，下一候选仍须从 X2 独立出发。
2. **双原型融合已验证但未成立为主模块**。RUN-010 只在 100/50 validation 冻结系数，最终选择 `a=0,b=1`，official H 相对 X2 仅 `+0.150057`；说明强 seen 专家与 shared unseen 专家略有互补，但没有达到独立模块最低 `+0.30 H`，已停止。
3. **可选模块三：CF-Role**。只在前两个模块已有效后验证同角色反事实约束；无独立增益或机制控制失败就删除，不为凑数量保留。

### 已完成证据

| 证据 | U | S | H | ZS | 评估与选择口径 | 已证明什么 |
|---|---:|---:|---:|---:|---|---|
| 历史 GPT-5.5 Mean7 | 66.197741 | 65.964007 | 66.080668 | 81.238914 | 冻结 CLIP，只读重算 | 七句原始文本锚点 |
| `V5-INNOVATION-008/RUN-007` 旧 PSE 公平基线 | 71.25 | 76.30 | 73.69 | 81.32 | 第 50 epoch 后 official test 一次 | 旧 PSE 相关完整 V5 组合确实达到约 73.7；不是纯 PSE |
| `V5-ABLATION-011` global-only | 71.410584 | 77.025419 | 74.111807 | 81.272805 | 每轮看 official test，并按 test H 选 epoch 33 | 无局部分支仍可约 74.11；包含 seen-only PSE、ICSA、CE、`0.1 topology`，不是严格单模块结果 |
| 当前 GPT-5.5-derived Mean8 | 66.894132 | 66.392905 | 66.642576 | 81.534684 | 固定推理，无训练 | 第八句相对 Mean7 约 `+0.5619 H`，八句话不是下降原因 |
| 当前 SharedPSE | 66.511977 | 75.260586 | 70.616348 | 82.601786 | seen 内部 validation 选 checkpoint，official test 一次 | 相对 Mean8 `+3.973772 H`，但仍比旧 74 路径弱；role scorer 约 `99.82%` 集中到 head |
| `V5-INNOVATION-018` DPEF 上限诊断 | 73.206306 | 79.987937 | 76.447016 | 82.601786 | official test 上搜索 341 个融合点 | 强原型与迁移原型具有超过 75 的容量；这是 test-exposed 上限，不是可报告的干净最终成绩 |

历史结果文件：`innovation/INNOVATION-008_pse_class_relation_calibration/result.md`、`ablation/ABLATION-011_current_global_only/result.md`。当前八句证据：`.runtime/gpt55_8_e0_rce_20260816_v2.json`、`.runtime/gpt55_8_shared_pse_metrics_20260816.json`。

### 旧注意力是否真正有效

`V5-ABLATION-012` 的 8 个服务器完成运行已经逐项核对，但本地 GitHub 轻量账本仍是 `ready_to_run`，尚未回填。这里先保留真实结果，状态标为 `server_verified_ledger_pending`：

| 条件 | RUN | seed | U | S | H | ZS | best epoch |
|---|---|---:|---:|---:|---:|---:|---:|
| Uniform attention | RUN-001 | 5 | 72.563004 | 75.611079 | 74.055691 | 81.174588 | 31 |
| Uniform attention | RUN-002 | 5 | 72.800291 | 75.967604 | 74.350231 | 81.476247 | 31 |
| Uniform attention | RUN-003 | 17 | 71.130252 | 77.351779 | 74.110672 | 81.647509 | 31 |
| Uniform attention | RUN-004 | 17 | 72.063565 | 76.171339 | 74.060536 | 81.347936 | 33 |
| Learned Q/K, no Q/K decay | RUN-005 | 5 | 72.695112 | 76.052445 | 74.335890 | 81.744051 | 36 |
| Learned Q/K, no Q/K decay | RUN-006 | 5 | 72.494018 | 75.706285 | 74.065338 | 81.247938 | 31 |
| Learned Q/K, no Q/K decay | RUN-007 | 17 | 71.836162 | 76.300198 | 74.000919 | 81.290662 | 38 |
| Learned Q/K, no Q/K decay | RUN-008 | 17 | 72.502553 | 75.956494 | 74.189345 | 81.349647 | 33 |
| Uniform 四轮均值 | - | 5/17 | 72.139278 | 76.275450 | 74.144282 | 81.411570 | - |
| Learned 四轮均值 | - | 5/17 | 72.381961 | 76.003855 | 74.147873 | 81.408074 | - |

Learned 与 Uniform 的均值只差 `+0.003591 H`。因此，旧 PSE 的强能力不能归因于 Q/K 学会了“哪句话重要”；更可信的来源是整条 V/O 投影、额外 projection、LayerNorm、强残差与 CE 驱动的原型重参数化。ABLATION-012 的正式目录结果页和参数矩阵仍待回填，完成回填前不得把本表称为 GitHub 已闭环账本。

### 已完成诊断与边界

| 诊断 | 结果 | 能说什么 | 不能说什么 |
|---|---|---|---|
| 旧 ABLATION-011 checkpoint 关闭 ICSA | `H=74.192959`，完整模型 `H=74.111807` | ICSA 不是该 checkpoint 的直接推理增益来源 | 不是重训消融，不能排除 ICSA 的训练期影响 |
| 旧 checkpoint 关闭 PSE、保留 ICSA | `H=66.1892` | 约 74 的输出差异主要经过 PSE 强路径产生 | 不能把约 8 H 全部写成 PSE 的独立因果增益 |
| 旧 checkpoint 同时关闭 PSE 与 ICSA | `H=66.0531` | 与原始文本路径接近，支持“旧 PSE 是强原型重写器” | 仍是 post-hoc 开关，不是公平重训 |
| 原型移动 | 旧 seen 原型与 base 平均 cosine 约 `0.506`，约旋转 `59.5°`；SharedPSE cosine 约 `0.9968`，约旋转 `4.6°` | 新旧性能差首先对应原型改写强度差 | 不能据此单独确定最优旋转角度 |
| 旧选模偏差 | epoch 33 `H=74.11`；epoch 50 约 `H=73.72` | test 选点可见抬高约 `0.39 H`，但解释不了全部差距 | 旧 `74.11` 不能直接当严格新基线 |
| topology 现状 | 当前干净配对：topology 0.1 的 `H=69.758734`，topology 0 的 `H=71.032353` | 在当前八句、validation 选模的强 Uniform-PSE 中，topology 使 `H` 降低 `1.273620`，不是旧约 74 的直接来源 | 单 seed 不能断言 topology 在所有训练制度下都无效 |

上述 checkpoint 开关属于本轮只读诊断，尚无独立正式实验目录；它们只用于确定下一步，不作为论文因果结论。

### 尚未完成的问题

| 缺口 | 状态 | 为什么必须做 |
|---|---|---|
| 当前八句上的旧强 Uniform-PSE + `topology=0.1` 干净锚点 | `completed_H69.758734` | 已排除历史七句、ICSA、局部分支和 test 选模混杂；结果低于历史约 74 |
| 同一模型 `topology=0` 配对 | `completed_H71.032353` | 当前协议下 topology 贡献为 `-1.273620 H` |
| DCRA-PSE 最终公式 | `frozen_before_test` | 已在读取 PSE-A/B official test 前冻结，避免根据测试结果反向改公式 |
| DCRA-PSE 与旧强 PSE 同底座直接比较 | `stop_no_gain_H69.748157` | 相对同 topology 的 Uniform PSE-A 为 `-0.010577 H`，未形成创新增益 |
| 精确旧强 PSE 母体恢复 | `completed_H73.523304` | 已确认精确旧 Uniform-MHA 算子相对简化实现贡献 `+2.090740 H`；后续新注意力必须以此为母体 |
| RBD-PSE 冻结公式 | `stop_no_gain_H73.454085` | `u_r + tanh(theta_r)*(v_r-mean_s(v_s))`；实现严格退回 X2，但实测相对 X2 `-0.069220 H`，不保留为有效模块 |
| BRVM-PSE 冻结公式 | `stop_no_gain_H73.523304` | 矩阵从均匀值发生轻微变化，但 U/S/H/ZS 与 X2 完全相同，不保留为有效模块 |
| 双原型融合的 validation-selected 版本 | `stop_no_official_gain_H73.673362` | validation 选出 `a=0,b=1`；official 仅比 X2 `+0.150057 H`，历史 DPEF `76.447` 仍只是 test-exposed 上限 |
| CF-Role 第三模块 | `not_started_blocked_by_main_module` | 主模块未成立，不为凑数量启动 |
| ABLATION-012 GitHub 轻量账本回填 | `ledger_pending` | 服务器结果已存在，但当前目录仍错误显示未运行 |

### 下一步最小实验矩阵

| 阶段 | 条件 | 唯一变化 | 选择规则 | 结果门槛与后续 |
|---|---|---|---|---|
| 1A | `PSE-A` 旧强 Uniform-PSE + topology | GPT-5.5-derived 八句；无 ICSA、无局部、无 gamma；保留旧 V/O、projection、LayerNorm、inner/outer residual | seen 内部 validation 选 checkpoint；official test 只评一次 | 先得到干净锚点；若明显低于历史末轮约 73.7，先查训练制度，不进入新模块 |
| 1B | `PSE-B` topology-off | 相对 1A 只改 `0.1 -> 0` | 与 1A 完全相同 | 直接记录 `PSE-A - PSE-B`；不预设 topology 一定有效 |
| 2 | `PSE-C` DCRA-PSE 主运行 | 相对 1A 固定 `topology=0.1`，只替换注意力/角色聚合；seen-only 边界保持一致 | 公式、配置和停止门在读取 1A/1B official test 前冻结；同一 validation 规则，test 一次 | `H >= PSE-A`，且相对 Mean8 至少约 `+4 H`；U/ZS 不可明显塌陷 |
| 2-control | Uniform、head-only、role-shuffle | 仅在 DCRA 主运行有正结果后启动 | 不参与挑 test 最优 | DCRA 必须胜过 Uniform，且 role-shuffle/head-only 应破坏其主张；否则不把“角色注意力”写成创新 |
| 2B | `PSE-RBD / RUN-006` | 以 X2 为母体，只新增八个中心化 Value 偏移门；其余训练、topology、seed、batch 与 epoch 完全相同 | 固定 epoch 50；checkpoint 保存后才读取 official test | 已完成：相对 X2 `-0.069220 H`，按冻结门停止，不调 gate 或 gamma |
| 2C | `PSE-BRVM / RUN-007` | 回到 X2，只把 uniform Value mixing 换成有界 `8x8` 角色关系矩阵 | 固定 epoch 50；checkpoint 保存后才读取 official test | 已完成：指标与 X2 完全相同，按门槛停止，不调 `rho=0.5` |
| 3 | `PSE-D / RUN-010` 双原型融合 | X2 seen 专家 + SharedPSE 共享原型；无 gamma | 固定 100/50 类不重叠 validation 冻结融合；official test 一次 | 已完成：`H=73.673362`，相对 X2 `+0.150057`，低于门槛并停止 |
| 4 | `PSE-E` CF-Role | 在前两模块上新增同角色反事实约束 | validation 冻结；test 一次 | 必须有独立增益并通过 wrong-role/random；否则删除 |

DCRA-PSE 已在读取 PSE-A/B official test 数字前冻结：视觉中心只由 90% seen 训练样本生成；对每个类别的八个角色，分别计算“本类视觉中心与本类角色文本的相似度”减去“与 199 个其他类别同角色文本的最大相似度”，再将八个 margin 标准化。最终角色权重为 `0.8/8 + 0.2*softmax(margin)`，因此每个角色权重严格位于 `[0.10, 0.30]` 且总和为 1，结构上禁止单角色 99.82% 垄断。它保留 PSE-A 的旧强 V/O 投影、projection、LayerNorm、inner/outer residual、seen-only 原型边界和 `topology=0.1`，唯一替换的是 uniform 角色聚合。八个角色的 logit 加数可以精确相加还原最终分数。冻结身份：`commit:15d39f363c04a0762780c8f4bf738fe913a57c0e`，配置 SHA-256 `5ee0e9796e69949b0e33802e407310db766b9ca213ba92b7d883d74dcbb6f708`；实测 `H=69.748157`，相对 PSE-A `-0.010577 H`，已按 `stop_no_gain` 停止。

### 当前进度勾选

- [x] 找到旧约 73.69 与 74.1118 的真实账本和组件边界。
- [x] 证明八句话本身没有拉低 Mean 基线。
- [x] 证明旧 Learned Q/K 相对 Uniform 只增加约 `0.0036 H`。
- [x] 定位旧强 PSE 的核心是强原型重参数化，而不是句子重要性选择。
- [x] 确认 DPEF `H=76.447016` 只代表 test-exposed 容量上限。
- [ ] 回填 ABLATION-012 的正式轻量账本。
- [x] 完成 PSE-A 当前八句干净旧强锚点：`H=69.758734`。
- [x] 完成 PSE-B topology 单变量消融：`H=71.032353`，topology 当前贡献 `-1.273620 H`。
- [x] 在查看 PSE-A/B official test 前冻结 DCRA-PSE 公式、配置和停止门槛（`commit:15d39f3`）。
- [x] 完成 DCRA-PSE 主运行：`H=69.748157`，相对 PSE-A 无增益，按门槛停止且不跑机制控制。
- [x] 完成旧强能力缺口诊断：X1 `H=71.432564`，X2 `H=73.523304`；训练协议与精确旧算子分别解释主要差距。
- [x] 基于 PSE-X2 强母体冻结 RBD-PSE 公式、单次 RUN-006 配置与停止门；旧 PSE 本身只作来源基线，不能直接改名。
- [x] 运行 RBD-PSE / RUN-006：`H=73.454085`，相对 X2 `-0.069220 H`；按冻结门停止，未跑机制控制。
- [x] 冻结 BRVM-PSE 公式、RUN-007 配置和停止门；该公式在查看 RUN-007 official test 前固定。
- [x] 运行 BRVM-PSE / RUN-007：`H=73.523304`，与 X2 完全相同；按冻结门停止，未跑机制控制。
- [x] 完成 RC-GDT / RUN-008：原始门与 H 目标冲突，按原规则停止且 official test 未读取。
- [x] 完成独立 RC-GDT / RUN-009：100/50 validation 选出 `lambda=0.8`，official test 只评一次；`H=73.532382`，相对 X2 仅 `+0.009078`，停止。
- [x] 完成无 official-test 选参的双原型融合 / RUN-010：validation 选出 `a=0,b=1`，official test 只评一次；`H=73.673362`，相对 X2 仅 `+0.150057`，停止。
- [ ] CF-Role：当前被未成立的主模块阻断，未启动。

固定执行顺序：PSE-RBD、PSE-BRVM 与 PSE-RC-GDT 均已失败并停止。下一候选必须继续从 X2 独立派生，不调已失败模块的 gate、矩阵预算、迁移强度、残差或 gamma，也不启动融合或第三模块。

### 2026-08-16 CHORM：冻结 X2 上的角色视觉度量

本轮只做一个新模块，不叠加失败模块、不调 gamma。CHORM 冻结 PSE-X2 的类别原型和分数，只学习一个跨类别共享的低秩视觉位移；主组使用 8 个角色门控，对照组把 8 个角色绑成同一个门。每个角色的最终加数为“位移后图像与同角色文本的相似度变化”，8 项可精确相加还原最终分数。它不改文本原型、不做角色 attention、不使用类别专属参数。

| 条件 | RUN | 划分 | 当前状态 | 通过条件 | 结果 |
|---|---|---|---|---|---|
| `CHORM-TIED` | RUN-011 | xlsa17 100/50 pseudo-GZSL | `completed_stop_no_gate` | 共享门控对照，不单独晋级 | `U/S/H/ZS=58.941698/88.595092/70.788380/81.248832`；相对 pseudo-X2 `+0.246971 H` |
| `CHORM-ROLE` | RUN-012 | 同一 100/50 pseudo-GZSL | `completed_stop_no_gate` | 相对 X2 `ΔH>=+0.5`、相对 tied `ΔH>=+0.3`、相对 role-shuffle `ΔH>=+0.3`，且 U/S 各自下降不超过 0.5 | `58.983362/88.595092/70.818419/81.290495`；相对 X2 `+0.277010 H`，相对 tied `+0.030039 H`，shuffle 后 H 不变，U 下降 `1.292747` |
| `CHORM-ROLE final` | RUN-013 | 标准 CUB 150 seen 训练、150+50 GZSL 测试 | `not_started_gate_failed` | 只有 RUN-012 同时通过全部 pseudo 门才启动；官方 test 在 checkpoint 保存后只评一次 | 未创建目录、未读取 official test |

冻结身份：`commit:d44bf2e8c9b472a671012a70978e8132049795ee`，配置 SHA-256 `3acfbebcb1ca4188933dd3035388cb001e7530c054bd7afced9b4592d83930fe`。RUN-011/012 可以双卡并行，但必须使用同一 pseudo split、seed 和 X2 训练协议；50 个 pseudo-unseen 类只提供标准 GZSL 文本语义，其图像不进入梯度或 checkpoint 选择。RUN-013 入口必须读取两份 pseudo `metrics.json`，复核代码/配置/split/X2 哈希及全部增益门后才允许创建输出目录。结果均为本地筛选证据，`formal_evidence=false`。若 RUN-012 未过门，RUN-013 不运行，CHORM 如实记为失败候选并回到 X2。

真实 pseudo-X2 基线为 `U/S/H/ZS=60.276109/85.020852/70.541409/80.279356`。RUN-011 与 RUN-012 的 split SHA 均为 `9c61cd5da54afe07bd95a89b3075436deb2fbf329cbe4a332e388fdc6346a284`，pseudo-X2 prototype SHA 均为 `109e1d91d011e35ff42c2ec79ad42d7aa8dc25b3467857dfb57acc9b29c7cf3c`，两卡比较口径一致。ROLE 的八组 gate 均值仅落在 `1.0815..1.0845`，角色置换后 U/S/H 完全不变，说明角色门退化成近似共享视觉变换，没有形成角色特异证据。

证据位于 `warehouse://runs/v5/local_trials/CHORM-20260816/`。RUN-011 的 `training.log / metrics.json / model_best.pth` SHA-256 分别为 `b13601d6df59e73aa3e78d90567d8b0ebe7aea2f8cf9a58ba3c167fb05ff90e8`、`294827eca1aaadd6eef929422e7d6fb9cb0a52cc19007ba877801d66b49b309a`、`ad6cd2af770e2efbccc7679b9557f13ba1af3a04cfa1ecaaf50ff46b90c60f27`；RUN-012 对应为 `57c8d406dd3c2ce7dd2578b7221c2b08ea9e4c49b78c858620d0cedf9af8bd89`、`cae07eced5f3b53c23d36c9fad40f9bf5aea3e75392d81dd958183478f4d2fdd`、`b78103e89cc3d0602690239eef75ca5fac7c3c583baad897b23cd5ff04fdab55`。

- [x] 冻结 CHORM 公式、两条件、100/50 门槛与输出目录。
- [x] 新代码及 X2 回归测试通过（最终 commit 44 项；含零初始化首次反传和 final 跨 RUN 门控测试）。
- [x] 两轮顺序只读审核均通过并绑定 `commit:d44bf2e8c9b472a671012a70978e8132049795ee`，阻断为 0。
- [x] 双卡完成 RUN-011 / RUN-012，并回填 U/S/H/ZS、模型与日志 SHA。
- [x] RUN-012 未过四项 pseudo 门；RUN-013 明确不运行，CHORM 按 `stop_no_gate` 关闭。

### 2026-08-16 RC-GDT / RUN-008、RUN-009：强位移的未见类迁移验证

| 项目 | 冻结内容 |
|---|---|
| 要解决的问题 | X2 已恢复强 seen 原型能力，但 unseen 仍保持 Mean8；验证 seen 学到的强位移能否在不共享整个 PSE 算子的前提下迁移给 unseen。 |
| 核心结构 | `Log` 提取 X2 的 seen 球面位移；一个非负且和为 1 的权重向量共同重建目标类八个角色；位移平行运输到 unseen 切空间；多邻居方向一致性门控制是否回退 Mean8。 |
| 唯一选择量 | `lambda=0.0..1.0`，步长 0.1；不调 gamma、attention、topology、adapter 或局部分支。 |
| 严格验证 | xlsa17 `train_loc/val_loc` 构成 100/50 类不重叠 pseudo-GZSL；pseudo-seen 每类留出 20% 图像评估 S；pseudo-unseen 图像不参与梯度。 |
| official test 门 | RUN-008 原门额外要求 pseudo-S 下降不超过 0.20；RUN-009 独立冻结为 `Delta pseudo-H>=+0.30` 且 pseudo-U 严格提高。两者都只允许 validation 选 lambda，过门后 official test 最多一次。 |
| validation 效果 | 两次确定性复现同一曲线：pseudo baseline `U/S/H/ZS=60.276109/85.020852/70.541409/80.279356`；最佳 `lambda=0.8` 为 `76.972997/75.435823/76.196658/80.829543`，`Delta H=+5.655250`。 |
| RUN-008 状态 | `completed_stop_by_original_gate`；按预先冻结的 S 硬门停止，official test 读取与评估次数均为 0，原判定不回写。 |
| RUN-009 official | `lambda=0.8`；`U/S/H/ZS=79.257989/68.578279/73.532382/82.232767`。相对 X2 为 `Delta U=+5.862510`、`Delta S=-5.073297`、`Delta H=+0.009078`、`Delta ZS=+0.698084`。 |
| 当前结论 | `stop_no_official_gain`。方法在 pseudo split 上学到强烈的 U/S 再平衡，但没有迁移成 official H 增益，不能作为主模块或 75+ 证据；不继续调 lambda，也不启动控制组。 |
| 代码与配置 | RUN-008：`commit:7b10bf2fed5fb40d73fff5b53887b1e2d4a7fa60`，配置 SHA `fcf7e3dfe2871e318b4a955909ab2583d5b39d812ecc62fe11b7c571664886f3`。RUN-009：`commit:f970dc3a6d27682b9fc63a994e71135f8b73ed2b`，配置 SHA `017d1825371c02fa46005cfb5d7a736c51edb92e373803c28a6f6378b7fa58e2`。 |
| 下一步唯一动作 | 回到 X2，设计新的强主模块；RC-GDT 不再扩网格、改 gate、加 gamma 或叠加其他失败模块。 |

- [x] RC-GDT RUN-008 的 100/50 pseudo-GZSL 主验证完成并回填完整 U/S/H/ZS。
- [x] RUN-008 未过原始 S 硬门，official test 明确未触达；`official_input_sha256=null`、`official_test_evaluations=0`。
- [x] RUN-009 按修正后的 H 目标门通过 validation，随后 official test 恰好评估一次；最终 H 仅比 X2 高 `0.009078`，按主模块最低增益门停止。

RUN-008 证据位于 `warehouse://runs/v5/local_trials/DCRA-PSE-20260816/RUN-008/`。`training.log`、`metrics.json`、`pseudo_x2.pth` SHA-256 分别为 `ee79bfb4ab5e4e6c510ae1e37a902fb2090b8cfe45625bb1e933b72da9217193`、`436d0ac5cecea6378703f6cb7e0d30487b77bfdef5ff0c1877abf1180272f0bb`、`f05a82699f9a460861bf19a14e8d322c4d22caba1ab42fa5047b623dd1a69fa4`。RUN-009 对应 `training.log`、`metrics.json`、`pseudo_x2.pth` SHA-256 为 `b8f5c662aee9170bb9250c5e0cc42eeeab3b6433e5c9d576891052212afa5bcf`、`f123c9681c7d695f0021df6625d6ee7e19cdc99353c483b162cae47442a885a4`、`41be2ddf78040599061c2ef6b7e340d64924e6ef11c1151b66a4a9d10bef6895`。两次 simplex projected residual 均约 `9.2e-10`；50 个 pseudo-unseen 类从未参与梯度。RUN-008 的原始失败门与 RUN-009 的正式无增益结论都必须保留，不能改写成成功模块。

### 2026-08-16 DPEF validation / RUN-010：双原型融合重验

本轮冻结原 INNOVATION-018 的 341 点融合网格，但不再在 official test 上搜索。pseudo-X2 与 pseudo-SharedPSE 都只用 xlsa17 的 100 个 pseudo-seen 类训练；每类 20% 外层图像只评 pseudo-S，50 个 pseudo-unseen 类图像只做外层验证。SharedPSE 还在外层训练行内另留 10% 选择 epoch，最佳为 100；外层 seen 和全部 pseudo-unseen 图像均未进入梯度或 checkpoint 选择。

| 条件 | a | b | U | S | H | ZS |
|---|---:|---:|---:|---:|---:|---:|
| pseudo X2-seen + raw-unseen 控制 | 0.00 | 0.00 | 60.276109 | 85.020852 | 70.541409 | 80.279356 |
| pseudo SharedPSE 全类别控制 | 1.00 | 1.00 | 69.750005 | 75.091738 | 72.322370 | 81.877404 |
| pseudo validation 选择 | 0.00 | 1.00 | 67.506129 | 83.319658 | 74.583898 | 81.877404 |
| official 标准 GZSL | 0.00 | 1.00 | 77.678543 | 70.060951 | 73.673362 | 82.601786 |

选择点 `a=0,b=1` 表示 seen 原型完整使用 X2、unseen 原型完整使用 SharedPSE，341 点搜索没有支持连续“融合”本身；它只支持两类采用不同已有专家。official 相对 X2 为 `Delta U=+4.283065`、`Delta S=-3.590626`、`Delta H=+0.150057`、`Delta ZS=+1.067102`，低于预先冻结的 `+0.30 H` 最低门，因此记为 `stop_no_official_gain`，不继续缩网格、调 gamma 或包装成主模块。

运行身份为 `commit:893e862b6599b1771e6c597d9c372a914d130278`，配置 SHA-256 为 `aa9fcfde438433c618ce64efeda61a4b90a5f9f4a2cb650eee956bc600557065`；两个最终来源 checkpoint SHA 分别为 X2 `a0d8465d3a716ec52d197c8ca10ab9e70dff73d09fe56099e38d8270ee7243f3` 与 SharedPSE `f83adac761d9a8e5f4df1864a38fd427dac7c1fe2cf215697155d959dd71035e`。RUN-010 的 `training.log`、`metrics.json`、`pseudo_experts.pth` SHA-256 分别为 `8e49195fb51d20944572939767184fb178035497d94cba3c4b139dd5e269a957`、`579aae032158641ae518ce3f1e76abda50fab031fd60f9d9d3d195e828f520bf`、`1a1237e8fe8051e97f420f2450c8e4b601592db25e879d168f7caf4ff2d6c1db`。official test 未用于选 `(a,b)` 且只评一次；但同一网格历史上已在 test 暴露，因此证据等级仍为 `validation-selected recheck / formal_evidence=false`。

### 2026-08-16 干净三模块框架与 HSP-PSE 主模块筛选

干净框架固定为一条全局语义主路和一条小视觉残差：模块一 HSP-PSE 用 `6 个局部 + 1 个独特 + 1 个全局` 生成强语义原型；模块二 HSTB 负责把 seen 学到的可靠角色位移迁移给 unseen；模块三 VEC 用冻结 CLIP patch 生成有界、可删除的局部与独特视觉证据。HSTB 与 VEC 只有在 HSP 主模块先通过时才实现和运行；当前不叠加失败候选、不使用 gamma。

HSP-PSE 不使用 Q/K 或句间 attention。八句先分别执行共享 `WV -> GELU -> WO -> 0.65/0.35 residual -> LayerNorm`，再形成角色位移；六个局部固定等权平均，独特与全局各自保留一组位移。三组独立 sigmoid 门的上限为 `local/unique/global=0.65/0.325/0.1625`，初始化为 `0.4875/0.08125/0.08125`。只改训练 seen 类，pseudo-unseen 与 official-unseen 精确保持 Mean8；训练损失为 seen CE 加 `0.1 topology`。

| 条件 | RUN | 划分 | 当前状态 | 预注册门 | U / S / H / ZS |
|---|---|---|---|---|---|
| Mean8 | 同次只读基线 | xlsa17 100/50 pseudo-GZSL | `completed` | 无训练 | `68.808311 / 70.628786 / 69.706665 / 80.279356` |
| 旧强 X2 | RUN-014 | 同一 100/50 pseudo-GZSL | `completed_control` | 公平对照 | `60.276109 / 85.020852 / 70.541409 / 80.279356` |
| HSP-PSE | RUN-015 | 同一 100/50 pseudo-GZSL | `completed_stop_no_gate` | 相对 Mean8 `Delta H>=+3.0`；相对 X2 `Delta H>=-0.3`；`U>=X2_U-0.5` | `63.023394 / 81.972867 / 71.259883 / 80.279356` |
| HSP-PSE final | RUN-016 | 标准 CUB 150 seen 训练、150+50 GZSL 测试 | `not_started_gate_failed` | 只有 RUN-015 通过全部 pseudo 门才启动 | 未创建目录、未读取 official test |

RUN-015 相对 X2 为 `Delta U=+2.747285`、`Delta S=-3.047985`、`Delta H=+0.718475`、`Delta ZS=0`，说明 6+1+1 分层确实缓解了 X2 的 seen 偏置并提高伪 GZSL H；但相对同次 Mean8 只有 `Delta H=+1.553219`，未达到主模块要求的 `+3.0 H`，因此不能把它写成已恢复 73--74 强能力。最终三门为 `0.492303/0.095492/0.089366`，均未触顶。按冻结规则停止，不读取 official test，不启动 HSTB 或 VEC，也不反向调整 gate、topology 或 gamma。

冻结身份：`commit:80daef7f01829e6dad9bff42d38a2655d68e7684`；配置 SHA-256 `efd51a7e8dced2a085c59031f6761ef4977d842e31c33be84158541fd8490ab5`；56 项 HSP/X2/CHORM 相关测试与真实 200x8 cache CPU smoke 通过；两轮顺序只读审核均为 pass、阻断为 0。RUN-014/015 使用相同 commit、配置、输入 SHA、类别顺序和 pseudo split，50 个 pseudo-unseen 类图像不进入梯度或 checkpoint 选择。

证据位于 `warehouse://runs/v5/local_trials/HSP-PSE-20260816/`。RUN-014 的 `training.log / metrics.json / model_final.pth` SHA-256 为 `e43bc1dfc2f2a5c8ecda428c6cca79cfb5c1e6a1c6fe630a2adbfdddcc593206`、`c22bc08c47e089ca4b9242c372964be11304d046d2e5fa936d0c5f1eee9b5768`、`45e41524663d2f09613063ef33029f3d4e3dd2e069d11d9a099a19d01a17ed1a`；RUN-015 对应为 `f1d5fee7a47662de927376b005dca64429918873e530b00b6964ae375a81f225`、`e81258757fba2383cabcc570677282e7581d4d394ecb880874950b52251d7ad8`、`4973d0fa415c93d2380f6f2315af1a7ff8db5fb6993f4fd917087177be343d6d`。

- [x] 冻结 HSP-PSE 公式、三门、100/50 门槛和 RUN-014/015/016 身份。
- [x] 实现 HSP 独立入口；测试、真实 cache smoke 与两轮审核通过。
- [x] 完成 RUN-014 与 RUN-015，回填完整 U/S/H/ZS、门值和证据 SHA。
- [x] RUN-015 未过主模块门；RUN-016 未运行，official test 未触达。
- [ ] HSTB：设计已记录；被 HSP 主模块门阻断，未实现、未运行。
- [ ] VEC：设计已记录；被 HSP 主模块门阻断，未实现、未运行。

#### HSP-PSE V2：修正验证问题后的完整最终结果

V1 的 `Delta H vs Mean8 >= +3.0` 不是公平的主模块筛选门：同一 100/50 划分中的已知强 X2 也只比 Mean8 高 `+0.834744 H`，该绝对门会连强参考本身一起拒绝。V1 的 RUN-014/015 结果和失败判定原样保留，RUN-016 仍未创建。V2 在读取任何 official test 前单独冻结，只修改研究问题为“同一划分、同一训练协议下，HSP 是否直接优于 X2”；模型公式、seed、50 epoch、topology、输入和划分均未改变。

| 条件 | RUN | 划分 | 状态 | 冻结门 | U / S / H / ZS |
|---|---|---|---|---|---|
| 旧强 X2 V2 控制 | RUN-017 | xlsa17 100/50 pseudo-GZSL | `completed_control` | 同次直接对照 | `60.276109 / 85.020852 / 70.541409 / 80.279356` |
| HSP-PSE V2 | RUN-018 | 同一 100/50 pseudo-GZSL | `completed_gate_passed` | `Delta H vs X2 >= +0.3`；`U >= X2_U-0.5` | `63.023394 / 81.972867 / 71.259883 / 80.279356` |
| HSP-PSE V2 final | RUN-019 | 标准 CUB：150 seen 训练；150 seen + 50 unseen 联合 GZSL | `completed_stop_no_official_gain` | `H>=73`；vs Mean8 `Delta H>=+4`；vs X2 `Delta H>=+0.3` | `76.616621 / 66.517359 / 71.210698 / 81.534684` |

RUN-018 相对 RUN-017 为 `Delta U=+2.747285`、`Delta S=-3.047985`、`Delta H=+0.718475`、`Delta ZS=0`，所以 V2 pseudo 门通过。RUN-019 随后用全部 150 个 seen 类重新训练固定 50 epoch，先保存 checkpoint，再读取 official test；official test 不参与模型、epoch、门值或参数选择。其同次 Mean8 为 `66.894132 / 66.392905 / 66.642576 / 81.534684`，HSP 相对 Mean8 为 `Delta U=+9.722489`、`Delta S=+0.124454`、`Delta H=+4.568122`、`Delta ZS=0`，但相对冻结 X2 为 `Delta U=+3.221142`、`Delta S=-7.134217`、`Delta H=-2.312607`、`Delta ZS=0`。因此它证明 6+1+1 强位移能够明显提高 U，却没有保住 S，也没有恢复旧 X2 的 `H=73.523304`；按冻结门停止，不能称为有效主模块。

V2 最终三门为 `local/unique/global=0.476685/0.109793/0.096228`。冻结身份为 `commit:5b80aa76c1ea5f9f012dc34d77d93e396629c4c7`，配置 SHA-256 为 `a8994776650646bd49280f220c5e32cdc3805f21fdf35262e6b6bedb73207c49`；57 项 HSP/X2/CHORM 相关测试通过，两轮顺序只读审核均为 pass、阻断为 0。V2 全部结果仍为本地筛选证据，`formal_evidence=false`，未 push GitHub。

证据位于 `warehouse://runs/v5/local_trials/HSP-PSE-V2-20260816/`。RUN-017 的 `training.log / metrics.json / model_final.pth` SHA-256 为 `1bb23bd3e6b7b320b4949b72c93f88cc8a19bba61e86e39abcf508232c94bc95`、`9d84f451fef34d69d4a2fb14d0d39c336063ecfa3ac978654a66880e3b6c78c5`、`1c7eecea913a86a1cacac595e89836c2a410a253918e6bcbabfee5d5197323fd`；RUN-018 对应为 `47a3bba2c1a8b6c180d591c94c627c43e62ef0ee527a95e6690f90c7964e8ef1`、`6a00c982a418a7190999948cf63e6f76e77e99aa559b7770be8c4365c4f52f1a`、`ef07fcc5cfc425a543ad39622cf97136864a86388b1229acb496e4e6773d94de`；RUN-019 对应为 `403f31657e6c3af1c79377d0041f11b01d5ba87cba9a4f10561b10cec8fa4633`、`12ee94b89a4888ddb31854c88d5ceaa49dea1330d3a9027684abd97b0a71a435`、`25adead2624af8cd37f6478362287f9a9b7c14a5e209d0d44986be85a7eb7100`。

- [x] V2 在 official test 前冻结直接 X2 比较门和全新 RUN-017/018/019 身份。
- [x] V2 代码、配置和证据绑定通过 57 项测试及两轮顺序审核。
- [x] RUN-017/018 未读取 official test；RUN-018 通过修正后的 pseudo 门。
- [x] RUN-019 按标准 150/50 CUB GZSL 完成一次最终评估并如实判定失败。
- [ ] HSTB：继续阻断；HSP-PSE 未达到主模块的 X2 参考线，不在失败主模块上叠加迁移桥。
- [ ] VEC：继续阻断；不为凑模块数量在失败主路上叠加视觉残差。

### 2026-08-17 HSTB / RUN-020：从冻结 X2 独立迁移 unseen 角色位移

owner 随后明确改变了本地筛选路线：HSTB 不再叠加失败的 HSP，而是直接从冻结 X2 独立派生；本轮允许固定一组公式直接测试 official split，不使用 validation，不搜索参数，不使用 gamma。该结果因此只能标记为 `test_exposed=true / formal_evidence=false`，不能作为无 test 泄漏的正式晋级证据。

HSTB 对 X2 的每个 seen 类逐角色做反事实删除，得到六个局部角色和独特角色的球面边际位移；每个 unseen 类、每个角色分别检索 Top-5 seen 邻居，将位移平行运输到 unseen Mean8 切空间，并用邻居方向一致性门决定接受或严格回退。global 角色固定为语义锚点、不迁移；150 个 seen 原型逐位保持 X2。冻结参数为 `top_k=5`、一致性阈值 `0.6`、角色范数与总范数上限均取 seen 分布 90% 分位、绝对总角度上限 `pi/3`、迁移强度 `1.0`。

| 条件 | U | S | H | ZS | 相对 X2 | 状态 |
|---|---:|---:|---:|---:|---|---|
| 冻结 X2 | 73.395479 | 73.651576 | 73.523304 | 81.534684 | 基线 | `completed_control` |
| HSTB / RUN-020 | 74.877411 | 72.941726 | 73.896895 | 82.082748 | `Delta U=+1.481932`、`Delta S=-0.709850`、`Delta H=+0.373591`、`Delta ZS=+0.548065` | `completed_stop_no_gain` |

HSTB 达到预注册的 `H>=73.8`、`Delta H>=+0.3` 和 `Delta U>=+0.5`，ZS 也提高；但 S 下降 `0.709850`，超过最多下降 `0.5` 的硬门。机制门同样未通过：350 个 unseen-角色门全部打开，`closed_gate_count=0`，一致性最小值仍为 `0.643614`，所以固定 `0.6` 阈值没有产生任何“冲突时回退”；模块实质上退化为无拒绝的七角色运输。50 个 unseen 类都发生移动，平均球面角位移 `0.040203`，角色邻居未退化为同一组（完全相同邻居比例 `0`）。因此当前 HSTB 有可见的 U/H/ZS 正增益，但不能作为已成立模块；不基于这次 official 结果修改阈值、Top-K、迁移强度或追加 gamma。

冻结身份：`commit:49c1b7f5b77672094198e2ed1dccf7a3eea452db`；配置 SHA-256 `9d4911c8295abd2aea703347c711b6fc852043a9d028b23a767ce18766c55d40`；X2 checkpoint SHA-256 `a0d8465d3a716ec52d197c8ca10ab9e70dff73d09fe56099e38d8270ee7243f3`。65 项 HSTB/HSP/X2/CHORM 相关测试通过，两轮顺序只读审核均为 pass、阻断为 0。official test 对冻结 X2 和 HSTB 各评一次；没有在单次 RUN 内据 test 选择任何参数。

证据位于 `warehouse://runs/v5/local_trials/HSTB-DIRECT-20260817/RUN-020/`。`training.log / metrics.json / model_final.pth` SHA-256 分别为 `cff5eae54b167837e844cd34c77bb12a4ae58b9163f84881a5d659724b66c76a`、`d8c8f7d7eb25b273c6b1ddbe066c322d3ba8af5e9ca1ead6afa73d9f23ba2d88`、`69b12d1f32aebb30a26b85a60de9409205aae43bd75d8029116646038d001bb1`；冻结 HSTB 原型 SHA-256 为 `28f9a5bf7902dde958c9702f0b53034236ec3ffeef3fcb8d5cf4d6ef13406b3e`。

- [x] 从 X2 独立冻结 HSTB 公式、直接 test-exposed 协议、RUN-020 身份和停止门。
- [x] 实现 HSTB；65 项相关测试和两轮顺序只读审核通过。
- [x] 完成 RUN-020，回填完整 U/S/H/ZS、机制诊断及全部证据 SHA。
- [x] 按冻结 S 门与机制门记为 `stop_no_gain`；不调 threshold、Top-K、strength 或 gamma。
- [ ] VEC：尚未实现、未运行；是否从 X2 独立测试应由下一轮 owner 指令决定，不自动叠加当前 HSTB。

### 2026-08-17 HSTB-V2 + CVEI / RUN-021--023：迁移保护与 Top-2 视觉裁决

owner 随后明确要求 HSTB 优化版与视觉分支一起实现和测试，并继续采用固定单配置直接评 official test 的本地筛选口径。三条条件在读取本轮 official 结果前一起冻结；均不使用 validation、gamma、Adapter 或 test 内搜索，统一标记为 `test_exposed=true / formal_evidence=false`。三条 RUN 串行使用同一冻结 X2、GPT-5.5-derived 八句、标准 CUB 150/50 类划分和同一代码提交，目录互不覆盖。

HSTB-V2 在 RUN-020 的方向一致性门外增加语义突出度与位移范数稳定性门，并在球面切空间删除朝最近 seen 原型的正向分量，再对全部 150 个 seen 原型执行确定性回溯保护。CVEI 不训练投影层，也不重写 200 类排行榜；它只取 X2/HSTB 全局分数的 Top-1 与 Top-2，用六个局部角色在同一批差异 Patch 上做对称复核。只有至少 4/6 角色支持第二名，且视觉中位证据超过全局分差时，才交换 Top-1/Top-2 的原始分数；其余 198 类逐位不变。RUN-023 使用同一 HSTB-V2 原型再叠加同一 CVEI 公式，不重新训练。

| 条件 | U | S | H | ZS | 相对 X2 | 状态 |
|---|---:|---:|---:|---:|---|---|
| 冻结 X2 | 73.395479 | 73.651576 | 73.523304 | 81.534684 | 基线 | `completed_control` |
| HSTB-V2 / RUN-021 | 73.733008 | 73.566920 | 73.649870 | 81.705534 | `Delta U=+0.337529`、`Delta S=-0.084656`、`Delta H=+0.126566`、`Delta ZS=+0.170851` | `completed_stop_no_gain` |
| CVEI / RUN-022 | 73.485404 | 73.375046 | 73.430184 | 81.591272 | `Delta U=+0.089926`、`Delta S=-0.276530`、`Delta H=-0.093121`、`Delta ZS=+0.056589` | `completed_stop_no_gain` |
| HSTB-V2 + CVEI / RUN-023 | 73.584276 | 73.248291 | 73.415899 | 81.725752 | `Delta U=+0.188798`、`Delta S=-0.403285`、`Delta H=-0.107405`、`Delta ZS=+0.191069` | `completed_stop_no_gain` |

RUN-021 将旧 HSTB 的 S 下降从 `-0.709850` 压到 `-0.084656`，说明 seen 竞争保护确实缓和了副作用；但 H 增益也从 `+0.373591` 缩到 `+0.126566`，未过 `+0.30 H` 门。更关键的是，新增双可靠性门仍未形成选择：350 个 unseen-角色门仍全部打开，`closed_gate_count=0`、`evidence_closed_count=0`，50 个 unseen 类全部移动；竞争保护发生 59 次缩短/投影动作，但没有把“证据不足时回退”变成真实机制。因此 HSTB-V2 不保留为成立模块。

RUN-022 的 CVEI 在 official GZSL seen/unseen 上分别交换 27/58 个样本；seen 为 `4 rescue / 10 harm`，unseen 为 `24 rescue / 21 harm`。它对 unseen 略有帮助，却对 seen 制造更多错误，最终 H 下降 `0.093121`。unseen-only ZSL 为 `19 rescue / 17 harm`，只带来很小的 ZS 正增益。RUN-023 中 CVEI 在 HSTB-V2 基座上仍为 seen `4/10`、unseen `18/22`，直接抹掉 HSTB-V2 的小幅 H 增益。结论是 Top-2 对称裁决已避免 VCER 的大幅崩溃，但当前六角色多数投票仍不是有效视觉模块；不基于本轮 test 继续改 `K=16`、`4/6`、`1/8` 或追加 gamma。

冻结身份：`commit:be655d4faf4ed5a22c9783b0a05a3ca251a6efc0`；配置 SHA-256 `c6479c9ede7f4968bb813106e631b3147f8dbe87ce455c8c50994b54e8d217dd`；X2 checkpoint SHA-256 `a0d8465d3a716ec52d197c8ca10ab9e70dff73d09fe56099e38d8270ee7243f3`。76 项相关测试与真实 `200x8` 文本、`1764x576` Patch smoke 通过；两轮顺序只读审核均为 pass、阻断为 0。

证据分别位于：

- `warehouse://runs/v5/local_trials/HSTB-V2-20260817/RUN-021/`：`training.log / metrics.json / model_final.pth` SHA-256 为 `a4e13ff947766d46eac5dfc3ef4121ca64559705fc4ef162b163d4a4acd3af8b`、`c2cd1cf660c1f38d6037ea34e57ea3b9506af4860f0e26f81aae72446cdb6551`、`9ac0e453b79b16de79e0340bae58ecc3eba0895c165f7883a750de443a061112`；原型 SHA-256 为 `126c640b5b08cb34d05997bf5950bca07622ed2fc2d3b64d8c4c4a6a437b191b`。
- `warehouse://runs/v5/local_trials/CVEI-20260817/RUN-022/`：对应 SHA-256 为 `2af40ac75574d114a9bb51b22173a5e4f89ae712fd21141da93b71e5d1c0a51f`、`c6436517d35ec03103dee3e124dbb82b3228853d69251dd2670e5d6c82957133`、`61d88575e4fa083543dcc1e5f652ab08f61e45ca6479a2531d9e3ca66954bd9f`。
- `warehouse://runs/v5/local_trials/HSTB-V2-CVEI-20260817/RUN-023/`：对应 SHA-256 为 `6db3c46a8ab8d1a647637ba284c0ddd8d4a14e2ff2b57ba1ae2f928d0052ed95`、`941dc09a3133f9b07ca6ac821369347ca39511a759f0cbce74e17c6e832b1885`、`6aa780cce87c54747a994aeade6b7097ef8eaf0380f301481c3bf6f6baa104c6`；组合使用的 HSTB-V2 原型 SHA 与 RUN-021 一致。

- [x] HSTB-V2、CVEI 与组合三条公式和 RUN 身份在本轮 official 前一起冻结。
- [x] 实现、76 项测试、真实 cache smoke 和两轮顺序审核通过。
- [x] RUN-021/022/023 串行完成，完整 U/S/H/ZS、机制诊断与证据 SHA 已回填。
- [x] 三条均按冻结门记为 `stop_no_gain`；不调阈值、Top-K、投票数、视觉强度或 gamma。
- [ ] 当前仍只有 X2 是约 `73.52 H` 的强参考，不把 HSTB-V2 或 CVEI 计为已成立原创模块。

### 2026-08-17 REDM + CLPF：角色编辑动力学与视觉证据闭环

第一阶段 `REDM / RUN-024` 已完成并按冻结门停止；第二阶段 `CLPF` 未启动。两者原计划共同解决同一个问题：X2 能把 seen 原型改得很强，但现有 HSTB 只复制邻居位移、350 个门全部打开；已有 CVEI 又把视觉分数独立叠到 logits，造成 harm 多于 rescue。REDM 虽能拟合 seen 类之间的强原型几何，却把 unseen 原型平均移动约 0.819 弧度，导致迁移崩溃，因此不再继续叠加视觉反馈模块。

`REDM` 固定冻结 X2 与 CLIP，只训练一个约 9.9 万参数的低秩奇对称角色编辑函数。输入为六个局部角色和 unique 的类间文本差，global 只保留为 Mean8 锚点；训练目标是重建 seen 类之间 X2 强原型相对 Mean8 几何的残差，推理时从 Top-5 seen 锚点预测 50 个 unseen 原型，150 个 seen 原型必须逐位保持 X2。固定 rank=64、Top-20 训练邻居、Top-5 推理锚点、50 epoch、seed=5、无 validation、无 gamma；本轮 official test 只用于候选决定，因此统一标记 `test_exposed=true / formal_evidence=false`。

| 条件 | RUN | 唯一变化 | 当前状态 | U / S / H / ZS | 保留门 |
|---|---|---|---|---|---|
| 冻结 X2 | 已有 RUN-005 | 强 Uniform-PSE + topology=0.1 | `completed_control` | `73.395479 / 73.651576 / 73.523304 / 81.534684` | 基线 |
| X2 + REDM | RUN-024 | 只替换 unseen 原型为角色编辑动力学预测；seen 保持 X2 | `completed_stop_no_gain` | `52.012736 / 86.600608 / 64.991355 / 72.163808` | 未通过：`Delta U=-21.382743`、`Delta S=+12.949032`、`Delta H=-8.531949`、`Delta ZS=-9.370875` |
| X2 + REDM + CLPF | RUN-025（暂定） | 用冻结 patch 的角色预测误差反馈控制 X2/REDM 位移，不直接加独立视觉 logits | `not_started_cancelled_by_redm_gate` | `not_run` | RUN-024 未过门，按预注册规则不启动 |

RUN-024 代码在独立分支 `codex/redm-local-20260817`，输出固定为 `warehouse://runs/v5/local_trials/REDM-DIRECT-20260817/RUN-024/`，目录必须不存在。若 RUN-024 不过门，立即停止 REDM，不扫 rank、邻居数、学习率或 gamma，也不启动 CLPF；若通过，只允许下一步实现一次 CLPF 最小闭环。

RUN-024 冻结身份与证据：`commit:f776c831af64ff0f1807af1c85b4d9f2e0420dec`，config SHA-256=`615ec0ee7773ddba82703587dbce1149483be0338c0586b3bcc098a1d663a1fb`。机制诊断通过：seen 训练对端点误差从 `0.487526` 降至 `0.096943`（下降 `80.12%`），奇对称误差为 `0`，最大角色范数占比为 `0.147499`；但 unseen 原型移动角度均值为 `0.818927` 弧度，造成 U、H、ZS 大幅下降，说明失败点是跨类迁移而非训练拟合。产物 SHA-256：`training.log=aceee086804db02eec3ff54cc8491aa383191b78a6f6296778ca3635f94e61ac`、`metrics.json=d26271204210eda10d68014fd87aed97c11cfd5685cd835a772a3d091a3f95df`、`model_final.pth=11de20f5a3f5008aa650962a8cb8640913f1a3d624c5d8812f9929d0da0982b2`。本次为 `test_exposed` 本地筛选，不作为正式 confirmation evidence。

### 2026-08-17 CRPC / RUN-025：交叉留出角色-Patch证书

REDM 失败后回到冻结 X2，不再移动任何类别原型。X2 先提出 Top-1、Top-2 和两者文本差异最大的一个局部角色；24x24 Patch 在每个 2x2 块中拆为互不重用的 A/B 棋盘，一半只负责选共同可见区域，另一半只负责验证第二名相对第一名的角色证据，再交换职责复核。只有两次复核都支持第二名，且用 150 seen / 7057 张训练图像学到的两参数单调置信度达到 `0.8`，才交换 X2 前两名的原始 cosine 值；否则逐位保持 X2，其他 198 类永远不变。

| 条件 | RUN | 训练与测试 | 当前状态 | U / S / H / ZS | 保留门 |
|---|---|---|---|---|---|
| 冻结 X2 | 已有 RUN-005 | 150 seen 训练；标准 200 类联合 GZSL | `completed_control` | `73.395479 / 73.651576 / 73.523304 / 81.534684` | 基线 |
| X2 + CRPC | RUN-025 | 只训练两个校准标量，50 epoch；无 validation、无 gamma；checkpoint 后 official 一次 | `completed_stop_no_gain` | `73.395479 / 73.651576 / 73.523304 / 81.534684` | 未通过：与 X2 完全相同，训练与 official 均 `action_count=0` |

冻结身份：分支 `codex/x2-role-patch-predictor-local-20260817`，`commit:9f5121332c3cc73bcda98fdb08cb1f81cbe08b12`，config SHA-256=`074563e989f34aa650b7d197ba55d131af3ffd0e0cc8d912cb2355c003610bac`；输出固定为 `warehouse://runs/v5/local_trials/CRPC-DIRECT-20260817/RUN-025/`。9 项 CRPC 测试、60 项相关回归和真实 cache smoke 已通过，两轮顺序只读审核均为 pass、阻断为0。训练中正常证书1716个、角色打乱证书1463个，但固定置信度阈值下两者都没有动作；official seen/unseen/ZS 同样均为0次交换，因此所有指标逐位复现 X2。结论是交叉留出证书有效地避免了 harm，却保守到完全没有修正能力；不根据这次 test 降低0.8阈值、修改棋盘或追加gamma。产物 SHA-256：`training.log=56ffb7af4f9823ac6324bf36fbc8b501b65a195cdd2ac339d26eac188bc488ac`、`metrics.json=f47d8f44cd6b434555e632ea36fd52dc204ab9575cc69bf0bd46e57658daf5da`、`model_final.pth=e048d473a5c9e61f9b06eda48a42d8d1d6194340880baf1d5c542e6175e1b3d8`。该运行仍是 `test_exposed=true / formal_evidence=false` 的本地候选筛选。
