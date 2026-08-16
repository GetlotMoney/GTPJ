# 本地强 PSE 与旧算子等价诊断

本目录在独立本地分支复用既有八句训练入口，只用于筛选 DCRA-PSE；它不是 `V5-INNOVATION-013` 的结果改写，也不直接形成 promotion/confirmation 证据。

固定框架：冻结 CLIP CLS、GPT-5.5-derived 八角色文本、global-only、seen CE、无 ICSA、无局部、无 gamma。PSE-A/B/C 按 seen 训练集内部固定 10% validation CE 选择 checkpoint；后续 X1/X2 诊断在看 test 前固定为全量 7057 seen、旧随机采样和 epoch 50。两种协议都只在 checkpoint 固定并保存后读取 official test，一次同时计算 Mean8 和目标条件。

三个条件在同一个 `config.yaml` 中一次冻结：

- `PSE-A / RUN-001`：旧强 Uniform Value/Output/Projection/LayerNorm/inner-outer residual，`topology=0.1`。
- `PSE-B / RUN-002`：相对 PSE-A 只把 `topology=0`。
- `PSE-C / RUN-003`：相对 PSE-A 只把 Uniform 聚合换为 DCRA；同角色视觉判别 margin 经类内标准化后使用 `0.8 × uniform + 0.2 × softmax`，每个角色权重结构上位于 `[0.10, 0.30]`。

DCRA 的 seen 视觉类中心只由训练 indices 计算，validation 和 official test 均不参与。第一轮为与旧 PSE 公平比较，seen 类使用增强原型，unseen 类逐值保持 Mean8。三个条件均使用同一八句 cache、seed、训练划分、50 epoch 分段 Adam 日程和评估口径。

本地筛选判定：先记录 PSE-A/B 的真实 topology 差值；PSE-C 必须不低于 PSE-A、相对同次 Mean8 至少约 `+4 H`，且 U/ZS 不出现明显塌陷，才进入机制控制与正式化。

在 PSE-A/B/C 完成后，新增两个预先冻结的缺口诊断：

- `PSE-X1 / RUN-004`：保留当前简化 Uniform-PSE，改为全量 seen、旧式每 step 随机抽样、固定 epoch 50。
- `PSE-X2 / RUN-005`：与 X1 完全相同，只把 PSE 训练算子换成旧生产级 Uniform-MHA：保留完整 Q/K/V 参数初始化、V/out projection、attention-weight dropout、逐句 projection/dropout、inner residual、LayerNorm 和 outer residual；仅 seen 进入 PSE，unseen 仍保持与 X1 相同的 Mean8，避免额外混入文本聚合差异。

因此 `X1-PSE-A` 只用于诊断训练数据/采样制度，`X2-X1` 只用于诊断旧 Uniform-MHA 训练算子。两组固定 `topology=0.1`，official test 不参与选择。
