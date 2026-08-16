# 证据边界

完整 crop cache、日志和 state 保存在
`warehouse://runs/v5/local_trials/ARTV-20260817/RUN-001`，仓库只登记轻量指标与摘要。

- `evaluation.log` SHA-256：`b2d2f898d0a19536884eea61a3066fec826980057fa00475f21f399fbfd33e4c`
- `metrics.json` SHA-256：`590a4a7a064c27472519e67e30570eafc5c6c26cb5d04584da8784ada3f1145f`
- `artv_state.pth` SHA-256：`bf1b6ad31d11e600b854fa9969ed1b6b8531fe92a0ff19b76ed65259824e87f7`
- seen/unseen crop SHA-256：`2c0c9cfdcc864b01017cfbf98b2be12406bfe690a5b6e984072700c19b5be932` / `a63a92d36287d56c5865dc5d4d59c53940adde7184bc89c3e02b2ef94c22e342`
- 启动器未保存数值退出码；`metrics.json` 为 completed 且日志无 traceback，参数矩阵不补造退出码。
