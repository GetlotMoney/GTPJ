# 配置策略

`config/versions/v5.yaml` 是当前 owner-activated active mainline 配置。`config/versions/v4.yaml` 仍是更强的 confirmed reference 配置，`confirmed_H=74.47`，3 次复现均值 `H_mean=74.45`。

规则：

- `config/versions/vX.yaml` 保存版本 `vX` 可复用的固定配置。
- `experiments/vX/config.yaml` 是该版本的归档副本。
- tune、ablation 或 confirmation 运行必须先把版本配置复制到自己的实验目录。
- 不要为了跑一次临时实验而直接修改版本配置。
- `config/GTPJ_cub_gzsl.yaml` 是当前 CUB 运行别名，只在 owner 明确激活版本时切换。

当前别名：

```text
config/GTPJ_cub_gzsl.yaml -> identical to config/versions/v5.yaml
```

当前 v5 主线关键参数：

```text
bvsa_text_mode: conditional
sgmp_text_mode: conditional
jepa_text_mode: conditional
pse_outer_ratio: 0.65
clip_a_self_outer_ratio: 0.65
local_weight: 0.2
```
