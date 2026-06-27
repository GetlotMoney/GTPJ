# 配置策略

`config/versions/v2.yaml` 是当前 active baseline `GTPJ-v2` 的固定配置。
`config/versions/v1.yaml` 保留为 `GTPJ-v1` 的历史固定配置。

规则：

- `config/versions/vX.yaml` 保存版本 `vX` 可复用的 baseline 配置。
- `experiments/vX/config.yaml` 是该版本的归档副本。
- tune、ablation 或 confirmation 运行必须先把版本配置复制到自己的实验目录。
- 不要为了跑一次临时实验而直接修改版本配置。
- 版本配置只包含当前 baseline 启用的字段。未启用的候选模块在 `idea_tree/` 中跟踪，
  只有选中 `IDEA-xxxx` 节点后，才能加入 trial-local 配置。
- 旧的空转 key 和只影响 runtime 的开关不保留在版本配置中。

当前别名：

```text
config/GTPJ_cub_gzsl.yaml -> 与 config/versions/v2.yaml 内容相同
```
