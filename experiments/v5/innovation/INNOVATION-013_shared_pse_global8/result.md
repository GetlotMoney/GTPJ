# V5-INNOVATION-013 结果

状态：`completed`；证据等级为 `valid_single_run`，决定为 `keep`。

| Run | U | S | H | ZS | Best epoch | ΔH vs 纯 CLIP | 决定 |
|---|---:|---:|---:|---:|---:|---:|---|
| `RUN-002` | 63.233232 | 74.993896 | 68.613253 | 79.671144 | 100 | +4.449214 | `keep` |

- 正式提交：`15c445694dd217d0e2792dcc304ad69e26199c73`
- 配置 SHA-256：`e38bd1f760b0106b617cc5fad7d1dbca040460dc8bb4966f639da327958e3413`
- 纯 CLIP 全局八句基线：`H=64.16403868322334`
- 训练日志 SHA-256：`78acbb6d1bd2641d387a323861b90dc5064e30fb970e92d4ccb0f86d9f861d65`
- metrics.json SHA-256：`0fcf8ded7a097ee10a8c7b0568f1a1e28662837834f919f3ab03d02ce0d5ffe6`
- 证据清单 SHA-256：`0df9fe4e8e4f5a30a5fb4a7bd1902a2f13f322573a7c25ac863c1144809862dd`
- Warehouse：`warehouse://runs/v5/innovation/V5-INNOVATION-013/RUN-002`

PSE 单模块真实提升 4.449214 个 H 百分点，主要把 S 提高到 74.99；U 仍为 63.23，是下一模块的明确瓶颈。最佳验证点位于第 100 轮上限，因此不能声称已经收敛、最优、确认或晋级。
