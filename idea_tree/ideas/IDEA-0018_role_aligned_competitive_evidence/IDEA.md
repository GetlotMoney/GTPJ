# IDEA-0018：角色对齐竞争证据（RACE）

- 状态：`rejected / stop_no_gain`
- 来源：owner 2026-08-16 确认；研究候选 `CAND-001`。
- 问题：seen 训练的 prototype 位移提高 S 却损伤 U，而 attention 权重不能作为忠实解释。
- 假设：不移动 prototype，直接加入图像条件的同角色目标减 rival 证据，可以避免 seen 专属漂移。
- 最小实验：`V5-INNOVATION-020/RUN-001`，同次 Mean8、aligned、no-contrast、wrong-role；100/50 验证选一个强度，official test 一次。
- 失败门：`delta_H < 0.50` 或 U/S 任一下降超过 0.50 即停止，不换 seed 或扩网格追数。
- 结果：RUN-001 选择 `lambda=0.1`，official `H=66.541096`，相对同次 Mean8 `delta_H=-0.101480`；wrong-role 与 aligned 近似，故角色竞争假设被当前公式否定。
