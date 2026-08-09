# V5-INNOVATION-009 结果

状态：`RUN-001` 因评估设备错误失败，尚无可用于方法判断的完整指标。

## RUN-001 失败记录

- 代码提交：`2aed5d6922887e591698ea4151fd51bca63ea307`
- 已完成：真实缓存加载与第 1 个 epoch 的全部训练步。
- 失败位置：首次评估的 ZS 类别索引。
- 原因：评估 logits 已在 CPU，但 `unseenclasses` 仍在 CUDA，PyTorch 拒绝跨设备索引。
- 指标：未完成首次完整 U/S/H/ZS 评估，因此不记录结果数值。
- 证据：`/data/lby/projects/cv_project/GTPJ_Warehouse/runs/v5/innovation/V5-INNOVATION-009/RUN-001/training.log`
- 处理：保留失败记录；修复设备统一后使用新的运行目录重跑，不覆盖本目录。
