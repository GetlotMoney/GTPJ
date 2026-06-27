# GTPJ 下一步动作

这是当前执行窗口。这里只放近期要做的少数动作，不放所有想法。

## P0

- [ ] 跑 `CONFIRM-001_v2_seed5`，确认 `GTPJ-v2 / H=74.29` 是否可在 clean confirmation 中复现。

## P1

- [ ] 做 `GTPJ-v2` 的 U/S gap analysis，解释 `S - U = 6.20` 的来源。
- [ ] 规划 v2 的下一轮 tune 或 ablation，优先围绕 `clip_a_self_outer_ratio`、switch-off path 和 confirmation 稳定性。

## 已完成

- [x] 初始化干净的 GTPJ 仓库。
- [x] 创建可执行 workflow 入口和 CLI helper。
- [x] 确定 `GTPJ-v1` 第一版正式 baseline，CUB seed=5 H=73.93。
- [x] 清空来源不明的旧创意树和待做实验队列。
- [x] 登记并完成 `IDEA-0001 / TRIAL-001`。
- [x] 将 `TRIAL-001 / ATTEMPT-019` 提升为 `GTPJ-v2` 当前主线，CUB seed=5 H=74.29。
