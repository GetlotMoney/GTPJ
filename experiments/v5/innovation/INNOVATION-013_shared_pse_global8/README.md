# 本地 PSE-A/B/C 强原型对照

本目录在独立本地分支复用既有八句训练入口，只用于筛选 DCRA-PSE；它不是 `V5-INNOVATION-013` 的结果改写，也不直接形成 promotion/confirmation 证据。

固定框架：冻结 CLIP CLS、GPT-5.5-derived 八角色文本、global-only、seen CE、无 ICSA、无局部、无 gamma。checkpoint 只按 seen 训练集内部固定 10% validation CE 选择，选择并保存完成后才读取 official test，一次同时计算 Mean8 和目标条件。

三个条件在同一个 `config.yaml` 中一次冻结：

- `PSE-A / RUN-001`：旧强 Uniform Value/Output/Projection/LayerNorm/inner-outer residual，`topology=0.1`。
- `PSE-B / RUN-002`：相对 PSE-A 只把 `topology=0`。
- `PSE-C / RUN-003`：相对 PSE-A 只把 Uniform 聚合换为 DCRA；同角色视觉判别 margin 经类内标准化后使用 `0.8 × uniform + 0.2 × softmax`，每个角色权重结构上位于 `[0.10, 0.30]`。

DCRA 的 seen 视觉类中心只由训练 indices 计算，validation 和 official test 均不参与。第一轮为与旧 PSE 公平比较，seen 类使用增强原型，unseen 类逐值保持 Mean8。三个条件均使用同一八句 cache、seed、训练划分、50 epoch 分段 Adam 日程和评估口径。

本地筛选判定：先记录 PSE-A/B 的真实 topology 差值；PSE-C 必须不低于 PSE-A、相对同次 Mean8 至少约 `+4 H`，且 U/ZS 不出现明显塌陷，才进入机制控制与正式化。
